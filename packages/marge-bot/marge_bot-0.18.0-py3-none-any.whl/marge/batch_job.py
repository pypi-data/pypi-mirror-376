import logging as log
import time
from typing import Optional

from . import branch, git, gitlab, job
from . import project as mb_project
from . import user as mb_user
from .commit import Commit
from .merge_request import MergeRequest
from .pipeline import Pipeline


class CannotBatch(Exception):
    pass


class BatchMergeJob(job.MergeJob):
    def __init__(
        self,
        *,
        api: gitlab.Api,
        user: mb_user.User,
        project: mb_project.Project,
        repo: git.Repo,
        options: job.MergeJobOptions,
        merge_requests: list[MergeRequest],
        batch_branch_name: str,
    ):
        super().__init__(
            api=api, user=user, project=project, repo=repo, options=options
        )
        self.batch_branch_name = batch_branch_name
        self._merge_requests = merge_requests

    def remove_batch_branch(self) -> None:
        log.info("Removing local batch branch")
        try:
            self._repo.remove_branch(self.batch_branch_name)
        except git.GitError:
            pass

    def close_batch_mr(self) -> None:
        log.info("Closing batch MRs")
        params = {
            "author_id": self._user.id,
            "labels": self.batch_branch_name,
            "state": "opened",
            "order_by": "created_at",
            "sort": "desc",
        }
        batch_mrs = MergeRequest.search(
            api=self._api, project_id=self._project.id, params=params
        )
        for batch_mr in batch_mrs:
            log.info("Closing batch MR !%s", batch_mr.iid)
            batch_mr.close()
            for batch_pipeline in Pipeline.pipelines_by_merge_request(
                self._project.id, batch_mr.iid, self._api
            ):
                if batch_pipeline.status in ("pending", "running"):
                    log.info("Cancelling obsolete batch pipeline %s", batch_pipeline.id)
                    batch_pipeline.cancel()

    def create_batch_mr(self, target_branch: str) -> MergeRequest:
        self.push_batch()
        log.info("Creating batch MR")
        params = {
            "source_branch": self.batch_branch_name,
            "target_branch": target_branch,
            "title": "Marge Bot Batch MR - DO NOT TOUCH",
            "labels": self.batch_branch_name,
        }
        batch_mr = MergeRequest.create(
            api=self._api, project_id=self._project.id, params=params
        )
        log.info("Batch MR !%s created", batch_mr.iid)
        return batch_mr

    def get_mrs_with_common_target_branch(
        self, target_branch: str
    ) -> list[MergeRequest]:
        log.info("Filtering MRs with target branch %s", target_branch)
        return [
            merge_request
            for merge_request in self._merge_requests
            if merge_request.target_branch == target_branch
        ]

    def ensure_mergeable_mr(
        self, merge_request: MergeRequest, skip_ci: bool = False
    ) -> None:
        super().ensure_mergeable_mr(merge_request)

        if self._project.only_allow_merge_if_pipeline_succeeds and not skip_ci:
            ci_status, pipeline_msg, _ = self.get_mr_ci_status(merge_request)
            if ci_status != "success":
                raise CannotBatch(f"This MR has not passed CI. {pipeline_msg}")

    def get_mergeable_mrs(
        self, merge_requests: list[MergeRequest]
    ) -> list[MergeRequest]:
        log.info("Filtering mergeable MRs")
        mergeable_mrs = []
        for merge_request in merge_requests:
            try:
                self.ensure_mergeable_mr(merge_request)
            except (CannotBatch, job.SkipMerge) as ex:
                log.warning('Skipping unbatchable MR: "%s"', ex)
            except job.CannotMerge as ex:
                log.warning('Skipping unmergeable MR: "%s"', ex)
                self.unassign_from_mr(merge_request)
                merge_request.comment(f"I couldn't merge this branch: {ex}")
            else:
                mergeable_mrs.append(merge_request)
        return mergeable_mrs

    def push_batch(self) -> None:
        log.info("Pushing batch branch")
        self._repo.push(self.batch_branch_name, force=True)

    def ensure_mr_not_changed(self, merge_request: MergeRequest) -> None:
        log.info("Ensuring MR !%s did not change", merge_request.iid)
        changed_mr = MergeRequest.fetch_by_iid(
            merge_request.project_id, merge_request.iid, self._api
        )
        error_message = "The {} changed whilst merging!"
        for attr in (
            "source_branch",
            "source_project_id",
            "target_branch",
            "target_project_id",
            "sha",
        ):
            if getattr(changed_mr, attr) != getattr(merge_request, attr):
                raise job.CannotMerge(error_message.format(attr.replace("_", " ")))

    def merge_batch(
        self, target_branch: str, source_branch: str, no_ff: bool = False
    ) -> str:
        if no_ff:
            return self._repo.merge(target_branch, source_branch, "--no-ff")

        return self._repo.fast_forward(target_branch, source_branch)

    def update_merge_request(
        self, merge_request: MergeRequest, source_repo_url: Optional[str] = None
    ) -> str:
        log.info("Fusing MR !%s", merge_request.iid)
        approvals = merge_request.fetch_approvals(self.approvals_factory)

        _, _, actual_sha = self.update_from_target_branch_and_push(
            merge_request,
            source_repo_url=source_repo_url,
            skip_ci=self._options.skip_ci_batches,
        )

        sha_now = Commit.last_on_branch(
            merge_request.source_project_id, merge_request.source_branch, self._api
        ).id
        log.info(
            "update_merge_request: sha_now (%s), actual_sha (%s)", sha_now, actual_sha
        )
        # Make sure no-one managed to race and push to the branch in the
        # meantime, because we're about to impersonate the approvers, and
        # we don't want to approve unreviewed commits
        if sha_now != actual_sha:
            raise job.CannotMerge(
                "Someone pushed to branch while we were trying to merge"
            )

        # As we're not using the API to merge the individual MR, we don't strictly need to reapprove it.
        # However, it's a little weird to look at the merged MR to find it has no approvals,
        # so let's do it anyway.
        self.maybe_reapprove(merge_request, approvals)
        return sha_now

    def accept_mr(
        self,
        merge_request: MergeRequest,
        expected_remote_target_branch_sha: str,
        source_repo_url: Optional[str] = None,
    ) -> str:
        log.info("Accept MR !%s", merge_request.iid)

        # Make sure latest commit in remote <target_branch> is the one we tested against
        new_target_sha = Commit.last_on_branch(
            self._project.id, merge_request.target_branch, self._api
        ).id
        if new_target_sha != expected_remote_target_branch_sha:
            raise CannotBatch("Someone was naughty and by-passed marge")

        # Rebase and apply the trailers
        self.update_merge_request(merge_request, source_repo_url=source_repo_url)

        # This switches git to <target_branch>
        final_sha = self.merge_batch(
            merge_request.target_branch,
            merge_request.source_branch,
            self._options.use_no_ff_batches,
        )
        # Don't force push in case the remote has changed.
        self._repo.push(merge_request.target_branch, force=False)

        time.sleep(2)

        # At this point Gitlab should have recognised the MR as being accepted.
        log.info("Successfully merged MR !%s", merge_request.iid)

        pipelines = Pipeline.pipelines_by_branch(
            api=self._api,
            project_id=merge_request.source_project_id,
            branch=merge_request.source_branch,
            status="running",
        )
        for pipeline in pipelines:
            pipeline.cancel()

        if merge_request.force_remove_source_branch:
            branch.Branch.delete_by_name(
                project_id=merge_request.source_project_id,
                branch=merge_request.source_branch,
                api=self._api,
            )

        return final_sha

    def execute(self, exc_comment: Optional[str] = None) -> None:
        # pylint: disable=too-many-branches,too-many-statements
        # Cleanup previous batch work
        self.remove_batch_branch()
        self.close_batch_mr()

        target_branch = self._merge_requests[0].target_branch
        merge_requests = self.get_mrs_with_common_target_branch(target_branch)
        merge_requests = self.get_mergeable_mrs(merge_requests)

        if len(merge_requests) <= 1:
            # Either no merge requests are ready to be merged, or there's only one for this target branch.
            # Let's raise an error to do a basic job for these cases.
            raise CannotBatch("not enough ready merge requests")

        self._repo.fetch("origin")

        # Save the sha of remote <target_branch> so we can use it to make sure
        # the remote wasn't changed while we're testing against it
        remote_target_branch_sha = self._repo.get_commit_hash(f"origin/{target_branch}")

        self._repo.checkout_branch(target_branch, f"origin/{target_branch}")
        self._repo.checkout_branch(self.batch_branch_name, f"origin/{target_branch}")

        batch_mr = self.create_batch_mr(target_branch=target_branch)
        batch_mr_sha = batch_mr.sha

        working_merge_requests = []

        for merge_request in merge_requests:
            try:
                _, source_repo_url, merge_request_remote = self.fetch_source_project(
                    merge_request
                )
                self._repo.checkout_branch(
                    merge_request.source_branch,
                    f"{merge_request_remote}/{merge_request.source_branch}",
                )

                if self._options.use_merge_commit_batches:
                    # Rebase and apply the trailers before running the batch MR
                    actual_sha = self.update_merge_request(
                        merge_request, source_repo_url=source_repo_url
                    )
                    # Update <batch> branch with MR changes
                    batch_mr_sha = self._repo.merge(
                        self.batch_branch_name,
                        merge_request.source_branch,
                        "-m",
                        f"Batch merge !{merge_request.iid} into"
                        + f"{merge_request.target_branch} (!{batch_mr.iid})",
                        local=True,
                    )
                else:
                    # Update <source_branch> on latest <batch> branch so it contains previous MRs
                    self.fuse(
                        merge_request.source_branch,
                        self.batch_branch_name,
                        source_repo_url=source_repo_url,
                        local=True,
                    )
                    # Update <batch> branch with MR changes
                    batch_mr_sha = self._repo.fast_forward(
                        self.batch_branch_name, merge_request.source_branch, local=True
                    )

                # We don't need <source_branch> anymore. Remove it now in case another
                # merge request is using the same branch name in a different project.
                self._repo.remove_branch(merge_request.source_branch)
            except (git.GitError, job.CannotMerge):
                log.warning(
                    "Skipping MR !%s, got conflicts while rebasing", merge_request.iid
                )
                continue
            else:
                if self._options.use_merge_commit_batches:
                    # update merge_request with the current sha, we will compare it with
                    # the actual sha later to make sure no one pushed this MR meanwhile
                    merge_request.update_sha(actual_sha)

                working_merge_requests.append(merge_request)

        if len(working_merge_requests) <= 1:
            raise CannotBatch("not enough ready merge requests")

        # This switches git to <batch> branch
        self.push_batch()
        for merge_request in working_merge_requests:
            merge_request.comment(
                f"I will attempt to batch this MR (!{batch_mr.iid})..."
            )

        # wait for the CI of the batch MR
        if self._project.only_allow_merge_if_pipeline_succeeds:
            try:
                self.wait_for_ci_to_pass(batch_mr, commit_sha=batch_mr_sha)
            except job.CannotMerge as err:
                for merge_request in working_merge_requests:
                    merge_request.comment(
                        f"Batch MR !{batch_mr.iid} failed: {err.reason} I will retry later..."
                    )
                raise CannotBatch(err.reason) from err

        # check each sub MR, and accept each sub MR if using the normal batch
        for merge_request in working_merge_requests:
            try:
                # FIXME: this should probably be part of the merge request
                _, source_repo_url, merge_request_remote = self.fetch_source_project(
                    merge_request
                )
                self.ensure_mr_not_changed(merge_request)
                # we know the batch MR's CI passed, so we skip CI for sub MRs this time
                self.ensure_mergeable_mr(merge_request, skip_ci=True)

                if not self._options.use_merge_commit_batches:
                    # accept each MRs
                    remote_target_branch_sha = self.accept_mr(
                        merge_request,
                        remote_target_branch_sha,
                        source_repo_url=source_repo_url,
                    )
            except CannotBatch as err:
                merge_request.comment(
                    f"I couldn't merge this branch: {str(err)} I will retry later..."
                )
                raise
            except job.SkipMerge:
                # Raise here to avoid being caught below - we don't want to be unassigned.
                raise
            except job.CannotMerge as err:
                self.unassign_from_mr(merge_request)
                merge_request.comment(f"I couldn't merge this branch: {err.reason}")
                raise

        # Accept the batch MR
        if self._options.use_merge_commit_batches:
            # Approve the batch MR using the last sub MR's approvers
            if not batch_mr.fetch_approvals(self.approvals_factory).sufficient:
                approvals = working_merge_requests[-1].fetch_approvals(
                    self.approvals_factory
                )
                try:
                    approvals.approve(batch_mr)
                except (gitlab.Forbidden, gitlab.Unauthorized):
                    log.exception("Failed to approve MR:")

            try:
                ret = batch_mr.accept(
                    remove_branch=batch_mr.force_remove_source_branch,
                    sha=batch_mr_sha,
                    merge_when_pipeline_succeeds=bool(
                        self._project.only_allow_merge_if_pipeline_succeeds
                    ),
                )
                log.debug("batch_mr.accept result: %s", ret)
            except gitlab.ApiError as err:
                log.exception("Gitlab API Error:")
                raise job.CannotMerge(f"Gitlab API Error: {err}") from err
