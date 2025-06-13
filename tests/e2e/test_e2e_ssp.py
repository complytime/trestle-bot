# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""
E2E tests for SSP creation and autosync workflow.

Notes that this should be the only E2E for auto-syncing since the UX is the same for each model.
The SSP model is used here as a stand-in for all models because it is the most complex process.

The tests here are based on the following workflow:
1. Create new SSP
2. Autosync SSP to create initial Markdown
3. Run autosync again to check that no changes are pushed
4. Update the profile with sync-upstreams
5. Autosync again to check that the changes are pushed
"""

import logging
import os
import pathlib
from typing import Dict, Tuple

import pytest
from git.repo import Repo
from trestle.common.model_utils import ModelUtils
from trestle.core.commands.author.ssp import SSPGenerate
from trestle.core.models.file_content_type import FileContentType
from trestle.oscal.ssp import SystemSecurityPlan

from complyscribe.const import ERROR_EXIT_CODE, SUCCESS_EXIT_CODE
from complyscribe.tasks.authored.ssp import SSPIndex
from tests.e2e.e2e_testutils import E2ETestRunner
from tests.testutils import clean, prepare_upstream_repo, setup_for_ssp


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

test_prof = "simplified_nist_profile"
test_comp_name = "test_comp"
test_ssp_md = "md_ssp"
test_ssp_name = "test_ssp"


@pytest.fixture
def valid_args_dict() -> Dict[str, str]:
    return {
        "branch": "test",
        "markdown-dir": test_ssp_md,
        "oscal-model": "ssp",
        "committer-name": "test",
        "committer-email": "test@email.com",
        "ssp-index-file": "ssp-index.json",
    }


def replace_line_in_file_after_tag(
    file_path: pathlib.Path, tag: str, new_line: str
) -> bool:
    """Replace the line after tag with new string."""
    with file_path.open("r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if tag in line:
            lines[i + 1] = new_line

            with file_path.open("w") as f:
                f.writelines(lines)
            return True
    return False


@pytest.mark.slow
def test_ssp_editing_e2e(
    tmp_repo: Tuple[str, Repo],
    e2e_runner: E2ETestRunner,
    valid_args_dict: Dict[str, str],
) -> None:
    """Test the complyscribe autosync command with SSPs."""
    tmp_repo_str, _ = tmp_repo
    tmp_repo_path = pathlib.Path(tmp_repo_str)

    ssp_md_path = pathlib.Path(test_ssp_md) / test_ssp_name
    _ = setup_for_ssp(tmp_repo_path, test_prof, [test_comp_name], str(ssp_md_path))

    # Get command arguments for the test
    branch = valid_args_dict["branch"]
    markdown_path = valid_args_dict["markdown-dir"]
    committer_name = valid_args_dict["committer-name"]
    committer_email = valid_args_dict["committer-email"]

    create_args: Dict[str, str] = {
        "markdown-dir": markdown_path,
        "branch": branch,
        "committer-name": committer_name,
        "committer-email": committer_email,
        "ssp-name": test_ssp_name,
        "profile-name": test_prof,
        "compdefs": test_comp_name,
    }
    create_command = e2e_runner.build_test_command(
        tmp_repo_str,
        "create ssp",
        create_args,
    )
    exit_code, _, _ = e2e_runner.invoke_command(create_command)
    assert exit_code == SUCCESS_EXIT_CODE
    assert (tmp_repo_path / markdown_path).exists()

    # Check that the correct files are present with the correct content
    ssp_path = ModelUtils.get_model_path_for_name_and_class(
        tmp_repo_path, test_ssp_name, SystemSecurityPlan, FileContentType.JSON
    )
    index_path = os.path.join(tmp_repo_str, "ssp-index.json")
    ssp_index = SSPIndex(index_path)
    assert ssp_index.get_profile_by_ssp(test_ssp_name) == test_prof
    assert ssp_index.get_comps_by_ssp(test_ssp_name) == [test_comp_name]
    assert ssp_index.get_leveraged_by_ssp(test_ssp_name) is None
    assert ssp_path.exists()

    # Make a change to the SSP
    ac_1_path = tmp_repo_path / ssp_md_path / "ac" / "ac-1.md"
    assert replace_line_in_file_after_tag(
        ac_1_path, "ac-1_prm_6:", "    values:\n    ssp-values:\n      - my ssp val\n"
    )

    autosync_command = e2e_runner.build_test_command(
        tmp_repo_str, "autosync", valid_args_dict
    )
    exit_code, response_stdout, _ = e2e_runner.invoke_command(autosync_command)
    assert exit_code == SUCCESS_EXIT_CODE
    # Check that the ssp was pushed to the remote
    assert f"Changes pushed to {branch} successfully." in response_stdout

    # Check that if run again, the ssp is not pushed again
    exit_code, response_stdout, _ = e2e_runner.invoke_command(autosync_command)
    assert exit_code == SUCCESS_EXIT_CODE
    assert "Nothing to commit" in response_stdout

    # Check that if the upstream profile is updated, the ssp is updated
    local_upstream_path = prepare_upstream_repo()
    upstream_repos_arg = f"{e2e_runner.UPSTREAM_REPO}@main"
    upstream_command_args = {
        "branch": branch,
        "committer-name": committer_name,
        "committer-email": committer_email,
        "sources": upstream_repos_arg,
    }
    sync_upstreams_command = e2e_runner.build_test_command(
        tmp_repo_str,
        "sync-upstreams",
        upstream_command_args,
        local_upstream_path,
    )
    exit_code, response_stdout, _ = e2e_runner.invoke_command(sync_upstreams_command)
    assert exit_code == SUCCESS_EXIT_CODE
    assert f"Changes pushed to {branch} successfully." in response_stdout

    # Autosync again to check that the ssp is updated
    exit_code, response_stdout, _ = e2e_runner.invoke_command(autosync_command)
    assert exit_code == SUCCESS_EXIT_CODE
    assert f"Changes pushed to {branch} successfully." in response_stdout

    # Clean up the upstream repo
    clean(local_upstream_path, None)


@pytest.mark.slow
def test_ssp_e2e_editing_failure(
    tmp_repo: Tuple[str, Repo],
    e2e_runner: E2ETestRunner,
    valid_args_dict: Dict[str, str],
) -> None:
    """
    Test the complyscribe autosync command with SSPs with failure.

    Notes: The test should fail because of the missing entry in the ssp-index.
    This simulates the use case if an SSP is created outside of the tool.
    """
    tmp_repo_str, _ = tmp_repo
    tmp_repo_path = pathlib.Path(tmp_repo_str)

    ssp_md_path = pathlib.Path(test_ssp_md) / test_ssp_name
    args = setup_for_ssp(tmp_repo_path, test_prof, [test_comp_name], str(ssp_md_path))

    ssp_generate = SSPGenerate()
    assert ssp_generate._run(args) == 0

    autosync_command = e2e_runner.build_test_command(
        tmp_repo_str, "autosync", valid_args_dict
    )
    exit_code, response_stdout, response_stderr = e2e_runner.invoke_command(
        autosync_command
    )
    assert exit_code == ERROR_EXIT_CODE
    err_msg = "SSP test_ssp does not exists in the index"
    assert err_msg in response_stdout or err_msg in response_stderr
