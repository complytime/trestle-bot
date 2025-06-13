# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Base Git Provider class for ComplyScribe."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from urllib.parse import ParseResult, urlparse


class GitProviderException(Exception):
    """An error when interacting with a Git provider"""


class GitProvider(ABC):
    """
    Abstract base class for Git provider types
    """

    @property
    @abstractmethod
    def provider_pattern(self) -> re.Pattern[str]:
        """Regex pattern to validate repository URLs"""

    def match_url(self, repo_url: str) -> Tuple[Optional[re.Match[str]], str]:
        """Match a repository URL with the pattern"""
        parsed_url: ParseResult = urlparse(repo_url)

        path = parsed_url.path
        stripped_url = path
        if host := parsed_url.hostname:
            stripped_url = f"{host}{path}"
        if scheme := parsed_url.scheme:
            stripped_url = f"{scheme}://{stripped_url}"
        return self.provider_pattern.match(stripped_url), stripped_url

    @abstractmethod
    def parse_repository(self, repository_url: str) -> Tuple[str, str]:
        """Parse repository information into namespace and repo, respectively"""

    @abstractmethod
    def create_pull_request(
        self,
        ns: str,
        repo_name: str,
        base_branch: str,
        head_branch: str,
        title: str,
        body: str,
    ) -> int:
        """Create a pull request for a specified branch and return the request number"""
