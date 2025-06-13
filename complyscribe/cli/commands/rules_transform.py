# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Module for rules-transform command"""

import logging
from typing import Any, List

import click

from complyscribe.cli.options.common import (
    common_options,
    git_options,
    handle_exceptions,
)
from complyscribe.cli.utils import comma_sep_to_list, run_bot
from complyscribe.const import RULES_VIEW_DIR
from complyscribe.tasks.authored.compdef import AuthoredComponentDefinition
from complyscribe.tasks.base_task import ModelFilter, TaskBase
from complyscribe.tasks.regenerate_task import RegenerateTask
from complyscribe.tasks.rule_transform_task import RuleTransformTask
from complyscribe.transformers.yaml_transformer import ToRulesYAMLTransformer


logger = logging.getLogger(__name__)


@click.command(
    name="rules-transform",
    help="Transform rules to an OSCAL Component Definition JSON file.",
)
@click.pass_context
@common_options
@git_options
@click.option(
    "--markdown-dir",
    type=str,
    help="Directory name to store markdown files.",
)
@click.option(
    "--rules-view-dir",
    type=str,
    help="Top-level rules-view directory.",
    default=RULES_VIEW_DIR,
)
@click.option(
    "--skip-items",
    type=str,
    help="Comma-separated list of glob patterns for directories to skip when running tasks.",
)
@handle_exceptions
def rules_transform_cmd(ctx: click.Context, **kwargs: Any) -> None:
    """Run the rule transform operation."""
    # Allow any model to be skipped by setting skip_item, by default include all
    model_filter: ModelFilter = ModelFilter(
        skip_patterns=comma_sep_to_list(kwargs.get("skip_items", "")),
        include_patterns=["*"],
    )

    transformer = ToRulesYAMLTransformer()
    rule_transform_task: RuleTransformTask = RuleTransformTask(
        working_dir=kwargs["repo_path"],
        rules_view_dir=kwargs["rules_view_dir"],
        rule_transformer=transformer,
        model_filter=model_filter,
    )
    regenerate_task: RegenerateTask = RegenerateTask(
        markdown_dir=kwargs["markdown_dir"],
        authored_object=AuthoredComponentDefinition(kwargs["repo_path"]),
        model_filter=model_filter,
    )

    pre_tasks: List[TaskBase] = [rule_transform_task, regenerate_task]
    kwargs["working_dir"] = str(kwargs["repo_path"].resolve())
    result = run_bot(pre_tasks, kwargs)
    logger.debug(f"Bot results: {result}")
    logger.info("Rule transform complete!")
