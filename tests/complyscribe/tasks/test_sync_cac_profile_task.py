# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.


"""Test for Trestle Bot sync CaC profile task."""

import pathlib

import pytest
import trestle.oscal.profile as prof
from trestle.common.model_utils import ModelUtils
from trestle.core.models.file_content_type import FileContentType

import tests.testutils as testutils
from complyscribe.tasks.authored.profile import AuthoredProfile
from complyscribe.tasks.base_task import TaskException
from complyscribe.tasks.sync_cac_content_profile_task import SyncCacContentProfileTask


test_cat = "simplified_nist_catalog"
test_product = "rhel8"
test_policy = "1234-levels"
# Note: data in test_content_dir is copied from content repo, PR:
# https://github.com/ComplianceAsCode/content/pull/12819
test_content_path = pathlib.Path("tests/data/content_dir").resolve()
test_content_dir = str(test_content_path)


def test_sync_cac_profile_task(tmp_trestle_dir: str) -> None:
    """Test sync cac profile."""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    _ = testutils.setup_for_catalog(trestle_root, test_cat, "")

    cat_path = trestle_root.joinpath("catalogs", test_cat, "catalog.json")
    test_prof = AuthoredProfile(tmp_trestle_dir)
    sync_cac_task = SyncCacContentProfileTask(
        product=test_product,
        authored_profile=test_prof,
        oscal_catalog=str(cat_path),
        filter_by_level=[],
        cac_content_root=test_content_dir,
        policy_id=test_policy,
    )
    return_code = sync_cac_task.execute()
    assert return_code == 0

    import_path = f"trestle://{cat_path}"

    low_title = f"{test_product}-{test_policy}-low"
    low, _ = ModelUtils.load_model_for_class(
        trestle_root, low_title, prof.Profile, FileContentType.JSON
    )
    assert low is not None
    assert low.metadata.title == low_title
    assert len(low.imports) == 1
    assert low.imports[0].href == import_path
    assert low.imports[0].include_controls is not None
    assert len(low.imports[0].include_controls[0].with_ids) == 2

    medium_title = f"{test_product}-{test_policy}-medium"
    medium, _ = ModelUtils.load_model_for_class(
        trestle_root, medium_title, prof.Profile, FileContentType.JSON
    )
    assert medium is not None
    assert medium.metadata.title == medium_title
    assert len(medium.imports) == 1
    assert medium.imports[0].href == import_path
    assert len(medium.imports[0].include_controls[0].with_ids) == 3

    high_title = f"{test_product}-{test_policy}-high"
    high, _ = ModelUtils.load_model_for_class(
        trestle_root, high_title, prof.Profile, FileContentType.JSON
    )
    assert high is not None
    assert high.metadata.title == high_title
    assert len(high.imports) == 1
    assert high.imports[0].href == import_path
    assert len(high.imports[0].include_controls[0].with_ids) == 4

    sync_cac_task = SyncCacContentProfileTask(
        product=test_product,
        authored_profile=test_prof,
        oscal_catalog=str(cat_path),
        filter_by_level=["high"],
        cac_content_root=test_content_dir,
        policy_id=test_policy,
    )
    return_code = sync_cac_task.execute()
    assert return_code == 0
    new_high, _ = ModelUtils.load_model_for_class(
        trestle_root, high_title, prof.Profile, FileContentType.JSON
    )
    assert high.metadata.last_modified == new_high.metadata.last_modified


def test_sync_cac_task_with_invalid_filter(tmp_trestle_dir: str) -> None:
    """Test sync cac tasks with invalid level filter."""
    trestle_root = pathlib.Path(tmp_trestle_dir)
    _ = testutils.setup_for_catalog(trestle_root, test_cat, "")
    cat_path = trestle_root.joinpath("catalogs", test_cat, "catalog.json")
    test_prof = AuthoredProfile(tmp_trestle_dir)
    sync_cac_task = SyncCacContentProfileTask(
        product=test_product,
        authored_profile=test_prof,
        oscal_catalog=str(cat_path),
        filter_by_level=["invalid"],
        cac_content_root=test_content_dir,
        policy_id=test_policy,
    )

    with pytest.raises(
        TaskException, match="Specified levels .* do not match found levels in .*"
    ):
        sync_cac_task.execute()
