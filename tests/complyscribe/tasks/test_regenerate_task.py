# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test for complyscribe regenerate task"""

import argparse
import os
import pathlib
from typing import List
from unittest.mock import Mock, patch

import pytest
from trestle.core.commands.author.ssp import SSPAssemble, SSPGenerate

from complyscribe.tasks.authored.base_authored import (
    AuthoredObjectBase,
    AuthoredObjectException,
)
from complyscribe.tasks.authored.catalog import AuthoredCatalog
from complyscribe.tasks.authored.compdef import AuthoredComponentDefinition
from complyscribe.tasks.authored.profile import AuthoredProfile
from complyscribe.tasks.authored.ssp import AuthoredSSP, SSPIndex
from complyscribe.tasks.base_task import ModelFilter, TaskException
from complyscribe.tasks.regenerate_task import RegenerateTask
from tests import testutils


test_prof = "simplified_nist_profile"
test_comp = "test_comp"
test_cat = "simplified_nist_catalog"
test_ssp_output = "my-ssp"

cat_md_dir = "md_cat"
prof_md_dir = "md_prof"
compdef_md_dir = "md_comp"
ssp_md_dir = "md_ssp"


def test_regenerate_task_isolated(tmp_trestle_dir: str) -> None:
    """Test the regenerate task isolated from AuthoredObject implementation"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(cat_md_dir, test_cat)
    _ = testutils.setup_for_catalog(trestle_root, test_cat, md_path)

    mock = Mock(spec=AuthoredObjectBase)
    mock.get_trestle_root.return_value = tmp_trestle_dir
    regenerate_task = RegenerateTask(mock, cat_md_dir)

    with patch(
        "complyscribe.tasks.authored.types.get_trestle_model_dir"
    ) as mock_get_trestle_model_dir:
        mock_get_trestle_model_dir.return_value = "catalogs"

        assert regenerate_task.execute() == 0

        mock.regenerate.assert_called_once_with(
            model_path=f"catalogs/{test_cat}", markdown_path=cat_md_dir
        )


def test_regenerate_task_with_authored_object_failure(tmp_trestle_dir: str) -> None:
    """Test the regenerate task isolated with failing AuthoredObject implementation"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(cat_md_dir, test_cat)
    _ = testutils.setup_for_catalog(trestle_root, test_cat, md_path)

    mock = Mock(spec=AuthoredObjectBase)
    mock.get_trestle_root.return_value = tmp_trestle_dir
    mock.regenerate.side_effect = AuthoredObjectException("Test exception")
    regenerate_task = RegenerateTask(mock, cat_md_dir)

    with patch(
        "complyscribe.tasks.authored.types.get_trestle_model_dir"
    ) as mock_get_trestle_model_dir:
        with pytest.raises(TaskException, match="Test exception"):
            mock_get_trestle_model_dir.return_value = "catalogs"
            regenerate_task.execute()


@pytest.mark.parametrize(
    "skip_list",
    [
        ["simplified_nist_catalog"],
        ["*nist*"],
        ["simplified_nist_catalog", "simplified_nist_profile"],
        ["*catalog", "*profile"],
    ],
)
def test_regenerate_task_with_skip(tmp_trestle_dir: str, skip_list: List[str]) -> None:
    """Test the regenerate task isolated from AuthoredObject implementation"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(cat_md_dir, test_cat)
    _ = testutils.setup_for_catalog(trestle_root, test_cat, md_path)

    mock = Mock(spec=AuthoredObjectBase)
    mock.get_trestle_root.return_value = tmp_trestle_dir
    model_filter = ModelFilter(skip_list, ["*"])
    regenerate_task = RegenerateTask(
        mock, markdown_dir=cat_md_dir, model_filter=model_filter
    )

    with patch(
        "complyscribe.tasks.authored.types.get_trestle_model_dir"
    ) as mock_get_trestle_model_dir:
        mock_get_trestle_model_dir.return_value = "catalogs"

        assert regenerate_task.execute() == 0

        mock.regenerate.assert_not_called()


def test_catalog_regenerate_task(tmp_trestle_dir: str) -> None:
    """Test catalog regenerate at the task level"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(cat_md_dir, test_cat)
    _ = testutils.setup_for_catalog(trestle_root, test_cat, md_path)

    catalog = AuthoredCatalog(tmp_trestle_dir)
    regenerate_task = RegenerateTask(catalog, cat_md_dir)

    assert regenerate_task.execute() == 0
    assert os.path.exists(os.path.join(tmp_trestle_dir, md_path))


def test_profile_regenerate_task(tmp_trestle_dir: str) -> None:
    """Test profile regenerate at the task level"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(prof_md_dir, test_prof)
    _ = testutils.setup_for_profile(trestle_root, test_prof, md_path)

    profile = AuthoredProfile(tmp_trestle_dir)
    regenerate_task = RegenerateTask(profile, prof_md_dir)

    assert regenerate_task.execute() == 0
    assert os.path.exists(os.path.join(tmp_trestle_dir, md_path))


def test_compdef_regenerate_task(tmp_trestle_dir: str) -> None:
    """Test compdef regenerate at the task level"""
    trestle_root = pathlib.Path(tmp_trestle_dir)

    md_path = os.path.join(compdef_md_dir, test_comp)
    _ = testutils.setup_for_compdef(trestle_root, test_comp, md_path)

    compdef = AuthoredComponentDefinition(tmp_trestle_dir)
    regenerate_task = RegenerateTask(compdef, compdef_md_dir)

    assert regenerate_task.execute() == 0

    # The compdef is a special case where each component has a separate markdown directory
    assert os.path.exists(os.path.join(tmp_trestle_dir, md_path, test_comp))


@pytest.mark.parametrize(
    "write_ssp_index",
    [
        True,
        False,
    ],
)
def test_ssp_regenerate_task(tmp_trestle_dir: str, write_ssp_index: bool) -> None:
    """Test ssp regenerate at the task level with and without an index"""
    ssp_index_path = os.path.join(tmp_trestle_dir, "ssp-index.json")
    ssp_index = SSPIndex(ssp_index_path)
    if write_ssp_index:
        ssp_index.add_new_ssp(test_ssp_output, test_prof, [test_comp])
        ssp_index.write_out()

    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(ssp_md_dir, test_ssp_output)

    # Create initial SSP for testing
    args = testutils.setup_for_ssp(trestle_root, test_prof, [test_comp], md_path)
    ssp_generate = SSPGenerate()
    assert ssp_generate._run(args) == 0

    # create ssp from the markdown
    ssp_assemble = SSPAssemble()
    args = argparse.Namespace(
        trestle_root=tmp_trestle_dir,
        markdown=md_path,
        output=test_ssp_output,
        verbose=0,
        name=None,
        version=None,
        regenerate=False,
        compdefs=args.compdefs,
    )
    assert ssp_assemble._run(args) == 0

    ssp = AuthoredSSP(tmp_trestle_dir, ssp_index)
    regenerate_task = RegenerateTask(ssp, ssp_md_dir)

    if write_ssp_index:
        assert regenerate_task.execute() == 0
        assert os.path.exists(os.path.join(tmp_trestle_dir, md_path))
    else:
        with pytest.raises(
            TaskException, match="SSP my-ssp does not exists in the index"
        ):
            regenerate_task.execute()
