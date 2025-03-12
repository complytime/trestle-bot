# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Red Hat, Inc.

"""
Integration tests for validating that trestle-bot output is consumable by complytime
"""
import json
import logging
import os
import pathlib
import subprocess
import sys
from typing import Generator, Tuple, TypeVar

import pytest
from click import BaseCommand
from click.testing import CliRunner, Result
from git import Repo

from tests.testutils import TEST_DATA_DIR, setup_for_catalog, setup_for_profile
from trestlebot.cli.commands.sync_cac_content import (
    sync_cac_catalog_cmd,
    sync_content_to_component_definition_cmd,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

test_content_dir = TEST_DATA_DIR / "content_dir"

T = TypeVar("T")
YieldFixture = Generator[T, None, None]

_TEST_PREFIX = "trestlebot_tests"


@pytest.mark.slow
def test_complytime_setup() -> None:
    """Ensure that the complytime integration test setup works"""
    result = subprocess.run(
        ["complytime", "list", "--plain"],
        # cwd=complytime_home,
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"Title" in result.stdout
    assert b"Framework ID" in result.stdout


# @pytest.mark.slow
def test_full_sync(tmp_repo: Tuple[str, Repo], complytime_home: pathlib.Path) -> None:
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)
    setup_for_catalog(repo_path, "simplified_nist_catalog", "catalog")
    test_cac_control = "abcd-levels"

    runner = CliRunner()
    assert isinstance(sync_cac_catalog_cmd, BaseCommand)
    result: Result = runner.invoke(
        sync_cac_catalog_cmd,
        [
            "--cac-content-root",
            test_content_dir,
            "--repo-path",
            str(repo_path.resolve()),
            "--policy-id",
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

    test_product = "rhel8"
    test_cac_profile = test_content_dir / "products/rhel8/profiles/example.profile"
    test_prof = "simplified_nist_profile"
    test_comp_path = f"component-definitions/{test_product}/component-definition.json"
    test_cat = "simplified_nist_catalog"
    assert isinstance(sync_content_to_component_definition_cmd, BaseCommand)
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
            str(test_content_dir),
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

    # Fix trestle:// to file://

    new_cat_json_text = (
        pathlib.Path(repo_dir) / "catalogs/simplified_nist_catalog/catalog.json"
    ).read_text()
    new_cat_json_text = new_cat_json_text.replace(
        "trestle://catalogs/simplified_nist_catalog/catalog.json",
        "file://controls/catalog.json",
    )
    new_cat_json = json.loads(new_cat_json_text)

    new_prof_json_text = (
        pathlib.Path(repo_dir) / "profiles/simplified_nist_profile/profile.json"
    ).read_text()
    new_prof_json_text = new_prof_json_text.replace(
        "trestle://catalogs/simplified_nist_catalog/catalog.json",
        "file://controls/catalog.json",
    )
    new_prof_json_text = new_prof_json_text.replace(
        '"param_id"', '"param-id"'
    )  # TODO compliance-trestle uses param_id and param-id interchangably, complytime requires param-id
    new_prof_json = json.loads(new_prof_json_text)

    new_cd_json_text = component_definition.read_text()
    new_cd_json_text = new_cd_json_text.replace(
        "trestle://profiles/simplified_nist_profile/profile.json",
        "file://controls/profile.json",
    )
    new_cd_json = json.loads(new_cd_json_text)

    with open(
        (complytime_home / ".config/complytime/controls/catalog.json"), "w"
    ) as file:
        json.dump(new_cat_json, file)
    with open(
        (complytime_home / ".config/complytime/controls/profile.json"), "w"
    ) as file:
        json.dump(new_prof_json, file)
    with open(
        (complytime_home / ".config/complytime/bundles/component-definition.json"), "w"
    ) as file:
        json.dump(new_cd_json, file)

    # shutil.copy(component_definition, complytime_home / '.config/complytime/bundles/')
    # shutil.copy(pathlib.Path(repo_dir) / 'catalogs/simplified_nist_catalog/catalog.json',
    #   complytime_home / '.config/complytime/bundles/')
    # shutil.copy(pathlib.Path(repo_dir) / 'profiles/simplified_nist_profile/profile.json',
    #   complytime_home / '.config/complytime/controls/')

    result = subprocess.run(
        ["complytime", "list", "--plain"],
        # cwd=complytime_home,
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"Title" in result.stdout
    assert b"Framework ID" in result.stdout


@pytest.mark.slow
def test_compdef_type_software_sync(
    tmp_repo: Tuple[str, Repo], complytime_home: pathlib.Path
) -> None:
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)
    setup_for_catalog(repo_path, "simplified_nist_catalog", "catalog")
    test_cac_control = "abcd-levels"

    runner = CliRunner()
    assert isinstance(sync_cac_catalog_cmd, BaseCommand)
    result = runner.invoke(
        sync_cac_catalog_cmd,
        [
            "--cac-content-root",
            str(test_content_dir),
            "--repo-path",
            str(repo_path.resolve()),
            "--policy-id",
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

    test_product = "rhel8"
    test_cac_profile = test_content_dir / "products/rhel8/profiles/example.profile"
    test_prof = "simplified_nist_profile"
    test_comp_path = f"component-definitions/{test_product}/component-definition.json"
    test_cat = "simplified_nist_catalog"
    assert isinstance(sync_content_to_component_definition_cmd, BaseCommand)
    setup_for_catalog(repo_path, test_cat, "catalog")
    setup_for_profile(repo_path, test_prof, "profile")

    compdef_type = "software"

    runner = CliRunner()
    result = runner.invoke(
        sync_content_to_component_definition_cmd,
        [
            "--product",
            test_product,
            "--repo-path",
            str(repo_path.resolve()),
            "--cac-content-root",
            str(test_content_dir),
            "--cac-profile",
            test_cac_profile,
            "--oscal-profile",
            test_prof,
            "--component-definition-type",
            compdef_type,
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

    # Fix trestle:// to file://

    new_cat_json_text = (
        pathlib.Path(repo_dir) / "catalogs/simplified_nist_catalog/catalog.json"
    ).read_text()
    new_cat_json_text = new_cat_json_text.replace(
        "trestle://catalogs/simplified_nist_catalog/catalog.json",
        "file://controls/catalog.json",
    )
    new_cat_json = json.loads(new_cat_json_text)

    new_prof_json_text = (
        pathlib.Path(repo_dir) / "profiles/simplified_nist_profile/profile.json"
    ).read_text()
    new_prof_json_text = new_prof_json_text.replace(
        "trestle://catalogs/simplified_nist_catalog/catalog.json",
        "file://controls/catalog.json",
    )
    new_prof_json_text = new_prof_json_text.replace(
        '"param_id"', '"param-id"'
    )  # TODO compliance-trestle uses param_id and param-id interchangably, complytime requires param-id
    new_prof_json = json.loads(new_prof_json_text)

    new_cd_json_text = component_definition.read_text()
    new_cd_json_text = new_cd_json_text.replace(
        "trestle://profiles/simplified_nist_profile/profile.json",
        "file://controls/profile.json",
    )
    new_cd_json = json.loads(new_cd_json_text)

    with open(
        (complytime_home / ".config/complytime/controls/catalog.json"), "w"
    ) as file:
        json.dump(new_cat_json, file)
    with open(
        (complytime_home / ".config/complytime/controls/profile.json"), "w"
    ) as file:
        json.dump(new_prof_json, file)
    with open(
        (complytime_home / ".config/complytime/bundles/component-definition.json"), "w"
    ) as file:
        json.dump(new_cd_json, file)

    # shutil.copy(component_definition, complytime_home / '.config/complytime/bundles/')
    # shutil.copy(pathlib.Path(repo_dir) / 'catalogs/simplified_nist_catalog/catalog.json',
    #   complytime_home / '.config/complytime/bundles/')
    # shutil.copy(pathlib.Path(repo_dir) / 'profiles/simplified_nist_profile/profile.json',
    #   complytime_home / '.config/complytime/controls/')

    result = subprocess.run(
        ["complytime", "list", "--plain"],
        # cwd=complytime_home,
        capture_output=True,
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0
    assert b"Title" in result.stdout
    assert b"Framework ID" in result.stdout


@pytest.mark.slow
def test_compdef_type_validation_sync(
    tmp_repo: Tuple[str, Repo], complytime_home: pathlib.Path
) -> None:
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)
    setup_for_catalog(repo_path, "simplified_nist_catalog", "catalog")
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
            "--policy-id",
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

    test_product = "rhel8"
    test_cac_profile = test_content_dir / "products/rhel8/profiles/example.profile"
    test_prof = "simplified_nist_profile"
    test_comp_path = f"component-definitions/{test_product}/component-definition.json"
    test_cat = "simplified_nist_catalog"
    assert isinstance(sync_content_to_component_definition_cmd, BaseCommand)
    setup_for_catalog(repo_path, test_cat, "catalog")
    setup_for_profile(repo_path, test_prof, "profile")

    compdef_type = "validation"

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
            "--component-definition-type",
            compdef_type,
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

    # Fix trestle:// to file://

    new_cat_json_text = (
        pathlib.Path(repo_dir) / "catalogs/simplified_nist_catalog/catalog.json"
    ).read_text()
    new_cat_json_text = new_cat_json_text.replace(
        "trestle://catalogs/simplified_nist_catalog/catalog.json",
        "file://controls/catalog.json",
    )
    new_cat_json = json.loads(new_cat_json_text)

    new_prof_json_text = (
        pathlib.Path(repo_dir) / "profiles/simplified_nist_profile/profile.json"
    ).read_text()
    new_prof_json_text = new_prof_json_text.replace(
        "trestle://catalogs/simplified_nist_catalog/catalog.json",
        "file://controls/catalog.json",
    )
    new_prof_json_text = new_prof_json_text.replace(
        '"param_id"', '"param-id"'
    )  # TODO compliance-trestle uses param_id and param-id interchangably, complytime requires param-id
    new_prof_json = json.loads(new_prof_json_text)

    new_cd_json_text = component_definition.read_text()
    new_cd_json_text = new_cd_json_text.replace(
        "trestle://profiles/simplified_nist_profile/profile.json",
        "file://controls/profile.json",
    )
    new_cd_json = json.loads(new_cd_json_text)

    with open(
        (complytime_home / ".config/complytime/controls/catalog.json"), "w"
    ) as file:
        json.dump(new_cat_json, file)
    with open(
        (complytime_home / ".config/complytime/controls/profile.json"), "w"
    ) as file:
        json.dump(new_prof_json, file)
    with open(
        (complytime_home / ".config/complytime/bundles/component-definition.json"), "w"
    ) as file:
        json.dump(new_cd_json, file)

    # shutil.copy(component_definition, complytime_home / '.config/complytime/bundles/')
    # shutil.copy(pathlib.Path(repo_dir) / 'catalogs/simplified_nist_catalog/catalog.json',
    #   complytime_home / '.config/complytime/bundles/')
    # shutil.copy(pathlib.Path(repo_dir) / 'profiles/simplified_nist_profile/profile.json',
    #   complytime_home / '.config/complytime/controls/')

    result = subprocess.run(
        ["complytime", "list", "--plain"],
        # cwd=complytime_home,
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"Title" in result.stdout
    assert b"Framework ID" in result.stdout
