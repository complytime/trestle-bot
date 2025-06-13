# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test for Trestle Bot Authored Compdef."""

import pathlib
import re

import pytest
from trestle.common.err import TrestleError
from trestle.oscal.profile import Profile

from complyscribe.const import RULES_VIEW_DIR, YAML_EXTENSION
from complyscribe.tasks.authored.base_authored import AuthoredObjectException
from complyscribe.tasks.authored.compdef import (
    AuthoredComponentDefinition,
    FilterByProfile,
)
from complyscribe.transformers.yaml_transformer import ToRulesYAMLTransformer
from tests import testutils


test_prof = "simplified_nist_profile"
test_filter_prof = "simplified_filter_profile"
test_comp = "test_comp"


def test_create_new_default(tmp_trestle_dir: str) -> None:
    """Test creating new default component definition"""
    # Prepare the workspace
    trestle_root = pathlib.Path(tmp_trestle_dir)
    _ = testutils.setup_for_profile(trestle_root, test_prof, "")
    authored_comp = AuthoredComponentDefinition(tmp_trestle_dir)

    authored_comp.create_new_default(test_prof, test_comp, "test", "My desc", "service")

    rules_view_dir = trestle_root / RULES_VIEW_DIR
    assert rules_view_dir.exists()

    compdef_dir = rules_view_dir / test_comp
    assert compdef_dir.exists()

    comp_dir = compdef_dir / "test"
    assert comp_dir.exists()

    yaml_files = list(comp_dir.glob(f"*{YAML_EXTENSION}"))
    assert len(yaml_files) == 12

    rule_file = next(
        (file for file in yaml_files if re.search(r"ac-5", file.stem)), None
    )
    assert rule_file is not None

    # Read one of the files and check the content
    rule_path = pathlib.Path(rule_file)
    rule_stream = rule_path.read_text()

    transformer = ToRulesYAMLTransformer()
    rule = transformer.transform(rule_stream)

    assert rule.name == "rule-ac-5"
    assert rule.description == "Rule for ac-5"
    assert rule.component.name == "test"
    assert rule.component.type == "service"
    assert rule.component.description == "My desc"
    assert rule.parameter is None
    assert rule.profile.description == (
        "NIST Special Publication 800-53 Revision 5 MODERATE IMPACT \
BASELINE"
    )
    assert (
        rule.profile.href == "trestle://profiles/simplified_nist_profile/profile.json"
    )
    assert rule.profile.include_controls is not None
    assert len(rule.profile.include_controls) == 1
    assert rule.profile.include_controls[0].id == "ac-5"


def test_create_new_default_with_filter(tmp_trestle_dir: str) -> None:
    """Test creating new default component definition with filter"""

    # Prepare the workspace
    trestle_root = pathlib.Path(tmp_trestle_dir)
    _ = testutils.setup_for_profile(trestle_root, test_prof, "")
    testutils.load_from_json(trestle_root, test_filter_prof, test_filter_prof, Profile)
    authored_comp = AuthoredComponentDefinition(tmp_trestle_dir)

    filter_by_profile = FilterByProfile(trestle_root, test_filter_prof)

    authored_comp.create_new_default(
        test_prof, test_comp, "test", "My desc", "service", filter_by_profile
    )

    rules_view_dir = trestle_root / RULES_VIEW_DIR
    assert rules_view_dir.exists()

    compdef_dir = rules_view_dir / test_comp
    assert compdef_dir.exists()

    comp_dir = compdef_dir / "test"
    assert comp_dir.exists()

    # Verity that the number of rules YAML files has been reduced
    # from 12 to 7.
    yaml_files = list(comp_dir.glob(f"*{YAML_EXTENSION}"))
    assert len(yaml_files) == 7


def test_create_new_default_no_profile(tmp_trestle_dir: str) -> None:
    """Test creating new default component definition successfully"""
    # Prepare the workspace
    trestle_root = pathlib.Path(tmp_trestle_dir)
    _ = testutils.setup_for_compdef(trestle_root, test_comp, "")

    authored_comp = AuthoredComponentDefinition(tmp_trestle_dir)

    with pytest.raises(
        AuthoredObjectException, match="Profile fake does not exist in the workspace"
    ):
        authored_comp.create_new_default(
            "fake", test_comp, "test", "My desc", "service"
        )


def test_filter_by_profile_with_no_profile(tmp_trestle_dir: str) -> None:
    """Test creating a profile filter with a non-existent profile"""
    trestle_root = pathlib.Path(tmp_trestle_dir)

    with pytest.raises(
        TrestleError, match="Profile fake does not exist in the workspace"
    ):
        _ = FilterByProfile(trestle_root, "fake")
