# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""
Module for create-cd create-ssp command for CLI
"""

import logging
from typing import Any, List

import click

from trestlebot import const
from trestlebot.cli.options.common import common_options, git_options, handle_exceptions
from trestlebot.cli.options.create import common_create_options
from trestlebot.cli.utils import comma_sep_to_list, run_bot
from trestlebot.tasks.assemble_task import AssembleTask
from trestlebot.tasks.authored.compdef import (
    AuthoredComponentDefinition,
    FilterByProfile,
)
from trestlebot.tasks.authored.ssp import AuthoredSSP, SSPIndex
from trestlebot.tasks.base_task import ModelFilter, TaskBase
from trestlebot.tasks.regenerate_task import RegenerateTask
from trestlebot.tasks.rule_transform_task import RuleTransformTask
from trestlebot.transformers.yaml_transformer import ToRulesYAMLTransformer


logger = logging.getLogger(__name__)


@click.group(name="create", help="Component definition and ssp authoring.")
@click.pass_context
@handle_exceptions
def create_cmd(ctx: click.Context) -> None:
    """
    Command leveraged for component definition and ssp authoring in trestlebot.
    """
    pass


@create_cmd.command(name="compdef", help="Component definition authoring subcommand.")
@click.pass_context
@common_create_options
@common_options
@git_options
@click.option(
    "--compdef-name",
    required=True,
    help="Name of component definition.",
)
@click.option(
    "--component-title",
    required=True,
    help="Title of initial component.",
)
@click.option(
    "--component-description",
    required=True,
    help="Description of initial component.",
)
@click.option(
    "--filter-by-profile",
    required=False,
    type=str,
    help="Optionally filter the controls in the component definition by a profile",
)
@click.option(
    "--component-definition-type",
    required=False,
    type=str,
    default="service",
    help="Type of component definition",
)
@handle_exceptions
def compdef_cmd(
    ctx: click.Context,
    **kwargs: Any,
) -> None:
    """
    Component definition authoring command.
    """
    pre_tasks: List[TaskBase] = []

    profile_name = kwargs["profile_name"]
    compdef_name = kwargs["compdef_name"]
    component_title = kwargs["component_title"]
    component_description = kwargs["component_description"]
    filter_by_profile = kwargs.get("filter_by_profile")
    component_definition_type = kwargs.get("component_definition_type", "service")
    repo_path = kwargs["repo_path"]
    markdown_dir = kwargs["markdown_dir"]
    if filter_by_profile:
        filter_by_profile = FilterByProfile(repo_path, filter_by_profile)

    authored_comp: AuthoredComponentDefinition = AuthoredComponentDefinition(
        trestle_root=repo_path,
    )
    authored_comp.create_new_default(
        profile_name=profile_name,
        compdef_name=compdef_name,
        comp_title=component_title,
        comp_description=component_description,
        comp_type=component_definition_type,
        filter_by_profile=filter_by_profile,
    )
    logger.info(f"Component definition name is: {component_title}.")

    transformer: ToRulesYAMLTransformer = ToRulesYAMLTransformer()

    model_filter: ModelFilter = ModelFilter(
        [], [compdef_name, component_title, f"{const.RULE_PREFIX}*"]
    )

    rule_transform_task: RuleTransformTask = RuleTransformTask(
        working_dir=repo_path,
        rules_view_dir=const.RULES_VIEW_DIR,
        rule_transformer=transformer,
        model_filter=model_filter,
    )
    logger.info(
        f"Profile to filter controls in the component files is: {filter_by_profile}."
    )
    logger.debug(
        f"Oscal profile in use with the component definition is: {profile_name}."
    )
    logger.debug(f"Component definition type is {component_definition_type}.")

    pre_tasks.append(rule_transform_task)

    regenerate_task: RegenerateTask = RegenerateTask(
        authored_object=authored_comp,
        markdown_dir=markdown_dir,
        model_filter=model_filter,
    )
    pre_tasks.append(regenerate_task)

    run_bot(pre_tasks, kwargs)

    logger.debug(f"You have successfully authored the {compdef_name}.")


@create_cmd.command(name="ssp", help="Authoring ssp subcommand.")
@click.pass_context
@common_create_options
@common_options
@git_options
@click.option(
    "--ssp-name",
    required=True,
    type=str,
    help="Name of SSP to create.",
)
@click.option(
    "--leveraged-ssp",
    required=False,
    type=str,
    help="Provider SSP to leverage for the new SSP.",
)
@click.option(
    "--ssp-index-file",
    required=False,
    type=str,
    default="ssp-index.json",
    help="Optionally set the path to the SSP index file.",
)
@click.option(
    "--yaml-header-path",
    required=False,
    type=str,
    help="Optionally set a path to a YAML file for custom SSP Markdown YAML headers.",
)
@click.option(
    "--version",
    required=False,
    type=str,
    help="Optionally set the version of the SSP.",
)
@click.option(
    "--compdefs",
    required=True,
    type=str,
    help="Comma separated list of component definitions.",
)
@handle_exceptions
def ssp_cmd(
    ctx: click.Context,
    **kwargs: Any,
) -> None:
    """
    SSP Authoring command
    """
    profile_name = kwargs["profile_name"]
    ssp_name = kwargs["ssp_name"]
    ssp_index_file = kwargs.get("ssp_index_file", "ssp-index.json")
    repo_path = kwargs["repo_path"]
    markdown_dir = kwargs["markdown_dir"]
    compdefs = kwargs["compdefs"]
    version = kwargs["version"]

    ssp_index: SSPIndex = SSPIndex(index_path=ssp_index_file)
    authored_ssp: AuthoredSSP = AuthoredSSP(trestle_root=repo_path, ssp_index=ssp_index)

    logger.info(f"SSP index file is: {ssp_index_file}.")

    comps: List[str] = comma_sep_to_list(compdefs)
    authored_ssp.create_new_default(
        ssp_name=ssp_name,
        profile_name=profile_name,
        compdefs=comps,
        markdown_path=markdown_dir,
        leveraged_ssp=kwargs["leveraged_ssp"],
        yaml_header=kwargs["yaml_header_path"],
    )

    logger.debug(f"The name of the SSP to create is {ssp_name}.")
    logger.debug(f"Oscal profile in use with the SSP is: {profile_name}.")

    # The starting point for SSPs is the markdown, so assemble into JSON.
    model_filter: ModelFilter = ModelFilter([], [ssp_name])
    assemble_task: AssembleTask = AssembleTask(
        authored_object=authored_ssp,
        markdown_dir=markdown_dir,
        version=version,
        model_filter=model_filter,
    )

    pre_tasks: List[TaskBase] = [assemble_task]

    run_bot(pre_tasks, kwargs)

    logger.debug(f"You have successfully authored the {ssp_name}.")
