# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Unit test for create commands ssp and cd"""
import pathlib
from typing import Tuple

from click.testing import CliRunner
from git import Repo

from complyscribe.cli.commands.create import create_cmd
from tests.testutils import setup_for_compdef, setup_for_ssp


test_prof = "simplified_nist_profile"
test_comp_name = "test_comp"
test_ssp_md = "md_ssp"
test_ssp_cd = "md_cd"


def test_invalid_create_cmd() -> None:
    """Tests that create command fails if given invalid oscal model subcommand."""
    runner = CliRunner()
    result = runner.invoke(create_cmd, ["invalid"])

    assert "Error: No such command 'invalid'" in result.output
    assert result.exit_code == 2


def test_create_ssp_cmd(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests successful create ssp command."""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    ssp_index_file = repo_path.joinpath("ssp-index.json")

    _ = setup_for_ssp(repo_path, test_prof, [test_comp_name], test_ssp_md)

    runner = CliRunner()
    result = runner.invoke(
        create_cmd,
        [
            "ssp",
            "--profile-name",
            test_prof,
            "--markdown-dir",
            "markdown",
            "--compdefs",
            test_comp_name,
            "--ssp-name",
            "test-name",
            "--repo-path",
            str(repo_path.resolve()),
            "--ssp-index-file",
            ssp_index_file,
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
        ],
    )
    assert result.exit_code == 0


def test_create_compdef_cmd(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests successful create compdef command."""
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    _ = setup_for_compdef(repo_path, test_comp_name, test_ssp_cd)

    runner = CliRunner()
    result = runner.invoke(
        create_cmd,
        [
            "compdef",
            "--profile-name",
            "oscal-profile-name",
            "--compdef-name",
            "test-name",
            "--component-title",
            "title-test",
            "--component-description",
            "description-test",
            "--component-definition-type",
            "type-test",
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
    assert result.exit_code == 0


def test_default_ssp_index_file_cmd(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests successful default ssp_index.json file creation."""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    runner = CliRunner()
    result = runner.invoke(
        create_cmd,
        [
            "ssp",
            "--profile-name",
            "oscal-profile-name",
            "--markdown-dir",
            "markdown",
            "--compdefs",
            "test-compdef",
            "--ssp-name",
            "test-name",
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
    assert result.exit_code == 0


def test_markdown_files_created(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests successful creation of markdown files."""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)
    ssp_index_file = repo_path.joinpath("ssp-index.json")

    runner = CliRunner()
    result = runner.invoke(
        create_cmd,
        [
            "ssp",
            "--profile-name",
            "oscal-profile-name",
            "--markdown-dir",
            "markdown",
            "--compdefs",
            "test-compdef",
            "--ssp-name",
            "test-name",
            "--repo-path",
            str(repo_path.resolve()),
            "--ssp-index-file",
            ssp_index_file,
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
        ],
    )
    assert result.exit_code == 0
