# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

import logging
from typing import Optional

from complyscribe import const
from complyscribe.github import GitHub
from complyscribe.gitlab import GitLab
from complyscribe.provider import GitProvider


logger = logging.getLogger(__name__)


class GitProviderFactory:
    """Factory class for creating Git provider objects"""

    @staticmethod
    def provider_factory(access_token: str, type: str, server_url: str) -> GitProvider:
        """
        Factory class for creating Git provider objects

        Args:
            access_token: Access token for the Git provider
            type: Type of Git provider. Supported values are "github" or "gitlab"
            server_url: URL of the Git provider server

        Returns:
            a GitProvider object

        Raises:
            ValueError: If the server URL is provided for GitHub provider
            RuntimeError: If the Git provider cannot be detected


        Notes: The GitHub provider currently only supports GitHub and not
        GitHub Enterprise. So the server value must be https://github.com.
        """

        git_provider: Optional[GitProvider] = None

        if type == const.GITHUB:
            logger.debug("Creating GitHub provider")
            if server_url and server_url != const.GITHUB_SERVER_URL:
                raise ValueError("GitHub provider does not support custom server URLs")
            git_provider = GitHub(access_token=access_token)
        elif type == const.GITLAB:
            logger.debug("Creating GitLab provider")
            if not server_url:
                # No server URL will use default https://gitlab.com
                git_provider = GitLab(api_token=access_token)
            else:
                git_provider = GitLab(api_token=access_token, server_url=server_url)

        if git_provider is None:
            raise RuntimeError("Could not determine Git provider from inputs")

        return git_provider
