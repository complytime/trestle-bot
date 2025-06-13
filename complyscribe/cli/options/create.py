# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""
Module for common create commands
"""

import functools
from typing import Any, Callable, Dict, Sequence, TypeVar

import click


F = TypeVar("F", bound=Callable[..., Any])


def common_create_options(f: F) -> F:
    """
    Configuring common create options decorator for SSP and CD command
    """

    @click.option(
        "--profile-name",
        prompt="Enter name of profile in trestle workspace to include",
        help="Name of profile in trestle workspace to include.",
    )
    @click.option(
        "--markdown-dir",
        type=str,
        prompt="Enter path to store markdown files",
        default="markdown/",
        help="Directory name to store markdown files.",
    )
    @functools.wraps(f)
    def wrapper_common_create_options(
        *args: Sequence[Any], **kwargs: Dict[Any, Any]
    ) -> Any:
        return f(*args, **kwargs)

    return wrapper_common_create_options
