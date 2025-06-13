# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Module for upstream command"""
import logging
import sys
from typing import Any, List

import click

from complyscribe.bot import ComplyScribe
from complyscribe.cli.options.common import (
    common_options,
    git_options,
    handle_exceptions,
)
from complyscribe.cli.utils import comma_sep_to_list
from complyscribe.const import ERROR_EXIT_CODE
from complyscribe.tasks.base_task import ModelFilter, TaskBase
from complyscribe.tasks.sync_upstreams_task import SyncUpstreamsTask


logger = logging.getLogger(__name__)


def load_value_from_ctx(
    ctx: click.Context, param: click.Parameter, value: Any = None
) -> Any:
    """Load config value for option from context."""
    if value:
        return value

    if not ctx.default_map:
        return None

    upstreams = ctx.default_map.get("upstreams")
    if not upstreams:
        return None

    config = upstreams.model_dump()
    value = config.get(param.name)
    if isinstance(value, List):
        return ",".join(value)
    return value


@click.command(
    name="sync-upstreams",
    help="Sync OSCAL content from upstream repositories.",
)
@click.pass_context
@click.option(
    "--sources",
    type=str,
    help="Comma-separated list of upstream git sources to sync. Each source is a string \
        in the form <repo_url>@<ref> where ref is a git ref such as a tag or branch.",
    envvar="COMPLYSCRIBE_UPSTREAMS_SOURCES",
    callback=load_value_from_ctx,
    required=False,
)
@click.option(
    "--exclude-models",
    type=str,
    help="Comma-separated list of glob patterns for model names to exclude when running \
        tasks (e.g. --include-models='component_x,profile_y*')",
    required=False,
    envvar="COMPLYSCRIBE_UPSTREAMS_EXCLUDE_MODELS",
    callback=load_value_from_ctx,
)
@click.option(
    "--include-models",
    type=str,
    default="*",
    help="Comma-separated list of glob patterns for model names to include when running \
        tasks (e.g. --include-models='component_x,profile_y*')",
    required=False,
    envvar="COMPLYSCRIBE_UPSTREAMS_INCLUDE_MODELS",
    callback=load_value_from_ctx,
)
@click.option(
    "--skip-validation",
    type=bool,
    help="Skip validation of the models when they are copied.",
    is_flag=True,
    envvar="COMPLYSCRIBE_UPSTREAMS_SKIP_VALIDATION",
    callback=load_value_from_ctx,
)
@common_options
@git_options
@handle_exceptions
def sync_upstreams_cmd(ctx: click.Context, **kwargs: Any) -> None:
    """Add new upstream sources to workspace."""
    if not kwargs.get("sources"):
        logger.error("complyscribe error: missing option '--sources'.")
        sys.exit(ERROR_EXIT_CODE)

    working_dir = str(kwargs["repo_path"].resolve())
    include_model_list = comma_sep_to_list(kwargs["include_models"])

    model_filter: ModelFilter = ModelFilter(
        skip_patterns=comma_sep_to_list(kwargs.get("exclude_models", "")),
        include_patterns=include_model_list,
    )

    validate: bool = not kwargs.get("skip_validation", False)

    sync_upstreams_task = SyncUpstreamsTask(
        working_dir=working_dir,
        git_sources=comma_sep_to_list(kwargs["sources"]),
        model_filter=model_filter,
        validate=validate,
    )

    pre_tasks: List[TaskBase] = [sync_upstreams_task]

    bot = ComplyScribe(
        working_dir=working_dir,
        branch=kwargs["branch"],
        commit_name=kwargs["committer_name"],
        commit_email=kwargs["committer_email"],
        author_name=kwargs.get("author_name", ""),
        author_email=kwargs.get("author_email", ""),
        target_branch=kwargs.get("target_branch", ""),
    )

    results = bot.run(
        patterns=["*.json"],
        pre_tasks=pre_tasks,
        commit_message=kwargs.get("commit_message", ""),
        pull_request_title=kwargs.get("pull_request_title", ""),
        dry_run=kwargs.get("dry_run", False),
    )

    logger.debug(f"complyscribe results: {results}")
