from unittest.mock import Mock

import pytest

from marge.gitlab import GET, Api
from marge.project import AccessLevel, Project

INFO = {
    "id": 1234,
    "path_with_namespace": "cool/project",
    "ssh_url_to_repo": "ssh://blah.com/cool/project.git",
    "merge_requests_enabled": True,
    "default_branch": "master",
    "only_allow_merge_if_pipeline_succeeds": True,
    "only_allow_merge_if_all_discussions_are_resolved": False,
    "permissions": {
        "project_access": {"access_level": AccessLevel.developer.value},
        "group_access": {"access_level": AccessLevel.developer.value},
    },
}

GROUP_ACCESS = {
    "project_access": None,
    "group_access": {"access_level": AccessLevel.developer.value},
}

NONE_ACCESS = {"project_access": None, "group_access": None}


# pylint: disable=attribute-defined-outside-init,duplicate-code
class TestProject:
    def setup_method(self, _method):
        self.api = Mock(Api)

    def test_fetch_by_id(self):
        api = self.api
        api.call = Mock(return_value=INFO)

        project = Project.fetch_by_id(project_id=1234, api=api)

        api.call.assert_called_once_with(GET("/projects/1234"))
        assert project.info == INFO

    def test_properties(self):
        project = Project(api=self.api, info=INFO)
        assert project.id == 1234
        assert project.path_with_namespace == "cool/project"
        assert project.ssh_url_to_repo == "ssh://blah.com/cool/project.git"
        assert project.merge_requests_enabled is True
        assert project.only_allow_merge_if_pipeline_succeeds is True
        assert project.only_allow_merge_if_all_discussions_are_resolved is False
        assert project.access_level == AccessLevel.developer

    def test_group_access(self):
        project = Project(api=self.api, info=dict(INFO, permissions=GROUP_ACCESS))
        bad_project = Project(api=self.api, info=dict(INFO, permissions=NONE_ACCESS))
        assert project.access_level == AccessLevel.developer
        with pytest.raises(AssertionError):
            bad_project.access_level  # pylint: disable=pointless-statement
