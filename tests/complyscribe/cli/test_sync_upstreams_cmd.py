# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.


"""Unit tests for upstreams commands."""

import pathlib
from typing import Tuple

from click.testing import CliRunner
from git import Repo

from complyscribe.cli.commands.sync_upstreams import sync_upstreams_cmd
from complyscribe.cli.config import make_config, write_to_file
from complyscribe.const import COMPLYSCRIBE_CONFIG_DIR
from tests.testutils import clean, prepare_upstream_repo, setup_for_init


TEST_CATALOG = "simplified_nist_catalog"
TEST_CATALOG_PATH = "catalogs/simplified_nist_catalog/catalog.json"
TEST_PROFILE = "simplified_nist_profile"
TEST_PROFILE_PATH = "profiles/simplified_nist_profile/profile.json"


def test_sync_upstreams(tmp_repo: Tuple[str, Repo]) -> None:
    """Test sync upstreams"""
    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    source: str = prepare_upstream_repo()

    runner = CliRunner()
    result = runner.invoke(
        sync_upstreams_cmd,
        [
            "--repo-path",
            repo_path,
            "--sources",
            f"{source}@main",
            "--branch",
            "main",
            "--committer-email",
            "test@email",
            "--committer-name",
            "test name",
        ],
    )

    assert repo_path.joinpath(TEST_CATALOG_PATH).exists()
    assert repo_path.joinpath(TEST_PROFILE_PATH).exists()
    assert result.exit_code == 0
    clean(source)


def test_sync_upstreams_with_config(
    tmp_repo: Tuple[str, Repo], tmp_init_dir: str
) -> None:
    """Test sync upstreams using a config file."""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    source: str = prepare_upstream_repo()

    complyscribe_dir = pathlib.Path(tmp_init_dir) / pathlib.Path(
        COMPLYSCRIBE_CONFIG_DIR
    )
    complyscribe_dir.mkdir()

    setup_for_init(pathlib.Path(tmp_init_dir))

    config_path = (
        pathlib.Path(tmp_init_dir)
        .joinpath(COMPLYSCRIBE_CONFIG_DIR)
        .joinpath("config.yml")
    )

    config = make_config(
        {
            "branch": "main",
            "committer_name": "test name",
            "committer_email": "test@email",
            "upstreams": {
                "sources": [f"{source}@main"],
                "include_models": ["*"],
                "skip_validation": False,
            },
        }
    )

    write_to_file(config, config_path)

    runner = CliRunner()
    result = runner.invoke(
        sync_upstreams_cmd,
        ["--repo-path", repo_path, "--config", config_path.resolve()],
    )
    assert repo_path.joinpath(TEST_CATALOG_PATH).exists()
    assert repo_path.joinpath(TEST_PROFILE_PATH).exists()
    assert result.exit_code == 0
    clean(source)


def test_sync_upstreams_exclude_models(tmp_repo: Tuple[str, Repo]) -> None:
    """Test sync upstreams with exclude models"""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    source: str = prepare_upstream_repo()

    runner = CliRunner()
    result = runner.invoke(
        sync_upstreams_cmd,
        [
            "--repo-path",
            repo_path,
            "--sources",
            f"{source}@main",
            "--branch",
            "main",
            "--exclude-models",
            TEST_PROFILE,
            "--committer-email",
            "test@email",
            "--committer-name",
            "test",
        ],
    )

    assert repo_path.joinpath(TEST_CATALOG_PATH).exists()
    assert not repo_path.joinpath(TEST_PROFILE_PATH).exists()
    assert result.exit_code == 0
    clean(source)


def test_sync_upstreams_no_sources(tmp_repo: Tuple[str, Repo]) -> None:
    """Test sync upstreams with sources option missing"""

    repo_dir, _ = tmp_repo
    repo_path = pathlib.Path(repo_dir)

    runner = CliRunner()
    result = runner.invoke(
        sync_upstreams_cmd,
        [
            "--repo-path",
            repo_path,
            "--branch",
            "main",
            "--committer-name",
            "test name",
            "--committer-email",
            "test@email",
        ],
    )

    assert "missing option '--sources'" in result.output
    assert result.exit_code == 1
