# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""E2E tests for commands for component definition authoring."""

import logging
import pathlib
from typing import Dict, List, Tuple

import pytest
from git.repo import Repo
from trestle.common.model_utils import ModelUtils
from trestle.core.models.file_content_type import FileContentType
from trestle.oscal.component import ComponentDefinition
from trestle.oscal.profile import Profile

from complyscribe.const import RULES_VIEW_DIR, SUCCESS_EXIT_CODE
from tests.e2e.e2e_testutils import E2ETestRunner
from tests.testutils import load_from_json, setup_for_profile, setup_rules_view


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

test_prof = "simplified_nist_profile"
test_filter_prof = "simplified_filter_profile"
test_comp_name = "test_comp"


@pytest.mark.slow
@pytest.mark.parametrize(
    "test_name, command_args",
    [
        (
            "success/happy path",
            {
                "branch": "test",
                "markdown-dir": "md_comp",
                "rules-view-dir": RULES_VIEW_DIR,
                "committer-name": "test",
                "committer-email": "test@email.com",
            },
        ),
        (
            "success/happy path with model skipping",
            {
                "branch": "test",
                "rules-view-dir": RULES_VIEW_DIR,
                "markdown-dir": "md_comp",
                "committer-name": "test",
                "committer-email": "test",
                "skip-items": test_comp_name,
            },
        ),
    ],
)
def test_rules_transform_e2e(
    tmp_repo: Tuple[str, Repo],
    e2e_runner: E2ETestRunner,
    test_name: str,
    command_args: Dict[str, str],
) -> None:
    """Test the complyscribe rules transform command."""
    logger.info(f"Running test: {test_name}")

    tmp_repo_str, _ = tmp_repo
    tmp_repo_path = pathlib.Path(tmp_repo_str)

    # Setup the rules directory
    setup_rules_view(tmp_repo_path, test_comp_name)

    command: List[str] = e2e_runner.build_test_command(
        tmp_repo_str, "rules-transform", command_args
    )
    exit_code, response_stdout, _ = e2e_runner.invoke_command(command)
    assert exit_code == SUCCESS_EXIT_CODE

    # Check that the component definition was created
    if "skip-items" in command_args:
        assert f"input: {test_comp_name}.csv" not in response_stdout
    else:
        comp_path: pathlib.Path = ModelUtils.get_model_path_for_name_and_class(
            tmp_repo_path, test_comp_name, ComponentDefinition, FileContentType.JSON
        )
        assert comp_path.exists()
        assert tmp_repo_path.joinpath("md_comp").exists()
        assert f"input: {test_comp_name}.csv" in response_stdout
    branch = command_args["branch"]
    assert f"Changes pushed to {branch} successfully." in response_stdout


@pytest.mark.slow
@pytest.mark.parametrize(
    "test_name, command_args",
    [
        (
            "success/happy path",
            {
                "profile-name": test_prof,
                "component-title": "test-comp",
                "compdef-name": "test-compdef",
                "component-description": "test",
                "markdown-dir": "markdown",
                "branch": "test",
                "committer-name": "test",
                "committer-email": "test@email.com",
            },
        ),
        (
            "success/happy path with filtering",
            {
                "profile-name": test_prof,
                "component-title": "test-comp",
                "compdef-name": "test-compdef",
                "component-description": "test",
                "markdown-dir": "markdown",
                "branch": "test",
                "committer-name": "test",
                "committer-email": "test@email.com",
                "filter-by-profile": test_filter_prof,
            },
        ),
    ],
)
def test_create_cd_e2e(
    tmp_repo: Tuple[str, Repo],
    e2e_runner: E2ETestRunner,
    test_name: str,
    command_args: Dict[str, str],
) -> None:
    """Test the complyscribe create compdef command."""
    logger.info(f"Running test: {test_name}")

    tmp_repo_str, _ = tmp_repo
    tmp_repo_path = pathlib.Path(tmp_repo_str)

    # Load profiles into the environment
    _ = setup_for_profile(tmp_repo_path, test_prof, "")
    load_from_json(tmp_repo_path, test_filter_prof, test_filter_prof, Profile)

    command = e2e_runner.build_test_command(
        tmp_repo_str, "create compdef", command_args
    )
    exit_code, _, _ = e2e_runner.invoke_command(command, tmp_repo_path)
    assert exit_code == SUCCESS_EXIT_CODE

    # Check that all expected files were created
    comp_path: pathlib.Path = ModelUtils.get_model_path_for_name_and_class(
        tmp_repo_path,
        command_args["compdef-name"],
        ComponentDefinition,
        FileContentType.JSON,
    )
    assert comp_path.exists()
    assert (tmp_repo_path / command_args["markdown-dir"]).exists()
    assert (
        tmp_repo_path
        / RULES_VIEW_DIR
        / command_args["compdef-name"]
        / command_args["component-title"]
    ).exists()
