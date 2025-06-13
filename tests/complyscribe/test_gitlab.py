# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test for GitLab provider logic"""

from typing import Callable, Generator, Tuple
from unittest.mock import patch

import pytest
from git.repo import Repo
from gitlab.exceptions import GitlabAuthenticationError, GitlabCreateError
from responses import GET, POST, RequestsMock

from complyscribe.gitlab import GitLab, GitLabCIResultsReporter
from complyscribe.provider import GitProviderException
from complyscribe.reporter import BotResults


@pytest.mark.parametrize(
    "repo_url",
    [
        "https://gitlab.com/owner/repo",
        "https://gitlab.com/owner/repo.git",
        "https://test:test@gitlab.com/owner/repo.git",
        "gitlab.com/owner/repo.git",
    ],
)
def test_parse_repository(repo_url: str) -> None:
    """Tests parsing valid GitLab repo urls"""
    gl = GitLab("fake")

    owner, repo_name = gl.parse_repository(repo_url)

    assert owner == "owner"
    assert repo_name == "repo"


@pytest.mark.parametrize(
    "repo_url",
    [
        "https://mygitlab.com/owner/repo",
        "https://mygitlab.com/owner/repo.git",
        "mygitlab.com/owner/repo.git",
    ],
)
def test_parse_repository_with_server_url(repo_url: str) -> None:
    """Test with a custom server url"""
    gl = GitLab("fake", "https://mygitlab.com")

    owner, repo_name = gl.parse_repository(repo_url)

    assert owner == "owner"
    assert repo_name == "repo"


@pytest.mark.parametrize(
    "repo_url",
    [
        "https://mygitlab.com/group/owner/repo",
        "https://mygitlab.com/group/owner/repo.git",
        "mygitlab.com/group/owner/repo.git",
    ],
)
def test_parse_repository_with_group(repo_url: str) -> None:
    """Test with nested namespaces"""
    gl = GitLab("fake", "https://mygitlab.com")

    owner, repo_name = gl.parse_repository(repo_url)

    assert owner == "group/owner"
    assert repo_name == "repo"


def test_parse_repository_integration(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests integration with git remote get-url"""
    repo_path, repo = tmp_repo

    remote = repo.create_remote("test", url="gitlab.com/test/repo.git")

    gl = GitLab("fake")

    owner, repo_name = gl.parse_repository(remote.url)

    assert owner == "test"
    assert repo_name == "repo"


def test_parse_repository_with_incorrect_name() -> None:
    """Test an invalid url input"""
    gl = GitLab("fake")
    with pytest.raises(
        GitProviderException,
        match="https://notgitlab.com/owner/repo.git is an invalid Gitlab repo URL",
    ):
        gl.parse_repository("https://notgitlab.com/owner/repo.git")


mr_content = {
    "id": 123,
    "title": "Example Merge Request",
    "description": "This is an example merge request description.",
    "state": "opened",
    "created_at": "2023-12-06T08:30:00Z",
    "updated_at": "2023-12-06T09:15:00Z",
    "source_branch": "feature-branch",
    "target_branch": "main",
    "author": {"id": 789, "name": "Jane Doe", "username": "janedoe"},
    "merge_status": "can_be_merged",
}


@pytest.fixture
def resp_merge_requests() -> Generator[RequestsMock, None, None]:
    with RequestsMock() as rsps:
        rsps.add(
            method=POST,
            url="http://localhost/api/v4/projects/1/merge_requests",
            json=mr_content,
            content_type="application/json",
            status=201,
        )
        rsps.add(
            method=GET,
            url="http://localhost/api/v4/projects/owner%2Frepo",
            json={"name": "name", "id": 1},
            content_type="application/json",
            status=200,
        )
        yield rsps


def test_create_pull_request(resp_merge_requests: RequestsMock) -> None:
    """Test creating a pull request"""
    gl = GitLab("fake", "http://localhost")
    pr_number = gl.create_pull_request(
        "owner", "repo", "main", "test", "My PR", "Has Changes"
    )
    assert pr_number == 123


def create_side_effect(name: str) -> None:
    raise GitlabCreateError("example")


def auth_side_effect(name: str) -> None:
    raise GitlabAuthenticationError("example")


@pytest.mark.parametrize(
    "side_effect, msg",
    [
        (create_side_effect, "Failed to create merge request in .*: example"),
        (
            auth_side_effect,
            "Authentication error during merge request creation in .*: example",
        ),
    ],
)
def test_create_pull_request_with_exceptions(
    side_effect: Callable[[str], None], msg: str
) -> None:
    """Test triggering an error during pull request creation"""
    gl = GitLab("fake")

    with patch("gitlab.v4.objects.ProjectManager.get") as mock_get:
        mock_get.side_effect = side_effect

        with pytest.raises(
            GitProviderException,
            match=msg,
        ):
            gl.create_pull_request(
                "owner", "repo", "main", "test", "My PR", "Has Changes"
            )
        mock_get.assert_called_once()


def test_gitlab_ci_results_reporter() -> None:
    """Test results reporter"""

    results = BotResults(changes=[], commit_sha="", pr_number=0)

    expected_output = "No changes detected"
    with patch("builtins.print") as mock_print:
        GitLabCIResultsReporter().report_results(results)
        mock_print.assert_any_call(expected_output)

    results = BotResults(changes=[], commit_sha="123456", pr_number=2)
    expected_output = (
        "\x1b[0Ksection_start:1234567890:commit_sha"
        "[collapsed=true]\r\x1b[0KCommit Information\n123456\n"
        "\x1b[0Ksection_end:1234567890:commit_sha\r\x1b[0K\n"
        "\x1b[0Ksection_start:1234567890:merge_request_number[collapsed=true]\r\x1b[0K"
        "Merge Request Number\n2\n\x1b[0Ksection_end:1234567890:merge_request_number\r\x1b[0K\n"
    )
    with patch("builtins.print") as mock_print:
        with patch("time.time_ns", return_value=1234567890):
            GitLabCIResultsReporter().report_results(results)
            mock_print.assert_called_once_with(expected_output)

    results = BotResults(changes=["file2"], commit_sha="", pr_number=0)
    expected_output = (
        "\x1b[0Ksection_start:1234567890:changes[collapsed=true]\r\x1b"
        "[0KChanges detected\nfile2\n\x1b[0Ksection_end:1234567890:changes\r\x1b[0K\n"
    )
    with patch("builtins.print") as mock_print:
        with patch("time.time_ns", return_value=1234567890):
            GitLabCIResultsReporter().report_results(results)
            mock_print.assert_called_once_with(expected_output)
