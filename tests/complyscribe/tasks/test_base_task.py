# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test workspace filtering logic."""

import pathlib
from typing import List

import pytest

from complyscribe.tasks.base_task import ModelFilter


@pytest.mark.parametrize(
    "skip_list, include_list, model_name, expected",
    [
        [["simplified_nist_catalog"], [], "simplified_nist_catalog", True],
        [[], ["simplified_nist_catalog"], "simplified_nist_catalog", False],
        [["simplified*"], ["*"], "simplified_nist_catalog", True],
        [
            ["simplified_nist_catalog"],
            ["simplified*"],
            "simplified_nist_profile",
            False,
        ],
        [[], [], "simplified_nist_catalog", True],
        [[], ["*"], "simplified_nist_catalog", False],
    ],
)
def test_is_skipped(
    skip_list: List[str], include_list: List[str], model_name: str, expected: str
) -> None:
    """Test skip logic."""
    model_path = pathlib.Path(model_name)
    model_filter = ModelFilter(skip_list, include_list)
    assert model_filter.is_skipped(model_path) == expected
