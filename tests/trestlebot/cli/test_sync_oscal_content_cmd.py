# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Unit test for sync-cac-content command"""
import json
import os.path
import pathlib
from typing import Tuple

from click.testing import CliRunner
from git import Repo
from ruamel.yaml import YAML

from tests.testutils import (
    TEST_DATA_DIR,
    setup_for_cac_content_dir,
    setup_for_compdef,
    setup_for_profile,
)
from trestlebot.cli.commands.sync_oscal_content import (
    sync_oscal_cd_to_cac_content_cmd,
    sync_oscal_content_cmd,
    sync_oscal_profile_to_cac_content_cmd,
)
from trestlebot.const import INVALID_ARGS_EXIT_CODE, SUCCESS_EXIT_CODE
from trestlebot.utils import get_comments_from_yaml_data, to_literal_scalar_string


test_product = "rhel8"
# Note: data in test_content_dir is copied from content repo, PR:
# https://github.com/ComplianceAsCode/content/pull/12819
test_content_dir = TEST_DATA_DIR / "content_dir"
test_policy_id = "abcd-levels"
test_profile_name = "simplified_nist_profile"


def test_invalid_sync_oscal_cmd() -> None:
    """Tests that sync-oscal-content command fails if given invalid subcommand."""
    runner = CliRunner()
    result = runner.invoke(sync_oscal_content_cmd, ["invalid"])

    assert "Error: No such command 'invalid'" in result.output
    assert result.exit_code == INVALID_ARGS_EXIT_CODE


def test_sync_oscal_cd_to_cac_control(
    tmp_repo: Tuple[str, Repo], tmp_init_dir: str
) -> None:
    """Tests sync OSCAL component definition information to cac content."""
    repo_dir, _ = tmp_repo
    trestle_repo_path = pathlib.Path(repo_dir)
    setup_for_compdef(
        trestle_repo_path,
        test_product,
        test_product,
        model_name=os.path.join(test_product, test_profile_name),
    )
    tmp_content_dir = tmp_init_dir
    setup_for_cac_content_dir(tmp_content_dir, test_content_dir)

    runner = CliRunner()
    result = runner.invoke(
        sync_oscal_cd_to_cac_content_cmd,
        [
            "--product",
            test_product,
            "--oscal-profile",
            test_profile_name,
            "--cac-content-root",
            tmp_content_dir,
            "--repo-path",
            str(trestle_repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )

    # Check the CLI sync-cac-content is successful
    assert result.exit_code == SUCCESS_EXIT_CODE, result.output

    yaml = YAML()

    # check profile
    profile_path = pathlib.Path(
        os.path.join(tmp_content_dir, "products/rhel8/profiles/example.profile")
    )

    profile_data = yaml.load(profile_path)
    selections_field = profile_data["selections"]
    assert "abcd-levels:all:medium" in selections_field
    assert "file_groupownership_sshd_private_key" not in selections_field
    assert "sshd_set_keepalive" in selections_field
    assert "var_password_pam_minlen=15" in selections_field
    assert "var_sshd_set_keepalive=1" not in selections_field
    assert "no-exist-param=fips" not in selections_field

    # check control file
    control_file_path = pathlib.Path(
        os.path.join(tmp_content_dir, "controls", "abcd-levels.yml")
    )
    control_file_data = yaml.load(control_file_path)
    for control in control_file_data["controls"]:
        if control["id"] == "AC-1":
            # get comment, check if missing rule comment exists
            exist_comments = get_comments_from_yaml_data(control)
            assert len(exist_comments) == 1
            comment = "TODO: Need to implement rule not_exist_rule_id"
            assert len([True for c in exist_comments if comment in c]) == 1
            rules = control.get("rules", [])
            assert "file_groupownership_sshd_private_key" not in rules
            assert "var_system_crypto_policy=not-exist-option" in rules
            assert "var_sshd_set_keepalive=1" not in rules
            assert "not_exist_rule_id" not in rules
            assert "configure_crypto_policy" in rules
            assert control["status"] == "not applicable"

            # check notes
            notes = control["notes"]
            assert (
                "Section a: AC-1(a) is an organizational control outside the "
                "scope of OpenShift configuration." in notes
            )
            assert (
                "Section b: AC-1(b) is an organizational control outside the "
                "scope of OpenShift configuration." in notes
            )
            assert (
                "Section c: AC-1(c) is an organizational control outside the "
                "scope of OpenShift configuration." in notes
            )
        elif control["id"] == "AC-2":
            rules = control.get("rules", [])
            assert rules == []
            assert control["status"] == "manual"
            exist_comments = get_comments_from_yaml_data(control)
            comment = (
                "The status should be updated to one of "
                "['inherently met', 'documentation', 'automated', 'supported']"
            )
            assert len([True for c in exist_comments if comment in c]) == 1
            # check notes
            assert not control.get("notes")

    # check var file
    var_file_path = pathlib.Path(
        os.path.join(
            tmp_content_dir, "linux_os/guide/test/var_system_crypto_policy.var"
        )
    )
    var_file_data = yaml.load(var_file_path)
    options = var_file_data["options"]
    assert "not-exist-option" in options
    assert options["not-exist-option"] == "not-exist-option"


def test_sync_oscal_cd_statements(
    tmp_repo: Tuple[str, Repo], tmp_init_dir: str
) -> None:
    """Tests sync OSCAL component definition information to cac content."""
    repo_dir, _ = tmp_repo
    trestle_repo_path = pathlib.Path(repo_dir)
    setup_for_compdef(
        trestle_repo_path,
        test_product,
        test_product,
        model_name=os.path.join(test_product, test_profile_name),
    )
    tmp_content_dir = tmp_init_dir
    setup_for_cac_content_dir(tmp_content_dir, test_content_dir)
    # modify control file for statement sync testing
    control_file = pathlib.Path(
        os.path.join(tmp_content_dir, "controls", "abcd-levels.yml")
    )
    yaml = YAML()
    data = yaml.load(control_file)

    for control in data["controls"]:
        if control["id"] == "AC-1":
            control["notes"] = to_literal_scalar_string(
                "OpenShift does not have the capability to create\n"
                "guest/anonymous accounts or temporary accounts.\n"
            )
        if control["id"] == "AC-2":
            control["notes"] = ""

    yaml.dump(data, control_file)
    runner = CliRunner()
    result = runner.invoke(
        sync_oscal_cd_to_cac_content_cmd,
        [
            "--product",
            test_product,
            "--oscal-profile",
            test_profile_name,
            "--cac-content-root",
            tmp_content_dir,
            "--repo-path",
            str(trestle_repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )

    # Check the CLI sync-cac-content is successful
    assert result.exit_code == SUCCESS_EXIT_CODE, result.output

    yaml = YAML()

    # check control file
    control_file_path = pathlib.Path(
        os.path.join(tmp_content_dir, "controls", "abcd-levels.yml")
    )
    control_file_data = yaml.load(control_file_path)
    for control in control_file_data["controls"]:
        if control["id"] == "AC-1":
            # check notes
            notes = control["notes"]
            assert (
                "Section a: AC-1(a) is an organizational control outside the "
                "scope of OpenShift configuration." in notes
            )
            assert (
                "Section b: AC-1(b) is an organizational control outside the "
                "scope of OpenShift configuration." in notes
            )
            assert (
                "Section c: AC-1(c) is an organizational control outside the "
                "scope of OpenShift configuration." in notes
            )
            assert (
                "OpenShift does not have the capability to create\n"
                "guest/anonymous accounts or temporary accounts.\n" in notes
            )
        elif control["id"] == "AC-2":
            # check notes
            assert not control.get("notes")


def test_sync_oscal_profile_levels_low_to_high(
    tmp_repo: Tuple[str, Repo], tmp_init_dir: str
) -> None:
    """
    Tests sync OSCAL profile levels to cac content Control file,
     levels change from low to high.
    """
    repo_dir, _ = tmp_repo
    trestle_repo_path = pathlib.Path(repo_dir)
    setup_for_profile(trestle_repo_path, "rhel8-abcd-levels-low", "profile")
    setup_for_profile(trestle_repo_path, "rhel8-abcd-levels-medium", "profile")
    setup_for_profile(trestle_repo_path, "rhel8-abcd-levels-high", "profile")

    tmp_content_dir = tmp_init_dir
    setup_for_cac_content_dir(tmp_content_dir, test_content_dir)

    runner = CliRunner()
    result = runner.invoke(
        sync_oscal_profile_to_cac_content_cmd,
        [
            "--cac-policy-id",
            test_policy_id,
            "--product",
            test_product,
            "--cac-content-root",
            tmp_content_dir,
            "--repo-path",
            str(trestle_repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )

    assert result.exit_code == SUCCESS_EXIT_CODE, result.output

    # check level change
    yaml = YAML()
    control_file_path = pathlib.Path(
        os.path.join(tmp_content_dir, "controls", "abcd-levels.yml")
    )
    control_file_data = yaml.load(control_file_path)
    for control in control_file_data["controls"]:
        if control["id"] == "AC-1":
            levels = control["levels"]
            assert levels == ["high"]
        elif control["id"] == "AC-2":
            levels = control["levels"]
            assert levels == ["high"]


def test_sync_oscal_profile_levels_high_to_low(
    tmp_repo: Tuple[str, Repo], tmp_init_dir: str
) -> None:
    """
    Tests sync OSCAL profile levels to cac content Control file,
     levels change from high to low.
    """
    repo_dir, _ = tmp_repo
    trestle_repo_path = pathlib.Path(repo_dir)

    args = setup_for_profile(trestle_repo_path, "rhel8-abcd-levels-low", "profile")
    # change low level profile for test
    with open(args.profile_path) as f:
        profile_data = json.load(f)

    with open(args.profile_path, "w") as f:
        profile_data["profile"]["imports"][0]["include-controls"][0]["with-ids"] = [
            "ac-1"
        ]
        json.dump(profile_data, f, indent=2)

    args = setup_for_profile(trestle_repo_path, "rhel8-abcd-levels-medium", "profile")
    # change medium level profile for test
    with open(args.profile_path) as f:
        profile_data = json.load(f)

    with open(args.profile_path, "w") as f:
        profile_data["profile"]["imports"][0]["include-controls"][0]["with-ids"] = [
            "ac-1",
            "ac-2",
        ]
        json.dump(profile_data, f, indent=2)
    setup_for_profile(trestle_repo_path, "rhel8-abcd-levels-high", "profile")

    tmp_content_dir = tmp_init_dir
    setup_for_cac_content_dir(tmp_content_dir, test_content_dir)
    yaml = YAML()
    # change control file for test
    control_file_path = pathlib.Path(
        os.path.join(tmp_content_dir, "controls", "abcd-levels.yml")
    )
    control_file_data = yaml.load(control_file_path)
    for control in control_file_data["controls"]:
        if control["id"] == "AC-1":
            control["levels"] = ["high"]
        elif control["id"] == "AC-2":
            control["levels"] = ["high"]
    yaml.dump(control_file_data, control_file_path)

    runner = CliRunner()
    result = runner.invoke(
        sync_oscal_profile_to_cac_content_cmd,
        [
            "--cac-policy-id",
            test_policy_id,
            "--product",
            test_product,
            "--cac-content-root",
            tmp_content_dir,
            "--repo-path",
            str(trestle_repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )

    assert result.exit_code == SUCCESS_EXIT_CODE, result.output

    # check level change
    control_file_data = yaml.load(control_file_path)
    for control in control_file_data["controls"]:
        if control["id"] == "AC-1":
            levels = control["levels"]
            assert levels == ["low"]
        elif control["id"] == "AC-2":
            levels = control["levels"]
            assert levels == ["medium"]
