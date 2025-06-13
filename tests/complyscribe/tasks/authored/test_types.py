# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test author types for ComplyScribe"""

from unittest.mock import Mock

import pytest

from complyscribe.tasks.authored import types
from complyscribe.tasks.authored.base_authored import (
    AuthoredObjectBase,
    AuthoredObjectException,
)
from complyscribe.tasks.authored.catalog import AuthoredCatalog
from complyscribe.tasks.authored.compdef import AuthoredComponentDefinition
from complyscribe.tasks.authored.profile import AuthoredProfile
from complyscribe.tasks.authored.ssp import AuthoredSSP
from tests import testutils


test_prof = "simplified_nist_profile"
test_comp = "test_comp"
test_ssp_output = "test-ssp"
markdown_dir = "md_ssp"


def test_get_authored_catalog(tmp_trestle_dir: str) -> None:
    """Test get authored type for catalogs"""

    authored_object: AuthoredObjectBase = types.get_authored_object(
        types.AuthoredType.CATALOG.value, tmp_trestle_dir, ""
    )

    assert authored_object.get_trestle_root() == tmp_trestle_dir
    assert isinstance(authored_object, AuthoredCatalog)


def test_get_authored_profile(tmp_trestle_dir: str) -> None:
    """Test get authored type for profiles"""

    authored_object: AuthoredObjectBase = types.get_authored_object(
        types.AuthoredType.PROFILE.value, tmp_trestle_dir, ""
    )

    assert authored_object.get_trestle_root() == tmp_trestle_dir
    assert isinstance(authored_object, AuthoredProfile)


def test_get_authored_compdef(tmp_trestle_dir: str) -> None:
    """Test get authored type for compdefs"""

    authored_object: AuthoredObjectBase = types.get_authored_object(
        types.AuthoredType.COMPDEF.value, tmp_trestle_dir, ""
    )

    assert authored_object.get_trestle_root() == tmp_trestle_dir
    assert isinstance(authored_object, AuthoredComponentDefinition)


def test_get_authored_ssp(tmp_trestle_dir: str) -> None:
    """Test get authored type for ssp"""
    with pytest.raises(
        FileNotFoundError,
    ):
        _ = types.get_authored_object(types.AuthoredType.SSP.value, tmp_trestle_dir, "")

    # Test with a valid ssp index
    authored_object: AuthoredObjectBase = types.get_authored_object(
        types.AuthoredType.SSP.value, tmp_trestle_dir, str(testutils.TEST_SSP_INDEX)
    )

    assert authored_object.get_trestle_root() == tmp_trestle_dir
    assert isinstance(authored_object, AuthoredSSP)


def test_invalid_authored_type(tmp_trestle_dir: str) -> None:
    """Test triggering an error with an invalid type"""
    with pytest.raises(
        AuthoredObjectException,
        match="Invalid authored type fake",
    ):
        _ = types.get_authored_object("fake", tmp_trestle_dir, "")


def test_get_model_dir_with_invalid_type() -> None:
    """Test triggering an error with an invalid type when getting the model dir."""
    with pytest.raises(
        AuthoredObjectException,
        match="Invalid authored object <class 'unittest.mock.Mock'>",
    ):
        mock = Mock(spec=AuthoredObjectBase)
        _ = types.get_trestle_model_dir(mock)
