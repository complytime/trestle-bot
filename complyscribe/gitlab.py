# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""GitLab related functions for the ComplyScribe."""

from __future__ import annotations

import os
import re
import time
from typing import Optional, Tuple
from urllib.parse import ParseResult, urlparse

import gitlab

from complyscribe.provider import GitProvider, GitProviderException
from complyscribe.reporter import BotResults, ResultsReporter


class GitLab(GitProvider):
    def __init__(self, api_token: str, server_url: str = "https://gitlab.com"):
        """Create GitLab object to interact with the GitLab API"""

        self._gitlab_client = gitlab.Gitlab(server_url, private_token=api_token)

        # For repo URL input validation
        parsed_url: ParseResult = urlparse(server_url)
        stripped_url = f"{parsed_url.netloc}{parsed_url.path}"
        pattern = rf"^(?:https?://)?{re.escape(stripped_url)}(/.+)/([^/.]+)(\.git)?$"
        self._pattern = re.compile(pattern)

    @property
    def provider_pattern(self) -> re.Pattern[str]:
        """Regex pattern to validate repository URLs"""
        return self._pattern

    def parse_repository(self, repo_url: str) -> Tuple[str, str]:
        """
        Parse repository url

        Args:
            repo_url: Valid url for a GitLab repo

        Returns:
            Owner and project name in a tuple, respectively
        """

        match: Optional[re.Match[str]]
        stripped_url: str
        match, stripped_url = self.match_url(repo_url)

        if not match:
            raise GitProviderException(f"{stripped_url} is an invalid Gitlab repo URL")

        owner = match.group(1)[1:]  # Removing the leading slash
        repo = match.group(2)
        return (owner, repo)

    def create_pull_request(
        self,
        ns: str,
        repo_name: str,
        base_branch: str,
        head_branch: str,
        title: str,
        body: str,
    ) -> int:
        """
        Create a pull (merge request in the GitLab) request in the repository

        Args:
            ns: Namespace or owner of the repository
            repo_name: Name of the repository
            base_branch: Branch that changes need to be merged into
            head_branch: Branch with changes
            title: Text for the title of the pull_request
            body: Text for the body of the pull request

        Returns:
            Pull/Merge request number
        """

        try:
            project = self._gitlab_client.projects.get(f"{ns}/{repo_name}")
            merge_request = project.mergerequests.create(
                {
                    "source_branch": head_branch,
                    "target_branch": base_branch,
                    "title": title,
                    "description": body,
                }
            )

            return merge_request.id

        except gitlab.exceptions.GitlabCreateError as e:
            raise GitProviderException(
                f"Failed to create merge request in {ns}/{repo_name}: {e}"
            )
        except gitlab.exceptions.GitlabAuthenticationError as e:
            raise GitProviderException(
                f"Authentication error during merge request creation in {ns}/{repo_name}: {e}"
            )


class GitLabCIResultsReporter(ResultsReporter):
    """Report bot results to the console in GitLabCI"""

    start_sequence = "\x1b[0K"
    end_sequence = "\r\x1b[0K"

    def report_results(self, results: BotResults) -> None:
        """
        Report the results of the ComplyScribe in GitLab CI
        """
        results_str = ""
        if results.commit_sha:
            commit_str = self._create_group(
                "commit_sha",
                "Commit Information",
                results.commit_sha,
            )
            results_str += commit_str

            if results.pr_number:
                pr_str = self._create_group(
                    "merge_request_number",
                    "Merge Request Number",
                    str(results.pr_number),
                )
                results_str += pr_str
        elif results.changes:
            changes_str = self._create_group(
                "changes", "Changes detected", self.get_changes_str(results.changes)
            )
            results_str += changes_str
        else:
            results_str += "No changes detected"
        print(results_str)  # noqa: T201

    @staticmethod
    def _create_group(
        section_title: str, section_description: str, content: str
    ) -> str:
        """Create a group for the GitLab CI output"""
        group_str = GitLabCIResultsReporter.start_sequence
        group_str += f"section_start:{time.time_ns()}:{section_title}[collapsed=true]"
        group_str += GitLabCIResultsReporter.end_sequence
        group_str += f"{section_description}\n{content}\n"
        group_str += GitLabCIResultsReporter.start_sequence
        group_str += f"section_end:{time.time_ns()}:{section_title}"
        group_str += GitLabCIResultsReporter.end_sequence
        group_str += "\n"
        return group_str


# GitLab ref: https://docs.gitlab.com/ee/ci/variables/predefined_variables.html
def is_gitlab_ci() -> bool:
    """Determine if the environment is GitLab CI"""
    var_value = os.getenv("GITLAB_CI")
    if var_value and var_value.lower() in ["true", "1"]:
        return True
    return False


def get_gitlab_root_url() -> str:
    """Get the GitLab URL"""
    protocol = os.getenv("CI_SERVER_PROTOCOL")
    host = os.getenv("CI_SERVER_HOST")
    if protocol and host:
        return f"{protocol}://{host}"
    else:
        raise GitProviderException(
            "Set CI_SERVER_PROTOCOL and CI SERVER HOST environment variables"
        )
