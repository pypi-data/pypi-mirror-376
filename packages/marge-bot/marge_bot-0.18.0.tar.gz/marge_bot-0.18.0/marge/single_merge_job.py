# pylint: disable=too-many-locals,too-many-branches,too-many-statements
import datetime
import logging as log
import subprocess
import time
from typing import Optional

from . import approvals as mb_approvals
from . import git, gitlab
from . import job as mb_job
from . import merge_request as mb_merge_request
from . import project as mb_project
from . import user as mb_user
from .commit import Commit


class SingleMergeJob(mb_job.MergeJob):
    def __init__(
        self,
        *,
        api: gitlab.Api,
        user: mb_user.User,
        project: mb_project.Project,
        repo: git.Repo,
        options: mb_job.MergeJobOptions,
        merge_request: mb_merge_request.MergeRequest,
    ):
        super().__init__(
            api=api, user=user, project=project, repo=repo, options=options
        )
        self._merge_request = merge_request
        self._options = options

    def execute(self, exc_comment: Optional[str] = None) -> None:
        merge_request = self._merge_request

        log.info("Processing !%s - %r", merge_request.iid, merge_request.title)

        try:
            approvals = merge_request.fetch_approvals(self.approvals_factory)
            self.update_merge_request_and_accept(approvals)
            log.info("Successfully merged !%s.", merge_request.info["iid"])
        except mb_job.SkipMerge as err:
            log.warning("Skipping MR !%s: %s", merge_request.info["iid"], err.reason)
        except mb_job.CannotMerge as err:
            message = f"This branch couldn't be merged: {err.reason}"
            log.warning(message)
            self.unassign_from_mr(merge_request)
            merge_request.comment(message)
        except subprocess.TimeoutExpired as err:
            log.exception("TimeoutExpired", exc_info=err)
            comment = f"A git command timed out after {err.timeout} seconds"
            if exc_comment:
                comment += " " + exc_comment
            merge_request.comment(comment)
            self.unassign_from_mr(merge_request)
        except git.GitError as err:
            log.exception("Unexpected Git error", exc_info=err)
            comment = "Something seems broken on bot's local git repo. Check bot logs for more details."
            if exc_comment:
                comment += " " + exc_comment
            merge_request.comment(comment)
            raise
        except Exception as err:
            log.exception("Unexpected Exception", exc_info=err)
            comment = "Unexpected exception in bot while handling this MR."
            if exc_comment:
                comment += " " + exc_comment
            merge_request.comment(comment)
            self.unassign_from_mr(merge_request)
            raise

    def update_merge_request_and_accept(
        self, approvals: mb_approvals.Approvals
    ) -> None:
        api = self._api
        merge_request = self._merge_request
        updated_into_up_to_date_target_branch = False

        while not updated_into_up_to_date_target_branch:
            self.ensure_mergeable_mr(merge_request)
            source_project, source_repo_url, _ = self.fetch_source_project(
                merge_request
            )
            target_project = self.get_target_project(merge_request)
            try:
                # NB. this will be a no-op if there is nothing to update/rewrite

                (target_sha, _updated_sha, actual_sha) = (
                    self.update_from_target_branch_and_push(
                        merge_request, source_repo_url=source_repo_url
                    )
                )
            except mb_job.GitLabRebaseResultMismatch as err:
                log.info("Gitlab rebase didn't give expected result: %s", err.reason)
                merge_request.comment(
                    "A merge request may have skipped the queue, trying again..."
                )
                continue

            if _updated_sha == actual_sha and self._options.guarantee_final_pipeline:
                log.info("No commits on target branch to fuse, triggering pipeline...")
                pipeline_info = merge_request.trigger_pipeline()
                log.info(
                    "Pipeline %s is triggered, waiting for it to finish...",
                    pipeline_info.get("id"),
                )
                self.wait_for_ci_to_pass(merge_request, actual_sha)

            log.info(
                "Commit id to merge %r into: %r (updated sha: %r)",
                actual_sha,
                target_sha,
                _updated_sha,
            )
            time.sleep(5)

            sha_now = Commit.last_on_branch(
                source_project.id, merge_request.source_branch, api
            ).id
            # Make sure no-one managed to race and push to the branch in the
            # meantime, because we're about to impersonate the approvers, and
            # we don't want to approve unreviewed commits
            if sha_now != actual_sha:
                raise mb_job.CannotMerge(
                    "Someone pushed to branch while we were trying to merge"
                )

            self.maybe_reapprove(merge_request, approvals)

            if target_project.only_allow_merge_if_pipeline_succeeds:
                self.wait_for_ci_to_pass(merge_request, actual_sha)
                time.sleep(2)

            try:
                self.wait_for_merge_status_to_resolve(merge_request)
            except mb_job.NeedsRebase:
                continue

            self.ensure_mergeable_mr(merge_request)

            try:
                ret = merge_request.accept(
                    remove_branch=merge_request.force_remove_source_branch,
                    sha=actual_sha,
                    merge_when_pipeline_succeeds=bool(
                        target_project.only_allow_merge_if_pipeline_succeeds
                    ),
                )
                log.debug("merge_request.accept result: %s", ret)
            except gitlab.Unprocessable as err:
                new_target_sha = Commit.last_on_branch(
                    self._project.id, merge_request.target_branch, api
                ).id
                # target_branch has moved under us since we updated, just try again
                if new_target_sha != target_sha:
                    log.info("Someone was naughty and by-passed marge")
                    merge_request.comment(
                        "A merge request may have skipped the queue, trying again..."
                    )
                    continue
                # otherwise the source branch has been pushed to or something
                # unexpected went wrong in either case, we expect the user to
                # explicitly re-assign to marge (after resolving potential
                # problems)
                raise mb_job.CannotMerge(
                    f"Merge request was rejected by GitLab: {err.error_message!r}"
                ) from err
            except gitlab.Unauthorized as err:
                log.warning("Unauthorized!")
                raise mb_job.CannotMerge(
                    "This user does not have permission to merge MRs."
                ) from err
            except gitlab.NotFound as ex:
                log.warning("Not Found!: %s", ex)
                merge_request.refetch_info()
                if merge_request.state == "merged":
                    # someone must have hit "merge when build succeeds" and we lost the race,
                    # the branch is gone and we got a 404. Anyway, our job here is done.
                    # (see #33)
                    updated_into_up_to_date_target_branch = True
                else:
                    log.warning(
                        "For the record, merge request state is %r", merge_request.state
                    )
                    raise
            except gitlab.MethodNotAllowed as ex:
                log.warning("Not Allowed!: %s", ex)
                merge_request.refetch_info()
                if merge_request.draft:
                    raise mb_job.CannotMerge(
                        "The request was marked as Draft as the bot was processing it."
                        " Maybe a Draft commit was pushed?"
                    ) from ex
                if merge_request.state == "reopened":
                    raise mb_job.CannotMerge(
                        "GitLab could not merge this branch. Possibly a Push Rule or a git-hook "
                        "is rejecting the commits; maybe the bot's email needs to be allow-listed?"
                    ) from ex
                if merge_request.state == "closed":
                    raise mb_job.CannotMerge(
                        "The merge request was closed while the merge was being attempted."
                    ) from ex
                if merge_request.state == "merged":
                    # We are not covering any observed behaviour here, but if at this
                    # point the request is merged, our job is done, so no need to complain
                    log.info("Merge request is already merged, someone was faster!")
                    updated_into_up_to_date_target_branch = True
                else:
                    raise mb_job.CannotMerge(
                        "Gitlab could not merge this branch for an unknown reason."
                        + (
                            " Maybe there are unresolved discussions?"
                            if self._project.only_allow_merge_if_all_discussions_are_resolved
                            else ""
                        )
                    ) from ex
            except gitlab.ApiError as err:
                log.exception("Unanticipated ApiError from GitLab on merge attempt")
                raise mb_job.CannotMerge(
                    "The was an unknown GitLab error. Check bot logs for more details."
                ) from err
            else:
                self.wait_for_branch_to_be_merged()
                updated_into_up_to_date_target_branch = True

    def wait_for_branch_to_be_merged(self) -> None:
        merge_request = self._merge_request
        time_0 = datetime.datetime.utcnow()
        waiting_time_in_secs = 10

        while datetime.datetime.utcnow() - time_0 < self._merge_timeout:
            merge_request.refetch_info()

            if merge_request.state == "merged":
                return  # success!
            if merge_request.state == "closed":
                raise mb_job.CannotMerge(
                    "The merge request was closed while the merge was being attempted."
                )
            assert merge_request.state in (
                "opened",
                "reopened",
                "locked",
            ), merge_request.state

            log.info(
                "Giving %s more secs for !%s to be merged...",
                waiting_time_in_secs,
                merge_request.iid,
            )
            time.sleep(waiting_time_in_secs)

        raise mb_job.CannotMerge(
            "It is taking too long to see the request marked as merged!"
        )
