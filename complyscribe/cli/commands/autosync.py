# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Autosync command"""

import logging
import sys
import traceback
from typing import Any, List

import click

from complyscribe.cli.options.common import common_options, git_options
from complyscribe.cli.utils import comma_sep_to_list, run_bot
from complyscribe.const import ERROR_EXIT_CODE
from complyscribe.tasks.assemble_task import AssembleTask
from complyscribe.tasks.authored import types
from complyscribe.tasks.authored.base_authored import AuthoredObjectBase
from complyscribe.tasks.base_task import ModelFilter, TaskBase
from complyscribe.tasks.regenerate_task import RegenerateTask


logger = logging.getLogger(__name__)


@click.command("autosync", help="Autosync catalog, profile, compdef and ssp.")
@click.pass_context
@common_options
@git_options
@click.option(
    "--oscal-model",
    type=click.Choice(choices=[model.value for model in types.AuthoredType]),
    help="OSCAL model type for autosync.",
    required=True,
)
@click.option(
    "--markdown-dir",
    type=str,
    help="Directory containing markdown files.",
    required=True,
)
@click.option(
    "--skip-items",
    type=str,
    help="Comma-separated list of glob patterns of the chosen model type \
        to skip when running tasks.",
)
@click.option(
    "--skip-assemble",
    help="Skip assembly task.",
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--skip-regenerate",
    help="Skip regenerate task.",
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--version",
    help="Version of the OSCAL model to set during assembly into JSON.",
    type=str,
)
@click.option(
    "--ssp-index-file",
    help="Path to ssp index file. Required if --oscal-model is 'ssp'.",
    type=str,
    required=False,
)
def autosync_cmd(ctx: click.Context, **kwargs: Any) -> None:
    """Command to autosync catalog, profile, compdef and ssp."""

    oscal_model = kwargs["oscal_model"]
    markdown_dir = kwargs["markdown_dir"]
    working_dir = str(kwargs["repo_path"].resolve())
    kwargs["working_dir"] = working_dir

    if oscal_model == "ssp" and not kwargs.get("ssp_index_file"):
        logger.error("complyscribe error: missing option '--ssp-index-file'.")
        sys.exit(ERROR_EXIT_CODE)

    pre_tasks: List[TaskBase] = []

    if kwargs.get("file_pattern"):
        kwargs.update({"patterns": comma_sep_to_list(kwargs["file_patterns"])})

    try:
        model_filter: ModelFilter = ModelFilter(
            skip_patterns=comma_sep_to_list(kwargs.get("skip_items", "")),
            include_patterns=["*"],
        )
        authored_object: AuthoredObjectBase = types.get_authored_object(
            oscal_model,
            working_dir,
            kwargs.get("ssp_index_file", ""),
        )

        # Assuming an edit has occurred assemble would be run before regenerate.
        if not kwargs.get("skip_assemble"):
            assemble_task: AssembleTask = AssembleTask(
                authored_object=authored_object,
                markdown_dir=markdown_dir,
                version=kwargs.get("version", ""),
                model_filter=model_filter,
            )
            pre_tasks.append(assemble_task)
        else:
            logger.info("Assemble task skipped.")

        if not kwargs.get("skip_regenerate"):
            regenerate_task: RegenerateTask = RegenerateTask(
                authored_object=authored_object,
                markdown_dir=markdown_dir,
                model_filter=model_filter,
            )
            pre_tasks.append(regenerate_task)
        else:
            logger.info("Regeneration task skipped.")

        results = run_bot(pre_tasks, kwargs)
        logger.debug(f"complyscribe results: {results}")
    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"complyscribe error: {str(e)}")
        logger.debug(traceback_str)
        sys.exit(ERROR_EXIT_CODE)
