# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.


"""Testing module for complyscribe autosync command"""
import pathlib
from typing import Tuple

from click.testing import CliRunner
from git import Repo

from complyscribe.cli.commands.autosync import autosync_cmd
from complyscribe.cli.config import ComplyScribeConfig, write_to_file


def test_invalid_oscal_model(tmp_repo: Tuple[str, Repo]) -> None:
    """Test invalid OSCAl model option."""

    repo_path, _ = tmp_repo
    runner = CliRunner()
    result = runner.invoke(
        autosync_cmd,
        [
            "--oscal-model",
            "invalid",
            "--repo-path",
            repo_path,
            "--markdown-dir",
            "markdown",
            "--branch",
            "main",
            "--committer-name",
            "Test User",
            "--committer-email",
            "test@example.com",
        ],
    )
    assert "Invalid value for '--oscal-model'" in result.output
    assert result.exit_code == 2


def test_missing_ssp_index_file_option(tmp_repo: Tuple[str, Repo]) -> None:
    """Test missing ssp_index_file option for autosync ssp."""
    repo_path, _ = tmp_repo
    runner = CliRunner()
    cmd_options = [
        "--oscal-model",
        "ssp",
        "--repo-path",
        repo_path,
        "--markdown-dir",
        "markdown",
        "--branch",
        "main",
        "--committer-name",
        "Test User",
        "--committer-email",
        "test@example.com",
    ]
    result = runner.invoke(autosync_cmd, cmd_options)
    assert result.exit_code == 1
    assert "missing option '--ssp-index-file'" in result.output


def test_missing_markdown_dir_option(tmp_repo: Tuple[str, Repo]) -> None:
    # When no markdown_dir setting in complyscribe config file.
    repo_path, _ = tmp_repo
    runner = CliRunner()
    filepath = pathlib.Path(repo_path).joinpath("config.yml")
    config_obj = ComplyScribeConfig(repo_path=repo_path)
    write_to_file(config_obj, filepath)
    cmd_options = [
        "--oscal-model",
        "compdef",
        "--repo-path",
        repo_path,
        "--branch",
        "main",
        "--committer-name",
        "Test User",
        "--committer-email",
        "test@example.com",
        "--config",
        str(filepath),
    ]
    result = runner.invoke(autosync_cmd, cmd_options)
    assert result.exit_code == 2
    assert "Error: Missing option '--markdown-dir'" in result.output

    # With non-existent 'markdown_dir' setting in config.yml
    config_obj = ComplyScribeConfig(markdown_dir="markdown")
    write_to_file(config_obj, filepath)
    result = runner.invoke(autosync_cmd, cmd_options)
    assert result.exit_code == 1
