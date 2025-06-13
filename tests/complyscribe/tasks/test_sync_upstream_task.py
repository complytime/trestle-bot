# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.


"""Test for complyscribe sync upstreams task"""

import os
import pathlib
import shutil
from typing import Tuple

import pytest
from git.repo import Repo
from trestle.common.const import TRESTLE_CONFIG_DIR

from complyscribe.tasks.base_task import ModelFilter, TaskException
from complyscribe.tasks.sync_upstreams_task import SyncUpstreamsTask
from tests.testutils import setup_for_compdef


def test_sync_upstreams_task(tmp_trestle_dir: str, tmp_repo: Tuple[str, Repo]) -> None:
    """Test sync upstreams task"""
    tmp_repo_path, repo = tmp_repo
    source_trestle_root = pathlib.Path(tmp_repo_path)
    setup_for_compdef(source_trestle_root, "test_comp", "test_comp")
    repo.git.add(all=True)
    repo.index.commit("Adds test_comp")
    sync = SyncUpstreamsTask(tmp_trestle_dir, [f"{tmp_repo_path}@main"])
    assert sync.execute() == 0

    # Make sure the correct files are in the destination workspace
    dest_trestle_root = pathlib.Path(tmp_trestle_dir)
    assert (dest_trestle_root / "component-definitions" / "test_comp").exists()
    assert (dest_trestle_root / "profiles" / "simplified_nist_profile").exists()
    assert (dest_trestle_root / "catalogs" / "simplified_nist_catalog").exists()


def test_sync_upstreams_task_with_filter(
    tmp_trestle_dir: str, tmp_repo: Tuple[str, Repo]
) -> None:
    """Test sync upstreams task with filter"""
    tmp_repo_path, repo = tmp_repo
    source_trestle_root = pathlib.Path(tmp_repo_path)
    setup_for_compdef(source_trestle_root, "invalid_comp", "invalid_comp")
    setup_for_compdef(source_trestle_root, "test_comp", "test_comp")
    repo.git.add(all=True)
    repo.index.commit("Adds test_comp and invalid_comp")
    model_filter = ModelFilter(
        skip_patterns=["invalid_comp"], include_patterns=["test_comp"]
    )
    sync = SyncUpstreamsTask(tmp_trestle_dir, [f"{tmp_repo_path}@main"], model_filter)
    assert sync.execute() == 0

    # Make sure the correct files are in the destination workspace
    dest_trestle_root = pathlib.Path(tmp_trestle_dir)
    assert (dest_trestle_root / "component-definitions" / "test_comp").exists()
    assert not (dest_trestle_root / "component-definitions" / "invalid_comp").exists()


def test_sync_upstream_invalid_source(tmp_trestle_dir: str) -> None:
    """Test sync upstreams task with invalid source"""
    sync = SyncUpstreamsTask(tmp_trestle_dir, ["invalid_source"])
    with pytest.raises(
        TaskException,
        match="Invalid source .* must be of the form <repo_url>@<ref>",
    ):
        sync.execute()


def test_sync_upstream_invalid_workspace(
    tmp_trestle_dir: str, tmp_repo: Tuple[str, Repo]
) -> None:
    """Test sync upstreams task with invalid source workspace"""
    tmp_repo_path, _ = tmp_repo
    # Remove the trestle config to make this workspace invalid
    trestle_config_dir = os.path.join(tmp_trestle_dir, TRESTLE_CONFIG_DIR)
    shutil.rmtree(trestle_config_dir)
    with pytest.raises(
        TaskException, match="Target workspace .* is not a valid trestle project root"
    ):
        SyncUpstreamsTask(tmp_trestle_dir, [f"{tmp_repo_path}@main"])


def test_sync_upstream_invalid_model(
    tmp_trestle_dir: str, tmp_repo: Tuple[str, Repo]
) -> None:
    """Test sync upstreams task with invalid model"""
    tmp_repo_path, repo = tmp_repo
    source_trestle_root = pathlib.Path(tmp_repo_path)
    setup_for_compdef(source_trestle_root, "invalid_comp", "invalid_comp")
    repo.git.add(all=True)
    repo.index.commit("Adds invalid_comp")
    sync = SyncUpstreamsTask(tmp_trestle_dir, [f"{tmp_repo_path}@main"])
    with pytest.raises(TaskException, match="Model .* is not valid"):
        sync.execute()

    # Now disable validation and try again
    sync = SyncUpstreamsTask(tmp_trestle_dir, [f"{tmp_repo_path}@main"], validate=False)
    assert sync.execute() == 0


def test_sync_upstream_invalid_git(
    tmp_trestle_dir: str, tmp_repo: Tuple[str, Repo]
) -> None:
    """Test sync upstreams task with invalid git source"""
    tmp_repo_path, _ = tmp_repo
    new_path = f"{tmp_repo_path}1"
    sync = SyncUpstreamsTask(tmp_trestle_dir, [f"{new_path}@main"])
    with pytest.raises(
        TaskException, match="Git error occurred while fetching content from .*"
    ):
        sync.execute()
