# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test for top-level complyscribe logic."""

import os
from typing import Callable, List, Tuple
from unittest.mock import Mock, patch

import pytest
from git import GitCommandError
from git.repo import Repo

from complyscribe.bot import ComplyScribe, RepoException
from complyscribe.provider import GitProvider, GitProviderException
from complyscribe.tasks.base_task import TaskBase, TaskException


def check_lists_equal(list1: List[str], list2: List[str]) -> bool:
    return sorted(list1) == sorted(list2)


@pytest.mark.parametrize(
    "file_patterns, expected_files",
    [
        (["*.txt"], ["file1.txt", "file2.txt"]),
        (["file*.txt"], ["file1.txt", "file2.txt"]),
        (["*.csv"], ["file3.csv"]),
        (["file*.csv"], ["file3.csv"]),
        (["*.txt", "*.csv"], ["file1.txt", "file2.txt", "file3.csv"]),
        (["."], ["file1.txt", "file2.txt", "file3.csv"]),
        ([], []),
    ],
)
def test_stage_files(
    tmp_repo: Tuple[str, Repo], file_patterns: List[str], expected_files: List[str]
) -> None:
    """Test staging files by patterns"""
    repo_path, repo = tmp_repo

    # Create test files
    with open(os.path.join(repo_path, "file1.txt"), "w") as f:
        f.write("Test file 1 content")
    with open(os.path.join(repo_path, "file2.txt"), "w") as f:
        f.write("Test file 2 content")
    with open(os.path.join(repo_path, "file3.csv"), "w") as f:
        f.write("test,")

    # Stage the files
    bot = ComplyScribe(
        working_dir=repo_path,
        branch="main",
        commit_name="Test User",
        commit_email="test@example.com",
    )
    bot._stage_files(repo, file_patterns)

    # Verify that files are staged
    staged_files = [item.a_path for item in repo.index.diff(repo.head.commit)]

    assert check_lists_equal(staged_files, expected_files) is True


def test_local_commit(tmp_repo: Tuple[str, Repo]) -> None:
    """Test local commit function"""
    repo_path, repo = tmp_repo

    # Create a test file
    test_file_path = os.path.join(repo_path, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("Test content")

    repo.index.add(test_file_path)

    # Commit the test file
    bot = ComplyScribe(
        working_dir=repo_path,
        branch="main",
        commit_name="Test User",
        commit_email="test@example.com",
    )
    commit_sha = bot._local_commit(
        repo,
        commit_message="Test commit message",
    )
    assert commit_sha != ""

    # Verify that the commit is made
    commit = next(repo.iter_commits())
    assert commit.message.strip() == "Test commit message"
    assert commit.author.name == "Test User"
    assert commit.author.email == "test@example.com"

    # Verify that the file is tracked by the commit
    assert os.path.basename(test_file_path) in commit.stats.files


def test_local_commit_with_author_information(tmp_repo: Tuple[str, Repo]) -> None:
    """Test setting author information for commits"""
    repo_path, repo = tmp_repo

    # Create a test file
    test_file_path = os.path.join(repo_path, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("Test content")

    repo.index.add(test_file_path)

    # Commit the test file
    bot = ComplyScribe(
        working_dir=repo_path,
        branch="main",
        commit_name="Test User",
        commit_email="test@example.com",
        author_name="Test Author User",
        author_email="test-author@example.com",
    )
    commit_sha = bot._local_commit(
        repo,
        commit_message="Test commit message",
    )
    assert commit_sha != ""

    # Verify that the commit is made
    commit = next(repo.iter_commits())
    assert commit.message.strip() == "Test commit message"
    assert commit.author.name == "Test Author User"
    assert commit.author.email == "test-author@example.com"

    # Verify that the file is tracked by the commit
    assert os.path.basename(test_file_path) in commit.stats.files


def test_run(tmp_repo: Tuple[str, Repo]) -> None:
    """Test bot run with mocked push"""
    repo_path, repo = tmp_repo

    # Create a test file
    test_file_path = os.path.join(repo_path, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("Test content")

    with patch("git.remote.Remote.push") as mock_push:
        mock_push.return_value = "Mocked result"

        # Test running the bot
        bot = ComplyScribe(
            working_dir=repo_path,
            branch="main",
            commit_name="Test User",
            commit_email="test@example.com",
            author_name="The Author",
            author_email="author@test.com",
        )
        results = bot.run(
            commit_message="Test commit message",
            patterns=["*.txt"],
        )
        assert not results.changes
        assert results.commit_sha != ""
        assert results.pr_number == 0

        # Verify that the commit is made
        commit = next(repo.iter_commits())
        assert commit.message.strip() == "Test commit message"
        assert commit.author.name == "The Author"
        assert commit.author.email == "author@test.com"
        mock_push.assert_called_once_with(refspec="HEAD:main")

        # Verify that the file is tracked by the commit
        assert os.path.basename(test_file_path) in commit.stats.files


def test_run_dry_run(tmp_repo: Tuple[str, Repo]) -> None:
    """Test bot run with dry run"""
    repo_path, _ = tmp_repo

    # Create a test file
    test_file_path = os.path.join(repo_path, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("Test content")

    with patch("git.remote.Remote.push") as mock_push:
        mock_push.return_value = "Mocked result"

        # Test running the bot
        bot = ComplyScribe(
            working_dir=repo_path,
            branch="main",
            commit_name="Test User",
            commit_email="test@example.com",
        )
        results = bot.run(
            commit_message="Test commit message",
            patterns=["*.txt"],
            dry_run=True,
        )
        assert results.changes == ["test.txt [added]"]
        assert results.commit_sha == ""
        assert results.pr_number == 0

        mock_push.assert_not_called()


def test_empty_commit(tmp_repo: Tuple[str, Repo]) -> None:
    """Test running bot with no file updates"""
    repo_path, _ = tmp_repo

    # Test running the bot
    bot = ComplyScribe(
        working_dir=repo_path,
        branch="main",
        commit_name="Test User",
        commit_email="test@example.com",
    )
    results = bot.run(
        commit_message="Test commit message",
        patterns=["*.txt"],
    )
    assert not results.changes
    assert results.commit_sha == ""
    assert results.pr_number == 0


def push_side_effect(refspec: str) -> None:
    raise GitCommandError("example")


def pull_side_effect(refspec: str) -> None:
    raise GitProviderException("example")


@pytest.mark.parametrize(
    "side_effect, msg",
    [
        (push_side_effect, "Git push to .* failed: .*"),
        (pull_side_effect, "Git pull request to .* failed: example"),
    ],
)
def test_run_with_exception(
    tmp_repo: Tuple[str, Repo], side_effect: Callable[[str], None], msg: str
) -> None:
    """Test bot run with mocked push with side effects that throw exceptions"""
    repo_path, _ = tmp_repo

    # Create a test file
    test_file_path = os.path.join(repo_path, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("Test content")

    bot = ComplyScribe(
        working_dir=repo_path,
        branch="main",
        commit_name="Test User",
        commit_email="test@example.com",
    )

    with patch("git.remote.Remote.push") as mock_push:
        mock_push.side_effect = side_effect

        with pytest.raises(RepoException, match=msg):
            _ = bot.run(
                commit_message="Test commit message",
                patterns=["*.txt"],
                dry_run=False,
            )


def test_run_with_failed_pre_task(tmp_repo: Tuple[str, Repo]) -> None:
    """Test bot run with mocked task that fails"""
    repo_path, _ = tmp_repo

    # Create a test file
    test_file_path = os.path.join(repo_path, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("Test content")

    mock = Mock(spec=TaskBase)
    mock.execute.side_effect = TaskException("example")

    bot = ComplyScribe(
        working_dir=repo_path,
        branch="main",
        commit_name="Test User",
        commit_email="test@example.com",
    )

    with pytest.raises(RepoException, match="Bot pre-tasks failed: example"):
        _ = bot.run(
            commit_message="Test commit message",
            patterns=["*.txt"],
            dry_run=True,
            pre_tasks=[mock],
        )


def test_run_with_provider(tmp_repo: Tuple[str, Repo]) -> None:
    """Test bot run with mock git provider"""
    repo_path, repo = tmp_repo

    # Create a test file
    test_file_path = os.path.join(repo_path, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("Test content")

    mock = Mock(spec=GitProvider)
    mock.create_pull_request.return_value = 10
    mock.parse_repository.return_value = ("ns", "repo")

    bot = ComplyScribe(
        working_dir=repo_path,
        branch="test",
        commit_name="Test User",
        commit_email="test@example.com",
        author_name="The Author",
        author_email="author@test.com",
        target_branch="main",
    )

    with patch("git.remote.Remote.push") as mock_push:
        mock_push.return_value = "Mocked result"

        # Test running the bot
        results = bot.run(
            commit_message="Test commit message",
            patterns=["*.txt"],
            git_provider=mock,
        )
        assert not results.changes
        assert results.commit_sha != ""
        assert results.pr_number == 10

        # Verify that the commit is made
        commit = next(repo.iter_commits())
        assert commit.message.strip() == "Test commit message"
        assert commit.author.name == "The Author"
        assert commit.author.email == "author@test.com"

        # Verify that the file is tracked by the commit
        assert os.path.basename(test_file_path) in commit.stats.files

        # Verify that the method was called with the expected arguments
        mock.create_pull_request.assert_called_once_with(
            ns="ns",
            repo_name="repo",
            head_branch="test",
            base_branch="main",
            title="Automatic updates from bot",
            body="Authored by complyscribe.",
        )
        mock_push.assert_called_once_with(refspec="HEAD:test")


def test_run_with_provider_with_custom_pr_title(tmp_repo: Tuple[str, Repo]) -> None:
    """Test bot run with customer pull request title"""
    repo_path, _ = tmp_repo

    # Create a test file
    test_file_path = os.path.join(repo_path, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("Test content")

    mock = Mock(spec=GitProvider)
    mock.create_pull_request.return_value = 10
    mock.parse_repository.return_value = ("ns", "repo")

    bot = ComplyScribe(
        working_dir=repo_path,
        branch="test",
        commit_name="Test User",
        commit_email="test@example.com",
        author_name="The Author",
        author_email="author@test.com",
        target_branch="main",
    )

    with patch("git.remote.Remote.push") as mock_push:
        mock_push.return_value = "Mocked result"

        # Test running the bot
        results = bot.run(
            commit_message="Test commit message",
            patterns=["*.txt"],
            git_provider=mock,
            pull_request_title="Test",
        )
        assert not results.changes
        assert results.commit_sha != ""
        assert results.pr_number == 10

        # Verify that the method was called with the expected arguments
        mock.create_pull_request.assert_called_once_with(
            ns="ns",
            repo_name="repo",
            head_branch="test",
            base_branch="main",
            title="Test",
            body="Authored by complyscribe.",
        )
        mock_push.assert_called_once_with(refspec="HEAD:test")
