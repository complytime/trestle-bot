# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test for complyscribe assemble task"""

import os
import pathlib
from typing import List
from unittest.mock import Mock, patch

import pytest
from trestle.common.model_utils import ModelUtils
from trestle.core.commands.author.catalog import CatalogGenerate
from trestle.core.commands.author.component import ComponentGenerate
from trestle.core.commands.author.prof import ProfileGenerate
from trestle.core.commands.author.ssp import SSPGenerate
from trestle.core.models.file_content_type import FileContentType
from trestle.oscal import catalog as oscal_cat
from trestle.oscal import component as oscal_comp
from trestle.oscal import profile as oscal_prof

from complyscribe.tasks.assemble_task import AssembleTask
from complyscribe.tasks.authored.base_authored import (
    AuthoredObjectBase,
    AuthoredObjectException,
)
from complyscribe.tasks.authored.catalog import AuthoredCatalog
from complyscribe.tasks.authored.compdef import AuthoredComponentDefinition
from complyscribe.tasks.authored.profile import AuthoredProfile
from complyscribe.tasks.authored.ssp import AuthoredSSP, SSPIndex
from complyscribe.tasks.base_task import ModelFilter, TaskException
from tests import testutils


test_prof = "simplified_nist_profile"
test_comp = "test_comp"
test_cat = "simplified_nist_catalog"
test_ssp_output = "my-ssp"

cat_md_dir = "md_cat"
prof_md_dir = "md_prof"
compdef_md_dir = "md_comp"
ssp_md_dir = "md_ssp"


def test_assemble_task_isolated(tmp_trestle_dir: str) -> None:
    """Test the assemble task isolated from AuthoredObject implementation"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(cat_md_dir, test_cat)
    args = testutils.setup_for_catalog(trestle_root, test_cat, md_path)
    cat_generate = CatalogGenerate()
    assert cat_generate._run(args) == 0

    mock = Mock(spec=AuthoredObjectBase)
    mock.get_trestle_root.return_value = tmp_trestle_dir
    assemble_task = AssembleTask(mock, cat_md_dir, "1.0.0")

    with patch(
        "complyscribe.tasks.authored.types.get_trestle_model_dir"
    ) as mock_get_trestle_model_dir:
        mock_get_trestle_model_dir.return_value = "catalogs"

        assert assemble_task.execute() == 0

        mock.assemble.assert_called_once_with(
            markdown_path=md_path, version_tag="1.0.0"
        )


def test_assemble_task_with_authored_object_failure(tmp_trestle_dir: str) -> None:
    """Test the assemble task with failing AuthoredObject implementation"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(cat_md_dir, test_cat)
    args = testutils.setup_for_catalog(trestle_root, test_cat, md_path)
    cat_generate = CatalogGenerate()
    assert cat_generate._run(args) == 0

    mock = Mock(spec=AuthoredObjectBase)
    mock.get_trestle_root.return_value = tmp_trestle_dir
    mock.assemble.side_effect = AuthoredObjectException("Test exception")
    assemble_task = AssembleTask(mock, cat_md_dir, "1.0.0")

    with patch(
        "complyscribe.tasks.authored.types.get_trestle_model_dir"
    ) as mock_get_trestle_model_dir:
        with pytest.raises(TaskException, match="Test exception"):
            mock_get_trestle_model_dir.return_value = "catalogs"
            assemble_task.execute()


def test_assemble_task_with_non_existent_markdown(tmp_trestle_dir: str) -> None:
    """Test the assemble task with failing AuthoredObject implementation"""

    mock = Mock(spec=AuthoredObjectBase)
    mock.get_trestle_root.return_value = tmp_trestle_dir
    mock.assemble.side_effect = AuthoredObjectException("Test exception")
    assemble_task = AssembleTask(mock, cat_md_dir, "1.0.0")

    with pytest.raises(TaskException, match="Markdown directory .* does not exist"):
        assemble_task.execute()


@pytest.mark.parametrize(
    "skip_list",
    [
        ["simplified_nist_catalog"],
        ["*nist*"],
        ["simplified_nist_catalog", "simplified_nist_profile"],
        ["*catalog", "*profile"],
    ],
)
def test_assemble_task_with_skip(tmp_trestle_dir: str, skip_list: List[str]) -> None:
    """Test ssp assemble with a skip list"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(cat_md_dir, test_cat)
    args = testutils.setup_for_catalog(trestle_root, test_cat, md_path)
    cat_generate = CatalogGenerate()
    assert cat_generate._run(args) == 0

    mock = Mock(spec=AuthoredObjectBase)
    mock.get_trestle_root.return_value = tmp_trestle_dir
    model_filter = ModelFilter(skip_list, ["*"])

    assemble_task = AssembleTask(mock, cat_md_dir, cat_md_dir, model_filter)

    with patch(
        "complyscribe.tasks.authored.types.get_trestle_model_dir"
    ) as mock_get_trestle_model_dir:
        mock_get_trestle_model_dir.return_value = "catalogs"

        assert assemble_task.execute() == 0
        mock.assemble.assert_not_called()


def test_catalog_assemble_task(tmp_trestle_dir: str) -> None:
    """Test catalog assemble at the task level"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(cat_md_dir, test_cat)
    args = testutils.setup_for_catalog(trestle_root, test_cat, md_path)
    cat_generate = CatalogGenerate()
    assert cat_generate._run(args) == 0

    # Get original last modified time
    cat, _ = ModelUtils.load_model_for_class(
        trestle_root, test_cat, oscal_cat.Catalog, FileContentType.JSON
    )
    orig_time = cat.metadata.last_modified

    catalog = AuthoredCatalog(tmp_trestle_dir)
    assemble_task = AssembleTask(catalog, cat_md_dir)

    assert assemble_task.execute() == 0

    # Get new last modified time and verify catalog was modified
    cat, _ = ModelUtils.load_model_for_class(
        trestle_root, test_cat, oscal_cat.Catalog, FileContentType.JSON
    )
    assert orig_time != cat.metadata.last_modified


def test_profile_assemble_task(tmp_trestle_dir: str) -> None:
    """Test profile assemble at the task level"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(prof_md_dir, test_prof)
    args = testutils.setup_for_profile(trestle_root, test_prof, md_path)
    profile_generate = ProfileGenerate()
    assert profile_generate._run(args) == 0

    # Get original last modified time
    prof, _ = ModelUtils.load_model_for_class(
        trestle_root, test_prof, oscal_prof.Profile, FileContentType.JSON
    )
    orig_time = prof.metadata.last_modified

    profile = AuthoredProfile(tmp_trestle_dir)
    assemble_task = AssembleTask(profile, prof_md_dir)

    assert assemble_task.execute() == 0

    # Get new last modified time adn verify profile was modified
    prof, _ = ModelUtils.load_model_for_class(
        trestle_root, test_prof, oscal_prof.Profile, FileContentType.JSON
    )
    assert orig_time != prof.metadata.last_modified


def test_compdef_assemble_task(tmp_trestle_dir: str) -> None:
    """Test compdef assemble at the task level"""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(compdef_md_dir, test_comp)
    args = testutils.setup_for_compdef(trestle_root, test_comp, md_path)
    comp_generate = ComponentGenerate()
    assert comp_generate._run(args) == 0

    # Get ac-1 markdown file
    comp_path = os.path.join(trestle_root, compdef_md_dir, test_comp, test_comp)
    ac1_md_path = os.path.join(comp_path, test_prof, "ac", "ac-1.md")
    testutils.replace_string_in_file(ac1_md_path, "partial", "implemented")

    # Get original last modified time
    comp, _ = ModelUtils.load_model_for_class(
        trestle_root, test_comp, oscal_comp.ComponentDefinition, FileContentType.JSON
    )
    orig_time = comp.metadata.last_modified

    compdef = AuthoredComponentDefinition(tmp_trestle_dir)
    assemble_task = AssembleTask(compdef, compdef_md_dir)

    assert assemble_task.execute() == 0

    # Get new last modified time and verify component was modified
    comp, _ = ModelUtils.load_model_for_class(
        trestle_root, test_comp, oscal_comp.ComponentDefinition, FileContentType.JSON
    )
    assert orig_time != comp.metadata.last_modified


@pytest.mark.parametrize(
    "write_ssp_index",
    [
        True,
        False,
    ],
)
def test_ssp_assemble_task(tmp_trestle_dir: str, write_ssp_index: bool) -> None:
    """Test ssp assemble at the task level with and without an index"""
    ssp_index_path = os.path.join(tmp_trestle_dir, "ssp-index.json")
    ssp_index = SSPIndex(ssp_index_path)

    if write_ssp_index:
        ssp_index.add_new_ssp(test_ssp_output, test_prof, [test_comp])
        ssp_index.write_out()

    trestle_root = pathlib.Path(tmp_trestle_dir)
    md_path = os.path.join(ssp_md_dir, test_ssp_output)
    args = testutils.setup_for_ssp(trestle_root, test_prof, [test_comp], md_path)
    ssp_generate = SSPGenerate()
    assert ssp_generate._run(args) == 0

    ssp = AuthoredSSP(tmp_trestle_dir, ssp_index)
    assemble_task = AssembleTask(ssp, ssp_md_dir)

    if write_ssp_index:
        assert assemble_task.execute() == 0
        assert os.path.exists(
            os.path.join(tmp_trestle_dir, "system-security-plans", test_ssp_output)
        )
    else:
        with pytest.raises(
            TaskException, match=".*: SSP my-ssp does not exists in the index"
        ):
            assemble_task.execute()
