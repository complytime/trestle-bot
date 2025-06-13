# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test for CSV Transformer."""

import csv
import pathlib
from typing import Dict, List

import pytest

from complyscribe.transformers.csv_transformer import (
    CSVBuilder,
    FromRulesCSVTransformer,
    ToRulesCSVTransformer,
)
from complyscribe.transformers.trestle_rule import TrestleRule


def test_csv_builder(test_rule: TrestleRule, tmp_trestle_dir: str) -> None:
    """Test CSV builder on a happy path"""

    csv_builder = CSVBuilder()
    csv_builder.add_row(test_rule)

    assert len(csv_builder._rows) == 1
    row = csv_builder._rows[0]
    assert row["Rule_Id"] == test_rule.name
    assert row["Rule_Description"] == test_rule.description
    assert row["Component_Title"] == test_rule.component.name
    assert row["Component_Type"] == test_rule.component.type
    assert row["Component_Description"] == test_rule.component.description
    assert row["Control_Id_List"] == "ac-1 ac-2"
    assert row["Parameter_Id"] == test_rule.parameter.name  # type: ignore
    assert row["Parameter_Description"] == test_rule.parameter.description  # type: ignore
    assert row["Parameter_Value_Alternatives"] == '{"default": "test", "test": "test"}'
    assert row["Parameter_Value_Default"] == test_rule.parameter.default_value  # type: ignore
    assert row["Profile_Description"] == test_rule.profile.description
    assert row["Profile_Source"] == test_rule.profile.href
    assert row["Check_Id"] == test_rule.check.name  # type: ignore
    assert row["Check_Description"] == test_rule.check.description  # type: ignore

    trestle_root = pathlib.Path(tmp_trestle_dir)
    tmp_csv_path = trestle_root.joinpath("test.csv")
    csv_builder.write_to_file(tmp_csv_path)

    assert tmp_csv_path.exists()

    first_row: List[str] = []
    with open(tmp_csv_path, "r", newline="") as csvfile:
        csv_reader = csv.reader(csvfile)
        first_row = next(csv_reader)

    for column in csv_builder._csv_columns.get_required_column_names():
        assert column in first_row


def test_validate_row_missing_keys(test_valid_csv_row: Dict[str, str]) -> None:
    """Test validate row with missing keys."""
    del test_valid_csv_row["Rule_Id"]
    csv_builder = CSVBuilder()
    with pytest.raises(RuntimeError, match="Row missing key: *"):
        csv_builder.validate_row(test_valid_csv_row)


def test_validate_row_extra_keys(test_valid_csv_row: Dict[str, str]) -> None:
    """Test validate row with extra keys."""
    test_valid_csv_row["extra_key"] = "extra_value"
    csv_builder = CSVBuilder()
    with pytest.raises(RuntimeError, match="Row has extra key: *"):
        csv_builder.validate_row(test_valid_csv_row)


def test_read_write_integration(test_rule: TrestleRule) -> None:
    """Test read/write integration."""
    from_rules_transformer = FromRulesCSVTransformer()
    to_rules_transformer = ToRulesCSVTransformer()

    csv_row_data = from_rules_transformer.transform(test_rule)
    read_rule = to_rules_transformer.transform(csv_row_data)

    assert read_rule == test_rule
