# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""
Common command options for complyscribe commands.
"""

import logging
import os
import pathlib
import sys
import traceback
from typing import Any, Callable, Dict, Optional, Sequence, TypeVar

import click

from complyscribe.cli.config import ComplyScribeConfigError, load_from_file
from complyscribe.cli.log import set_log_level
from complyscribe.const import COMPLYSCRIBE_CONFIG_DIR, ERROR_EXIT_CODE


F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def handle_exceptions(func: F) -> Any:
    def wrapper(*args: Sequence[Any], **kwargs: Dict[Any, Any]) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            traceback_str = traceback.format_exc()
            logger.error(f"complyscribe error: {str(ex)}")
            logger.debug(traceback_str)
            return ERROR_EXIT_CODE

    return wrapper


def debug_to_log_level(ctx: click.Context, param: str, value: str) -> None:
    """Sets logging level based on debug flag."""

    #  TODO: get log level from config file
    log_level = logging.DEBUG if value else logging.INFO
    set_log_level(log_level)


def load_config_to_ctx(
    ctx: click.Context, param: str, value: pathlib.Path
) -> Optional[pathlib.Path]:
    """Load yaml config file into Click context to set default values.  This
    allows values from the yaml config to be used as the default value for a
    given command option.

    If the user specifies a value for the option directly (e.g. uses --option value)
    then that value is used in favor of the value loaded from the config.

    Similarly, if an option has an associated ENVVAR, and that ENVVAR is set, then the
    ENVVAR value is used in favor of the value loaded from the config.

    Since the config contains values that should not be mapped to command option values
    the dictionary is explicitly built by directly plucking values from the config.

    This will always run before other options because the --config is_eager is True.
    """
    try:
        config = load_from_file(value)
        if not config:
            logger.debug(f"No complyscibe config file found at {value}.")
            return value
    except ComplyScribeConfigError as ex:
        logger.error(str(ex))
        for err in ex.errors:
            logger.error({err})
        sys.exit(ERROR_EXIT_CODE)

    if not ctx.default_map:
        ctx.default_map = {
            "repo_path": config.repo_path,
            "markdown_dir": config.markdown_dir,
            "ssp_index_file": config.ssp_index_file,
            "committer_name": config.committer_name,
            "committer_email": config.committer_email,
            "commit_message": config.commit_message,
            "branch": config.branch,
            "upstreams": config.upstreams,
        }
    else:
        ctx.default_map.update(config)
        logger.debug(f"Successfully loaded config file {value} into context.")
    return value


def common_options(f: F) -> F:
    """
    Configures common options used across commands.
    """

    f = click.option(
        "--debug",
        default=False,
        is_flag=True,
        is_eager=True,
        envvar="COMPLYSCRIBE_DEBUG",
        help="Enable debug logging messages.",
        callback=debug_to_log_level,
    )(f)
    f = click.option(
        "--config",
        "config_path",
        type=click.Path(path_type=pathlib.Path),
        envvar="COMPLYSCRIBE_CONFIG",
        help="Path to complyscribe configuration file.",
        default=f"{COMPLYSCRIBE_CONFIG_DIR}/config.yml",
        is_eager=True,
        callback=load_config_to_ctx,
    )(f)
    click.option(
        "--repo-path",
        type=click.Path(path_type=pathlib.Path, exists=True),
        envvar="COMPLYSCRIBE_REPO_PATH",
        help="Path to git respository root.",
        required=True,
        default=os.getcwd(),
    )(f)
    f = click.option(
        "--dry-run",
        help="Run tasks, but do not push changes to the repository.",
        is_flag=True,
    )(f)

    return f


def git_options(f: F) -> F:
    """
    Configure git options used for git operations.
    """
    f = click.option(
        "--branch",
        help="Git repo branch to push automated changes.",
        required=True,
        type=str,
    )(f)
    f = click.option(
        "--target-branch",
        help="Target branch (base branch) to create a pull request against. \
            No pull request is created if unset.",
        required=False,
        type=str,
    )(f)
    f = click.option(
        "--committer-name",
        help="User name for git committer.",
        required=True,
        type=str,
    )(f)
    f = click.option(
        "--committer-email",
        help="User email for git committer",
        required=True,
        type=str,
    )(f)
    f = click.option(
        "--file-patterns",
        help="Comma-separated list of file patterns to be used with `git add` in repository updates.",
        type=str,
        default=".",
    )(f)
    f = click.option(
        "--commit-message",
        help="Commit message for automated updates.",
        default="Automatic updates from complyscribe",
        type=str,
    )(f)
    f = click.option(
        "--author-name",
        help="Name for commit author if differs from committer.",
        type=str,
    )(f)
    f = click.option(
        "--author-email",
        help="Email for commit author if differs from committer.",
        type=str,
    )(f)

    return f
