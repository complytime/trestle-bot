# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""This module implements functions for the complyscribe bot."""

import logging
from typing import List, Optional

from git import GitCommandError
from git.objects.commit import Commit
from git.repo import Repo
from git.util import Actor

from complyscribe.provider import GitProvider, GitProviderException
from complyscribe.reporter import BotResults
from complyscribe.tasks.base_task import TaskBase, TaskException


logger = logging.getLogger(__name__)


class RepoException(Exception):
    """An error requiring the user to perform a manual action in the
    destination repo
    """


class ComplyScribe:
    """complyscribe class for managing git repositories."""

    def __init__(
        self,
        working_dir: str,
        branch: str,
        commit_name: str,
        commit_email: str,
        author_name: str = "",
        author_email: str = "",
        target_branch: str = "",
    ) -> None:
        """Initialize ComplyScribe.

        Args:
             working_dir: Location of the git repository
             branch: Branch to push updates to
             commit_name: Name of the user for commit creation
             commit_email: Email of the user for commit creation
             author_name: Optional name of the commit author
             author_email: Optional email of the commit author
             target_branch: Optional target or base branch for submitted pull request
        """
        self.working_dir = working_dir
        self.branch = branch
        self.target_branch = target_branch
        self.commit_name = commit_name
        self.commit_email = commit_email
        self.author_name = author_name
        self.author_email = author_email

    @staticmethod
    def _stage_files(gitwd: Repo, patterns: List[str]) -> None:
        """Stages files in git based on file patterns"""
        for pattern in patterns:
            if pattern == ".":
                logger.info("Staging all repository changes")
                # Using check to avoid adding git directory
                # https://github.com/gitpython-developers/GitPython/issues/292
                gitwd.git.add(all=True)
                return
            else:
                logger.info(f"Adding file for pattern {pattern}")
                gitwd.git.add(pattern)

    def _local_commit(
        self,
        gitwd: Repo,
        commit_message: str,
    ) -> Commit:
        """Creates a local commit in git working directory"""
        try:
            committer: Actor = Actor(name=self.commit_name, email=self.commit_email)

            author: Optional[Actor] = None
            if self.author_name and self.author_email:
                author = Actor(name=self.author_name, email=self.author_email)
            commit = gitwd.index.commit(
                commit_message, author=author, committer=committer
            )
            return commit

        except GitCommandError as e:
            raise RepoException(f"Git commit failed: {e}") from e

    def _push_to_remote(self, gitwd: Repo) -> str:
        """Pushes the local branch to the remote repository"""
        remote = gitwd.remote()

        # Push changes to the remote repository
        remote.push(refspec=f"HEAD:{self.branch}")

        logger.info(f"Changes pushed to {self.branch} successfully.")
        return remote.url

    def _create_pull_request(
        self,
        git_provider: GitProvider,
        remote_url: str,
        pull_request_title: str,
    ) -> int:
        """Creates a pull request in the remote repository"""

        # Parse remote url to get repository information for pull request
        namespace, repo_name = git_provider.parse_repository(remote_url)
        logger.debug(f"Detected namespace {namespace} and {repo_name}")

        pr_number = git_provider.create_pull_request(
            ns=namespace,
            repo_name=repo_name,
            head_branch=self.branch,
            base_branch=self.target_branch,
            title=pull_request_title,
            body="Authored by complyscribe.",
        )
        return pr_number

    def _checkout_branch(self, gitwd: Repo) -> None:
        """Checkout the branch"""
        try:
            branch_names: List[str] = [b.name for b in gitwd.branches]  # type: ignore
            if self.branch in branch_names:
                logger.debug(f"Local branch {self.branch} found")
                gitwd.git.checkout(self.branch)
            else:
                logger.debug(f"Local branch {self.branch} created")
                gitwd.git.checkout("-b", self.branch)
        except GitCommandError as e:
            raise RepoException(f"Git checkout failed: {e}") from e

    def _run_tasks(self, tasks: List[TaskBase]) -> None:
        """Run tasks"""
        for task in tasks:
            try:
                task.execute()
            except TaskException as e:
                raise RepoException(f"Bot pre-tasks failed: {e}")

    def _get_committed_files(self, commit: Commit) -> List[str]:
        """Get the list of committed files in the commit."""
        changes: List[str] = []
        if commit.parents:
            diffs = {diff.a_path: diff for diff in commit.parents[0].diff(commit)}
            for path in commit.stats.files.keys():
                diff = diffs.get(path, None)
                if diff:
                    if diff.change_type == "A":
                        changes.append(f"{path} [added]")
                    elif diff.change_type == "M":
                        changes.append(f"{path} [modified]")
                    elif diff.change_type == "D":
                        changes.append(f"{path} [deleted]")
                    elif diff.change_type == "R":
                        changes.append(f"{path} [renamed]")
        else:
            for path in commit.stats.files.keys():
                changes.append(f"{path} [added]")
        return changes

    def run(
        self,
        patterns: List[str],
        git_provider: Optional[GitProvider] = None,
        pre_tasks: Optional[List[TaskBase]] = None,
        commit_message: str = "Automatic updates from bot",
        pull_request_title: str = "Automatic updates from bot",
        dry_run: bool = False,
    ) -> BotResults:
        """
        Runs complyscribe logic and returns commit and pull request information.

        Args:
                patterns: List of file patterns for `git add`
                git_provider: Optional configured git provider for interacting with the API
                pre_tasks: Optional workspace task list to execute before staging files
                commit_message: Optional commit message for local commit
                pull_request_title: Optional customized pull request title
                dry_run: Only complete pre-tasks and return changes without pushing

        Returns:
            BotResults with changes, commit_sha, and pull request number.
            The commit_sha defaults to "" if there was no updates and the
            pull request number default to 0 if not submitted. The changes list is
            only populated if dry_run is enabled.
        """
        results: BotResults = BotResults([], "", 0)

        # Create Git Repo
        repo = Repo(self.working_dir)
        self._checkout_branch(repo)

        # Execute bot pre-tasks before committing repository updates
        if pre_tasks:
            self._run_tasks(pre_tasks)

        # Check if there are any unstaged files
        if repo.is_dirty(untracked_files=True):

            self._stage_files(repo, patterns)

            if repo.is_dirty():

                commit: Commit = self._local_commit(
                    repo,
                    commit_message,
                )
                results.commit_sha = commit.hexsha

                # Do not return the commit sha if dry run is enabled
                if dry_run:
                    logger.info("Dry run mode is enabled, no changes will be pushed")
                    return BotResults(self._get_committed_files(commit), "", 0)

                try:
                    remote_url = self._push_to_remote(repo)

                    # Only create a pull request if a GitProvider is configured and
                    # a target branch is set.
                    if git_provider and self.target_branch:
                        logger.info(
                            f"Git provider detected, submitting pull request to {self.target_branch}"
                        )
                        results.pr_number = self._create_pull_request(
                            git_provider, remote_url, pull_request_title
                        )
                    return results

                except GitCommandError as e:
                    raise RepoException(f"Git push to {self.branch} failed: {e}")
                except GitProviderException as e:
                    raise RepoException(
                        f"Git pull request to {self.target_branch} failed: {e}"
                    )
            else:
                logger.info("Nothing to commit")
                return results
        else:
            logger.info("Nothing to commit")
            return results
