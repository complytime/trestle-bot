# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Module for sync OSCAL models to cac content command"""
import logging
import pathlib
from typing import Any, List

import click

from complyscribe.cli.options.common import (
    common_options,
    git_options,
    handle_exceptions,
)
from complyscribe.cli.utils import run_bot
from complyscribe.tasks.base_task import TaskBase
from complyscribe.tasks.sync_oscal_content_catalog_task import SyncOscalCatalogTask
from complyscribe.tasks.sync_oscal_content_cd_task import SyncOscalCdTask
from complyscribe.tasks.sync_oscal_content_profile_task import SyncOscalProfileTask


logger = logging.getLogger(__name__)


@click.group(name="sync-oscal-content", help="Sync OSCAL models to cac content.")
@click.pass_context
@handle_exceptions
def sync_oscal_content_cmd(ctx: click.Context) -> None:
    """
    Command to sync OSCAL models to cac content
    """


@sync_oscal_content_cmd.command(
    name="component-definition",
    help="Sync OSCAL component definition to cac content.",
)
@click.pass_context
@common_options
@git_options
@click.option(
    "--cac-content-root",
    help="Root of the CaC content project.",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path
    ),
    required=True,
)
@click.option(
    "--product",
    type=str,
    help="Component title in OSCAL component definition that to find which component to sync",
    required=True,
)
@click.option(
    "--oscal-profile",
    type=str,
    help="Name of the profile in trestle workspace",
    required=True,
)
def sync_oscal_cd_to_cac_content_cmd(
    ctx: click.Context,
    cac_content_root: pathlib.Path,
    product: str,
    oscal_profile: str,
    **kwargs: Any,
) -> None:
    """Sync OSCAL component definition to cac content"""
    working_dir = kwargs["repo_path"]  # From common_options
    pre_tasks: List[TaskBase] = []
    sync_cac_content_task = SyncOscalCdTask(
        cac_content_root=cac_content_root,
        working_dir=working_dir,
        product=product,
        oscal_profile=oscal_profile,
    )
    pre_tasks.append(sync_cac_content_task)
    # change working_dir to CaC content repo, since this task changing
    # CaC content
    kwargs["repo_path"] = str(cac_content_root.resolve())
    result = run_bot(pre_tasks, kwargs)
    logger.debug(f"complyscribe results: {result}")


@sync_oscal_content_cmd.command(
    name="profile",
    help="Sync OSCAL profile information to cac content.",
)
@click.pass_context
@common_options
@git_options
@click.option(
    "--cac-content-root",
    help="Root of the CaC content project.",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path
    ),
    required=True,
)
@click.option(
    "--cac-policy-id",
    type=str,
    required=True,
    help="Policy id for source control file.",
)
@click.option(
    "--product",
    type=str,
    required=True,
    help="Product name for sync OSCAL Profile.",
)
def sync_oscal_profile_to_cac_content_cmd(
    ctx: click.Context,
    cac_content_root: pathlib.Path,
    cac_policy_id: str,
    product: str,
    **kwargs: Any,
) -> None:
    """Sync OSCAL profile to cac control file"""
    working_dir = kwargs["repo_path"]  # From common_options
    pre_tasks: List[TaskBase] = []
    sync_cac_content_task = SyncOscalProfileTask(
        cac_content_root=cac_content_root,
        working_dir=working_dir,
        cac_policy_id=cac_policy_id,
        product=product,
    )
    pre_tasks.append(sync_cac_content_task)
    # change working_dir to CaC content repo, since this task changing
    # CaC content
    kwargs["repo_path"] = str(cac_content_root.resolve())
    result = run_bot(pre_tasks, kwargs)
    logger.debug(f"complyscribe results: {result}")


@sync_oscal_content_cmd.command(
    name="catalog",
    help="Sync OSCAL catalog information to cac content.",
)
@click.pass_context
@common_options
@git_options
@click.option(
    "--cac-content-root",
    help="Root of the CaC content project.",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path
    ),
    required=True,
)
@click.option(
    "--cac-policy-id",
    type=str,
    required=True,
    help="Policy id for source control file.",
)
def sync_oscal_catalog_to_cac_content_cmd(
    ctx: click.Context,
    cac_content_root: pathlib.Path,
    cac_policy_id: str,
    **kwargs: Any,
) -> None:
    """Sync OSCAL catalog to CaC control file"""
    working_dir = kwargs["repo_path"]  # From common_options
    pre_tasks: List[TaskBase] = []
    sync_cac_content_task = SyncOscalCatalogTask(
        cac_content_root=cac_content_root,
        working_dir=working_dir,
        cac_policy_id=cac_policy_id,
    )
    pre_tasks.append(sync_cac_content_task)
    # change working_dir to CaC content repo, since this task changing
    # CaC content
    kwargs["repo_path"] = str(cac_content_root.resolve())
    result = run_bot(pre_tasks, kwargs)
    logger.debug(f"complyscribe results: {result}")
