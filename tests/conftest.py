# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Common test fixtures."""

import argparse
import pathlib
import tempfile
from typing import Any, Dict, Generator, Tuple, TypeVar

import pytest
from git.repo import Repo
from trestle.common.err import TrestleError
from trestle.core.commands.init import InitCmd

from complyscribe import const
from complyscribe.transformers.trestle_rule import (
    Check,
    ComponentInfo,
    Control,
    Parameter,
    Profile,
    TrestleRule,
)
from tests.testutils import clean, repo_setup


T = TypeVar("T")
YieldFixture = Generator[T, None, None]

_TEST_PREFIX = "complyscribe_tests"


@pytest.fixture(scope="function")
def tmp_repo() -> YieldFixture[Tuple[str, Repo]]:
    """Create a temporary git repository with an initialized trestle workspace root"""
    tmpdir = tempfile.mkdtemp(prefix=_TEST_PREFIX)
    tmp_path = pathlib.Path(tmpdir)
    repo: Repo = repo_setup(tmp_path)
    remote_url = "http://localhost:8080/test.git"
    repo.create_remote("origin", url=remote_url)
    yield tmpdir, repo
    clean(tmpdir, repo)


@pytest.fixture(scope="function")
def tmp_init_dir() -> YieldFixture[str]:
    tmpdir = tempfile.mkdtemp(prefix=_TEST_PREFIX)
    yield tmpdir
    clean(tmpdir)


@pytest.fixture(scope="function")
def tmp_trestle_dir() -> YieldFixture[str]:
    """Create an initialized temporary trestle directory"""
    with tempfile.TemporaryDirectory(prefix=_TEST_PREFIX) as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        try:
            args = argparse.Namespace(
                verbose=0,
                trestle_root=tmp_path,
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
        yield tmpdir


@pytest.fixture(scope="function")
def valid_rule_data() -> Dict[str, Any]:
    return {
        const.RULE_INFO_TAG: {
            const.NAME: "example_rule_1",
            const.DESCRIPTION: "My rule description for example rule 1",
            const.PROFILE: {
                const.DESCRIPTION: "Simple NIST Profile",
                const.HREF: "profiles/simplified_nist_profile/profile.json",
            },
            const.PARAMETER: {
                const.NAME: "prm_1",
                const.DESCRIPTION: "prm_1 description",
                const.ALTERNATIVE_VALUES: {
                    "default": "5%",
                    "5pc": "5%",
                    "10pc": "10%",
                    "15pc": "15%",
                    "20pc": "20%",
                },
                const.DEFAULT_VALUE: "5%",
            },
        }
    }


@pytest.fixture(scope="function")
def invalid_param_rule_data() -> Dict[str, Any]:
    return {
        const.RULE_INFO_TAG: {
            const.NAME: "example_rule_1",
            const.DESCRIPTION: "My rule description for example rule 1",
            const.PROFILE: {
                const.DESCRIPTION: "Simple NIST Profile",
                const.HREF: "profiles/simplified_nist_profile/profile.json",
                const.INCLUDE_CONTROLS: [{"id": "ac-1"}],
            },
            const.PARAMETER: {
                const.NAME: "prm_1",
                const.DESCRIPTION: "prm_1 description",
                const.ALTERNATIVE_VALUES: {
                    "5pc": "5%",
                    "10pc": "10%",
                    "15pc": "15%",
                    "20pc": "20%",
                },
                const.DEFAULT_VALUE: "5%",
            },
        },
        const.COMPONENT_INFO_TAG: {
            const.NAME: "Component 1",
            const.TYPE: "service",
            const.DESCRIPTION: "Component 1 description",
        },
    }


@pytest.fixture(scope="function")
def missing_key_rule_data() -> Dict[str, Any]:
    return {
        const.RULE_INFO_TAG: {
            const.DESCRIPTION: "My rule description for example rule 1",
            const.PROFILE: {
                const.DESCRIPTION: "Simple NIST Profile",
                const.HREF: "profiles/simplified_nist_profile/profile.json",
            },
            const.PARAMETER: {
                const.NAME: "prm_1",
                const.DESCRIPTION: "prm_1 description",
                const.ALTERNATIVE_VALUES: {
                    "default": "5%",
                    "5pc": "5%",
                    "10pc": "10%",
                    "15pc": "15%",
                    "20pc": "20%",
                },
                const.DEFAULT_VALUE: "5%",
            },
        }
    }


@pytest.fixture(scope="function")
def test_rule() -> TrestleRule:
    test_trestle_rule: TrestleRule = TrestleRule(
        name="test",
        description="test",
        component=ComponentInfo(name="test_comp", type="test", description="test"),
        parameter=Parameter(
            name="test",
            description="test",
            alternative_values={"default": "test", "test": "test"},
            default_value="test",
        ),
        check=Check(name="test_check", description="test check"),
        profile=Profile(
            description="test",
            href="test",
            include_controls=[Control(id="ac-1"), Control(id="ac-2")],
        ),
    )
    return test_trestle_rule


@pytest.fixture(scope="function")
def test_valid_csv_row() -> Dict[str, str]:
    return {
        "Rule_Id": "test",
        "Rule_Description": "test",
        "Component_Title": "test",
        "Component_Description": "test",
        "Component_Type": "test",
        "Control_Id_List": "ac-1",
        "Parameter_Id": "test",
        "Parameter_Description": "test",
        "Parameter_Value_Alternatives": "{}",
        "Parameter_Value_Default": "test",
        "Profile_Description": "test",
        "Profile_Source": "test",
        "Namespace": "test",
    }
