# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Unit test for sync-cac-content command"""
import pathlib
from typing import Any, Generator, Tuple

from click import BaseCommand
from click.testing import CliRunner
from git import Repo
from ssg.controls import Policy
from trestle.common.const import REPLACE_ME
from trestle.oscal.catalog import Catalog, Control
from trestle.oscal.component import ComponentDefinition

from tests.testutils import TEST_DATA_DIR, setup_for_catalog, setup_for_profile
from trestlebot.cli.commands.sync_cac_content import (
    sync_cac_catalog_cmd,
    sync_cac_content_cmd,
    sync_cac_content_profile_cmd,
    sync_content_to_component_definition_cmd,
)


test_product = "rhel8"
# Note: data in test_content_dir is copied from content repo, PR:
# https://github.com/ComplianceAsCode/content/pull/12819
test_content_dir = TEST_DATA_DIR / "content_dir"
test_cac_profile = "example"
test_prof = "simplified_nist_profile"
test_cat = "simplified_nist_catalog"
test_comp_path = f"component-definitions/{test_product}/component-definition.json"
test_policy_id = "1234-levels"
test_level = "low"
tester_prof_path = f"profiles/{test_policy_id}-{test_level}/profiles.json"


def test_invalid_sync_cac_cmd() -> None:
    """Tests that sync-cac-content command fails if given invalid subcommand."""
    runner = CliRunner()
    result = runner.invoke(sync_cac_content_cmd, ["invalid"])

    assert "Error: No such command 'invalid'" in result.output
    assert result.exit_code == 2


def test_sync_catalog_create(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests sync CaC Profile to new OSCAL Catalog."""
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)
    setup_for_catalog(repo_path, test_cat, "catalog")
    test_cac_control = "abcd-levels"

    runner = CliRunner()
    assert isinstance(sync_cac_catalog_cmd, BaseCommand)
    result = runner.invoke(
        sync_cac_catalog_cmd,
        [
            "--cac-content-root",
            test_content_dir,
            "--repo-path",
            str(repo_path.resolve()),
            "--cac-policy-id",
            test_cac_control,
            "--oscal-catalog",
            test_cac_control,
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
    assert result.exit_code == 0, result.output

    # Source
    policy = Policy(test_content_dir / "controls" / f"{test_cac_control}.yml")
    policy.load()

    # Destination
    # catalog_path = repo_path.joinpath(test_catalog_path)
    catalog_path = repo_path / "catalogs/abcd-levels/catalog.json"
    assert catalog_path.exists(), f"Catalog {catalog_path} must exist"
    catalog_obj = Catalog.oscal_read(catalog_path)
    assert catalog_obj.metadata.title == f"Catalog for {test_cac_control}"
    assert catalog_obj.metadata.oscal_version.__root__ == "1.1.3"
    assert catalog_obj.metadata.version == "REPLACE_ME"
    # (No top-level controls, all are in groups)
    assert sum([len(g.controls) for g in catalog_obj.groups]) == len(policy.controls)


def test_sync_catalog_create_real(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests sync Cac content product name to OSCAL component title ."""
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)
    setup_for_catalog(repo_path, test_cat, "catalog")

    runner = CliRunner()
    assert isinstance(sync_cac_catalog_cmd, BaseCommand)
    ocp4_policy = "nist_ocp4"
    result = runner.invoke(
        sync_cac_catalog_cmd,
        [
            "--cac-content-root",
            test_content_dir,
            "--repo-path",
            str(repo_path.resolve()),
            "--cac-policy-id",
            ocp4_policy,
            "--oscal-catalog",
            ocp4_policy,
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
    assert result.exit_code == 0, result.output

    # Source
    policy = Policy(test_content_dir / "controls/simplified_nist_ocp4.yml")
    policy.load()

    # Destination
    # catalog_path = repo_path.joinpath(test_catalog_path)
    catalog_path = repo_path / f"catalogs/{ocp4_policy}/catalog.json"
    assert catalog_path.exists(), f"Catalog {catalog_path} must exist"
    catalog_obj = Catalog.oscal_read(catalog_path)

    assert catalog_obj.metadata.title == f"Catalog for {ocp4_policy}"
    assert catalog_obj.metadata.oscal_version.__root__ == "1.1.3"
    assert catalog_obj.metadata.version == "REPLACE_ME"

    # (No top-level controls, all are in groups)
    def flatten_nested_controls(controls: Any) -> Generator[Control, None, None]:
        for control in controls:
            if control.controls:
                yield from flatten_nested_controls(control.controls)
            if isinstance(control, Control):
                yield control

    assert sum(1 for _ in flatten_nested_controls(catalog_obj.groups)) == len(
        policy.controls
    ), "Unexpected control count. Do you have multiple policy files with the same policy id?"


def test_sync_catalog_update(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests sync CaC Profile to existing OSCAL Catalog."""
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)
    setup_for_catalog(repo_path, test_cat, "catalog")

    runner = CliRunner()
    assert isinstance(sync_cac_catalog_cmd, BaseCommand)
    test_cac_control = "nist_ocp4"
    result = runner.invoke(
        sync_cac_catalog_cmd,
        [
            "--cac-content-root",
            test_content_dir,
            "--repo-path",
            str(repo_path.resolve()),
            "--cac-policy-id",
            test_cac_control,
            "--oscal-catalog",
            test_cat,
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    merged_catalog = Catalog.oscal_read(
        repo_path / "catalogs" / test_cat / "catalog.json"
    )
    assert (
        merged_catalog.metadata.title
        == "Trestle simplified: NIST Special Publication 800-53 Revision 5: "
        "Security and Privacy Controls for Federal Information Systems and Organizations"
    )
    assert merged_catalog.metadata.oscal_version.__root__ == "1.0.0"
    assert merged_catalog.metadata.version == "5.0.1"
    assert merged_catalog.groups[2].id == "au"


def test_missing_required_option(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests missing required options in sync-cac-content command."""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    runner = CliRunner()
    result = runner.invoke(
        sync_content_to_component_definition_cmd,
        [
            "--product",
            test_product,
            "--repo-path",
            str(repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
        ],
    )
    assert result.exit_code == 2


def test_non_existent_product(tmp_repo: Tuple[str, Repo]) -> None:
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    runner = CliRunner()
    result = runner.invoke(
        sync_content_to_component_definition_cmd,
        [
            "--product",
            "non-exist",
            "--repo-path",
            str(repo_path.resolve()),
            "--cac-content-root",
            test_content_dir,
            "--cac-profile",
            "cac-profile",
            "--oscal-profile",
            test_prof,
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
        ],
    )
    assert result.exit_code == 1


def test_sync_product(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests sync Cac content product name to OSCAL component title ."""
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)
    setup_for_catalog(repo_path, test_cat, "catalog")
    setup_for_profile(repo_path, test_prof, "profile")

    runner = CliRunner()
    result = runner.invoke(
        sync_content_to_component_definition_cmd,
        [
            "--product",
            test_product,
            "--repo-path",
            str(repo_path.resolve()),
            "--cac-content-root",
            test_content_dir,
            "--cac-profile",
            test_cac_profile,
            "--oscal-profile",
            test_prof,
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
    assert result.exit_code == 0
    component_definition = repo_path.joinpath(test_comp_path)
    # Check if the component definition is created
    assert component_definition.exists()
    compdef = ComponentDefinition.oscal_read(component_definition)
    assert compdef.metadata.title == "Component definition for rhel8"
    assert len(compdef.components) == 1
    component = compdef.components[0]
    assert component.title == "rhel8"
    # Check rules component props are added
    assert len(component.props) == 24
    rule_ids = [p.value for p in component.props if p.name == "Rule_Id"]
    assert sorted(rule_ids) == [
        "configure_crypto_policy",
        "file_groupownership_sshd_private_key",
        "sshd_set_keepalive",
    ]
    # Check parameters props are added
    param_ids = [p.value for p in component.props if p.name == "Parameter_Id"]
    assert sorted(list(set(param_ids))) == [
        "var_sshd_set_keepalive",
        "var_system_crypto_policy",
    ]

    # Check control_implementations are attached
    ci = component.control_implementations[0]
    assert ci.source == "trestle://profiles/simplified_nist_profile/profile.json"

    assert len(ci.props) == 1
    assert ci.props[0].name == "Framework_Short_Name"
    assert ci.props[0].value == "example"

    set_parameters = ci.set_parameters
    assert len(set_parameters) == 2
    set_params_ids = []
    set_params_dict = {}
    for param in set_parameters:
        set_params_ids.append(param.param_id)
        set_params_dict.update({param.param_id: param.values})
    assert sorted(set_params_ids) == [
        "var_sshd_set_keepalive",
        "var_system_crypto_policy",
    ]
    assert set_params_dict["var_sshd_set_keepalive"] == ["1"]
    assert set_params_dict["var_system_crypto_policy"] == ["fips"]

    # Check implemented requirements are populated
    for implemented_req in ci.implemented_requirements:
        if implemented_req.control_id == "ac-1":
            for prop in implemented_req.props:
                assert prop.value == "implemented"
                # Check mapping OscalStatus.IMPLEMENTED:CacStatus.AUTOMATED
                if prop.name == "implementation-status":
                    assert prop.value == "implemented"
            assert len(implemented_req.statements) == 2
            assert (
                implemented_req.statements[0].description
                == "AC-1(a) is an organizational control outside "
                "the scope of OpenShift configuration."
            )
            assert (
                implemented_req.statements[1].description
                == "AC-1(b) is an organizational control outside "
                "the scope of OpenShift configuration."
            )

        if implemented_req.control_id == "ac-2":
            for prop in implemented_req.props:
                assert prop.value == "alternative"
                # Check mapping OscalStatus.ALTERNATIVE:CacStatus.MANUAL
                if prop.name == "implementation-status":
                    assert prop.value == "alternative"
                    assert prop.remarks == REPLACE_ME


def test_sync_product_create_validation_component(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests sync Cac content to create validation component."""
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)
    setup_for_catalog(repo_path, test_cat, "catalog")
    setup_for_profile(repo_path, test_prof, "profile")

    runner = CliRunner()
    result = runner.invoke(
        sync_content_to_component_definition_cmd,
        [
            "--product",
            test_product,
            "--repo-path",
            str(repo_path.resolve()),
            "--cac-content-root",
            test_content_dir,
            "--cac-profile",
            test_cac_profile,
            "--oscal-profile",
            test_prof,
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
            "--component-definition-type",
            "validation",
        ],
    )
    # Check the CLI sync-cac-content is successful
    component_definition = repo_path.joinpath(test_comp_path)
    assert result.exit_code == 0

    # Check if the component definition is created
    assert component_definition.exists()
    compdef = ComponentDefinition.oscal_read(component_definition)
    component = compdef.components[0]
    assert len(component.props) == 30
    assert component.title == "openscap"
    assert component.type == "validation"


def test_missing_required_profile_option(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests missing required option in sync-cac-content-profile command."""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    setup_for_catalog(repo_path, test_cat, "catalog")

    runner = CliRunner()
    result = runner.invoke(
        sync_cac_content_profile_cmd,
        [
            "--cac-content-root",
            str(test_content_dir),
            "--product",
            test_product,
            "--oscal-catalog",
            test_cat,
            "--repo-path",
            str(repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
        ],
    )
    assert result.exit_code == 2


def test_profile_supplied(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests sync Cac profile content to create OSCAL Profile."""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    setup_for_catalog(repo_path, test_cat, "catalog")

    runner = CliRunner()
    result = runner.invoke(
        sync_cac_content_profile_cmd,
        [
            "--repo-path",
            str(repo_path.resolve()),
            "--cac-content-root",
            str(test_content_dir),
            "--product",
            test_product,
            "--oscal-catalog",
            test_cat,
            "--cac-policy-id",
            test_policy_id,
            "--filter-by-level",
            "medium",
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0


def test_created_oscal_profile(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests creation of OSCAL profile in correct path."""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    setup_for_catalog(repo_path, test_cat, "catalog")
    test_prof_path = f"profiles/{test_policy_id}-{test_level}/profile.json"

    runner = CliRunner()
    result = runner.invoke(
        sync_cac_content_profile_cmd,
        [
            "--cac-content-root",
            str(test_content_dir),
            "--product",
            test_product,
            "--oscal-catalog",
            test_cat,
            "--cac-policy-id",
            test_policy_id,
            "--filter-by-level",
            test_level,
            "--repo-path",
            str(repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )
    # Checking if CLI input created an OSCAL Profile
    # Asserting profile exists within the correct test profile path
    # Profile should populate in profiles/{cac-policy-id}-{filter-by-level}/profile.json
    assert result.exit_code == 0
    profile = repo_path.joinpath(test_prof_path)
    assert profile.exists()


def test_sync_missing_profile_option(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests sync Cac content profile command missing required option."""
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    runner = CliRunner()
    result = runner.invoke(
        sync_cac_content_profile_cmd,
        [
            "product",
            test_product,
            "--oscal-catalog",
            test_cat,
            "--cac-policy-id",
            test_policy_id,
            "--filter-by-level",
            "all",
            "--repo-path",
            str(repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )
    # Check the CLI sync-cac-content-profile fails due to missing profile option
    assert result.exit_code == 2
