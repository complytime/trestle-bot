# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test for GitHub provider logic"""

import json
import tempfile
from typing import Generator, Tuple
from unittest.mock import patch

import pytest
from git.repo import Repo
from responses import GET, POST, RequestsMock

from complyscribe.github import GitHub, GitHubActionsResultsReporter, set_output
from complyscribe.provider import GitProviderException
from complyscribe.reporter import BotResults
from tests.testutils import JSON_TEST_DATA_PATH


@pytest.mark.parametrize(
    "repo_url",
    [
        "https://github.com/owner/repo",
        "https://github.com/owner/repo.git",
        "github.com/owner/repo.git",
    ],
)
def test_parse_repository(repo_url: str) -> None:
    """Tests parsing valid GitHub repo urls"""
    gh = GitHub("fake")

    owner, repo_name = gh.parse_repository(repo_url)

    assert owner == "owner"
    assert repo_name == "repo"


def test_parse_repository_integration(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests integration with git remote get-url"""
    repo_path, repo = tmp_repo

    remote = repo.create_remote("test", url="github.com/test/repo.git")

    gh = GitHub("fake")

    owner, repo_name = gh.parse_repository(remote.url)

    assert owner == "test"
    assert repo_name == "repo"


def test_parse_repository_with_incorrect_name() -> None:
    """Test an invalid url input"""
    gh = GitHub("fake")
    with pytest.raises(
        GitProviderException,
        match="https://notgithub.com/owner/repo.git is an invalid GitHub repo URL",
    ):
        gh.parse_repository("https://notgithub.com/owner/repo.git")


@pytest.fixture
def resp_merge_requests() -> Generator[RequestsMock, None, None]:
    """Mock the GitHub API for pull request creation"""
    repo_content = json.load(
        open(JSON_TEST_DATA_PATH / "github_example_repo_response.json")
    )
    pr_content = json.load(
        open(JSON_TEST_DATA_PATH / "github_example_pull_response.json")
    )
    with RequestsMock() as rsps:
        rsps.add(
            method=POST,
            url="https://api.github.com/repos/owner/repo/pulls",
            json=pr_content,
            content_type="application/json",
            status=201,
        )
        rsps.add(
            method=GET,
            url="https://api.github.com/repos/owner/repo",
            json=repo_content,
            content_type="application/json",
            status=200,
        )
        yield rsps


def test_create_pull_request(resp_merge_requests: RequestsMock) -> None:
    """Test creating a pull request"""
    gh = GitHub("fake")
    pr_number = gh.create_pull_request(
        "owner", "repo", "main", "test", "My PR", "Has Changes"
    )
    assert pr_number == 123


def test_create_pull_request_invalid_repo() -> None:
    """Test triggering an error during pull request creation"""
    gh = GitHub("fake")
    with patch("github3.GitHub.repository") as mock_pull:
        mock_pull.return_value = None

        with pytest.raises(
            GitProviderException,
            match="Repository for owner/repo cannot be None",
        ):
            gh.create_pull_request(
                "owner", "repo", "main", "test", "My PR", "Has Changes"
            )
        mock_pull.assert_called_once()


def test_set_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test set output"""
    tmpdir = tempfile.TemporaryDirectory()
    tmpfile_path = f"{tmpdir.name}/output.txt"
    with open(tmpfile_path, "w") as tmpfile:
        tmpfile.write("")

    monkeypatch.setenv("GITHUB_OUTPUT", tmpfile_path)

    set_output("name", "value")

    with open(tmpfile_path, "r") as tmpfile:
        content = tmpfile.read()
        assert "name=value" in content


def test_github_actions_results_reporter() -> None:
    """Test results reporter"""
    results = BotResults(changes=[], commit_sha="123456", pr_number=2)

    expected_output = "::group::Commit\n123456\n::endgroup::\n::group::Pull Request\n2\n::endgroup::\n"

    # Mock set output
    def mock_set_output(name: str, value: str) -> None:
        print(f"{name}={value}")  # noqa: T201

    with patch("builtins.print") as mock_print:
        with patch(
            "complyscribe.github.set_output", side_effect=mock_set_output
        ) as mock_set_output:
            GitHubActionsResultsReporter().report_results(results)
            mock_print.assert_any_call(expected_output)
            mock_print.assert_any_call("changes=true")
            mock_print.assert_any_call("commit=123456")
            mock_print.assert_any_call("pr_number=2")

    results = BotResults(changes=["file1"], commit_sha="", pr_number=0)

    expected_output = "::group::Changes\nfile1\n::endgroup::\n"
    with patch("builtins.print") as mock_print:
        with patch(
            "complyscribe.github.set_output", side_effect=mock_set_output
        ) as mock_set_output:
            GitHubActionsResultsReporter().report_results(results)
            mock_print.assert_any_call(expected_output)
            mock_print.assert_any_call("changes=true")

    results = BotResults(changes=[], commit_sha="", pr_number=0)

    expected_output = "No changes detected"
    with patch("builtins.print") as mock_print:
        with patch(
            "complyscribe.github.set_output", side_effect=mock_set_output
        ) as mock_set_output:
            GitHubActionsResultsReporter().report_results(results)
            mock_print.assert_any_call(expected_output)
            mock_print.assert_any_call("changes=false")
