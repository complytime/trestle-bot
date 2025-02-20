# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Helper functions for unit test setup and teardown."""

import argparse
import logging
import os
import pathlib
import shutil
import tempfile
from typing import Dict, List, Optional

from git.repo import Repo
from trestle.common.err import TrestleError
from trestle.common.model_utils import ModelUtils
from trestle.core.base_model import OscalBaseModel
from trestle.core.commands.init import InitCmd
from trestle.core.models.file_content_type import FileContentType
from trestle.oscal import catalog as cat
from trestle.oscal import component as comp
from trestle.oscal import profile as prof

from trestlebot.cli.log import configure_logger
from trestlebot.const import YAML_EXTENSION


TEST_DATA_DIR = pathlib.Path(__file__).parent.resolve() / "data/"
JSON_TEST_DATA_PATH = pathlib.Path(__file__).parent.resolve() / "data/json/"
YAML_TEST_DATA_PATH = pathlib.Path(__file__).parent.resolve() / "data/yaml/"
TEST_SSP_INDEX = JSON_TEST_DATA_PATH / "test_ssp_index.json"
INVALID_TEST_SSP_INDEX = JSON_TEST_DATA_PATH / "invalid_test_ssp_index.json"
TEST_YAML_HEADER = YAML_TEST_DATA_PATH / "extra_yaml_header.yaml"

TEST_REMOTE_REPO_URL = "http://localhost:8080/test.git"


def configure_test_logger(level: int = logging.INFO) -> None:
    """
    Configure the logger for testing.

    Notes: This is used to patch the logger in tests
    so the caplog can be used to capture log messages.
    This does not happen when propagate is set to False.
    """
    configure_logger(level=level, propagate=True)


def clean(repo_path: str, repo: Optional[Repo] = None) -> None:
    """Clean up the temporary Git repository."""
    if repo is not None:
        repo.close()
    shutil.rmtree(repo_path)


def repo_setup(repo_path: pathlib.Path) -> Repo:
    """Create a temporary Git repository."""
    try:
        args = argparse.Namespace(
            verbose=0,
            trestle_root=repo_path,
            full=True,
            local=False,
            govdocs=False,
        )
        init = InitCmd()
        init._run(args)
    except Exception as e:
        raise TrestleError(
            f"Initialization failed for temporary trestle directory: {e}."
        )
    repo = Repo.init(repo_path)
    with repo.config_writer() as config:
        config.set_value("user", "email", "test@example.com")
        config.set_value("user", "name", "Test User")
    repo.git.add(all=True)
    repo.index.commit("Initial commit")
    # Create a default branch (main)
    repo.git.checkout("-b", "main")
    return repo


def args_dict_to_list(args_dict: Dict[str, str]) -> List[str]:
    """Transform dictionary of args to a list of args."""
    args = []
    for k, v in args_dict.items():
        args.append(f"--{k}")
        if v is not None:
            args.append(v)
    return args


def load_from_json(
    tmp_trestle_dir: pathlib.Path,
    file_prefix: str,
    model_name: str,
    model_type: OscalBaseModel,
) -> None:
    """Load model from JSON test dir."""
    src_path = JSON_TEST_DATA_PATH / f"{file_prefix}.json"
    dst_path: pathlib.Path = ModelUtils.get_model_path_for_name_and_class(
        tmp_trestle_dir, model_name, model_type, FileContentType.JSON  # type: ignore
    )
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst_path)


def load_from_yaml(
    rules_path: pathlib.Path,
    file_prefix: str,
    dst_name: str = "",
) -> None:
    """Load rule from YAML test dir."""
    if not dst_name:
        dst_name = file_prefix
    src_path = YAML_TEST_DATA_PATH / f"{file_prefix}{YAML_EXTENSION}"
    rules_path = rules_path.joinpath(f"{dst_name}{YAML_EXTENSION}")
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, rules_path)


def setup_for_ssp(
    tmp_trestle_dir: pathlib.Path,
    prof_name: str,
    comps: List[str],
    output_name: str,
) -> argparse.Namespace:
    """Setup trestle temp directory for ssp testing"""
    for comp_name in comps:
        load_from_json(tmp_trestle_dir, comp_name, comp_name, comp.ComponentDefinition)  # type: ignore

    comp_list = ",".join(comps)

    load_from_json(tmp_trestle_dir, prof_name, prof_name, prof.Profile)  # type: ignore
    load_from_json(
        tmp_trestle_dir,
        "simplified_nist_catalog",
        "simplified_nist_catalog",
        cat.Catalog,  # type: ignore
    )
    args = argparse.Namespace(
        trestle_root=tmp_trestle_dir,
        profile=prof_name,
        compdefs=comp_list,
        output=output_name,
        verbose=0,
        overwrite_header_values=False,
        yaml_header=None,
        allowed_sections=None,
        force_overwrite=None,
        leveraged_ssp=None,
        include_all_parts=False,
    )

    return args


def setup_for_profile(
    tmp_trestle_dir: pathlib.Path, prof_name: str, output_name: str
) -> argparse.Namespace:
    """Setup trestle temp directory for profile testing."""
    load_from_json(tmp_trestle_dir, prof_name, prof_name, prof.Profile)  # type: ignore

    load_from_json(
        tmp_trestle_dir,
        "simplified_nist_catalog",
        "simplified_nist_catalog",
        cat.Catalog,  # type: ignore
    )

    args = argparse.Namespace(
        trestle_root=tmp_trestle_dir,
        name=prof_name,
        output=output_name,
        verbose=0,
        yaml_header=None,
        overwrite_header_values=False,
        force_overwrite=None,
        sections=None,
        required_sections=None,
        allowed_sections=None,
    )

    return args


def setup_for_catalog(
    tmp_trestle_dir: pathlib.Path, cat_name: str, output_name: str
) -> argparse.Namespace:
    """Setup trestle temp directory for catalog testing"""
    load_from_json(tmp_trestle_dir, cat_name, cat_name, cat.Catalog)  # type: ignore
    args = argparse.Namespace(
        trestle_root=tmp_trestle_dir,
        name=cat_name,
        output=output_name,
        verbose=0,
        overwrite_header_values=False,
        yaml_header=None,
        force_overwrite=None,
    )

    return args


def setup_for_compdef(
    tmp_trestle_dir: pathlib.Path, comp_name: str, output_name: str
) -> argparse.Namespace:
    """Setup trestle temp directory for component definitions testing"""
    load_from_json(tmp_trestle_dir, comp_name, comp_name, comp.ComponentDefinition)  # type: ignore
    load_from_json(
        tmp_trestle_dir,
        "simplified_nist_profile",
        "simplified_nist_profile",
        prof.Profile,  # type: ignore
    )
    load_from_json(
        tmp_trestle_dir,
        "simplified_nist_catalog",
        "simplified_nist_catalog",
        cat.Catalog,  # type: ignore
    )
    args = argparse.Namespace(
        trestle_root=tmp_trestle_dir,
        name=comp_name,
        output=output_name,
        verbose=0,
        yaml_header=None,
        overwrite_header_values=False,
        force_overwrite=None,
    )

    return args


def setup_for_cac_content_dir(tmp_dir: str, cac_content_src_dir: pathlib.Path) -> None:
    """
    Setup cac content dir for testing
    """
    shutil.copytree(cac_content_src_dir, tmp_dir, dirs_exist_ok=True)

    # modify abcd-levels.yml control file for sync OSCAL content testing
    abcd_levels_control_file_path = os.path.join(tmp_dir, "controls", "abcd-levels.yml")
    replace_string_in_file(
        abcd_levels_control_file_path,
        "rules: []",
        "rules:\n      - file_groupownership_sshd_private_key\n"
        "      - var_sshd_set_keepalive=1\n      - var_system_crypto_policy=fips",
    )


def setup_rules_view(
    tmp_trestle_dir: pathlib.Path,
    output_name: str,
    rules_dir: str = "rules",
    comp_name: str = "test_comp",
    incomplete_rule: bool = False,
    skip_rules: bool = False,
) -> None:
    """Prepare rules view for testing with a single component definition and test component."""
    load_from_json(
        tmp_trestle_dir,
        "simplified_nist_profile",
        "simplified_nist_profile",
        prof.Profile,  # type: ignore
    )
    load_from_json(
        tmp_trestle_dir,
        "simplified_nist_catalog",
        "simplified_nist_catalog",
        cat.Catalog,  # type: ignore
    )
    rules_path = tmp_trestle_dir.joinpath(rules_dir)
    compdef_dir = rules_path.joinpath(output_name)
    comp_dir = compdef_dir.joinpath(comp_name)
    comp_dir.mkdir(parents=True, exist_ok=True)

    if skip_rules:
        return

    if incomplete_rule:
        load_from_yaml(comp_dir, "test_incomplete_rule")
    else:
        # Load a complete rule with optional fields
        load_from_yaml(comp_dir, "test_complete_rule")
        # Load a complete rule with only required fields
        load_from_yaml(comp_dir, "test_complete_rule_no_params")
        # Load a complete rule with multiple controls
        load_from_yaml(comp_dir, "test_complete_rule_multiple_controls")


def setup_for_init(tmp_init_dir: pathlib.Path) -> None:
    """Creates an empty git repo"""
    git_dir: pathlib.Path = tmp_init_dir.joinpath(pathlib.Path(".git"))
    git_dir.mkdir()


def replace_string_in_file(file_path: str, old_string: str, new_string: str) -> None:
    """Replace a string in a file."""
    # Read the content of the file
    with open(file_path, "r") as file:
        file_content = file.read()

    # Replace the old string with the new string
    updated_content = file_content.replace(old_string, new_string)

    # Write the updated content back to the file
    with open(file_path, "w") as file:
        file.write(updated_content)


def prepare_upstream_repo() -> str:
    """
    Prepare a temporary upstream repo for testing.

    Returns:
        str: Path to the upstream repo

    Notes:
    This includes the test NIST catalog and a modified profile.
    It modifies the simplified_nist_profile to simulate upstream
    changes for testing.
    """
    tmp_dir = pathlib.Path(tempfile.mkdtemp())
    repo: Repo = repo_setup(tmp_dir)
    load_from_json(
        tmp_dir, "simplified_nist_catalog", "simplified_nist_catalog", cat.Catalog
    )

    # Modify the profile to include an additional control and write it out
    src_path = JSON_TEST_DATA_PATH / "simplified_nist_profile.json"
    dst_path: pathlib.Path = ModelUtils.get_model_path_for_name_and_class(
        tmp_dir, "simplified_nist_profile", prof.Profile, FileContentType.JSON  # type: ignore
    )
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    test_profile: prof.Profile = prof.Profile.oscal_read(src_path)

    prof_import: prof.Import = test_profile.imports[0]
    prof_import.include_controls[0].with_ids.append(prof.WithId(__root__="ac-6"))
    test_profile.oscal_write(dst_path)

    repo.git.add(all=True)
    repo.index.commit("Add updated profile")
    repo.close()
    return str(tmp_dir)
