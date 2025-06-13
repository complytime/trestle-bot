# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""CSV Transformer for rule authoring."""

import csv
import json
import logging
import pathlib
from typing import Dict, List, Optional

import trestle.tasks.csv_to_oscal_cd as csv_to_oscal_cd
from trestle.common.const import TRESTLE_GENERIC_NS
from trestle.tasks.csv_to_oscal_cd import (
    CHECK_DESCRIPTION,
    CHECK_ID,
    COMPONENT_DESCRIPTION,
    COMPONENT_TITLE,
    COMPONENT_TYPE,
    CONTROL_ID_LIST,
    NAMESPACE,
    PARAMETER_DESCRIPTION,
    PARAMETER_ID,
    PARAMETER_VALUE_ALTERNATIVES,
    PARAMETER_VALUE_DEFAULT,
    PROFILE_DESCRIPTION,
    PROFILE_SOURCE,
    RULE_DESCRIPTION,
    RULE_ID,
    CsvColumn,
)

from complyscribe import const
from complyscribe.transformers.base_transformer import (
    FromRulesTransformer,
    ToRulesTransformer,
)
from complyscribe.transformers.trestle_rule import (
    Check,
    ComponentInfo,
    Control,
    Parameter,
    Profile,
    TrestleRule,
    get_default_rule,
)


logger = logging.getLogger(__name__)


class ToRulesCSVTransformer(ToRulesTransformer):
    """
    Interface for CSV transformer to Rules model.

    Notes: This will transform individual rows of CSV to and from a
    Trestle object with row compliance with the Trestle CSV requirements.
    """

    def __init__(self) -> None:
        """Initialize."""
        super().__init__()

    def transform(self, row: Dict[str, str]) -> TrestleRule:
        """Transform a CSV row to a TrestleRule object."""
        rule_info = self._extract_rule_info(row)
        profile = self._extract_profile(row)
        component_info = self._extract_component_info(row)
        parameter = self._extract_parameter(row)
        check = self._extract_check(row)

        return TrestleRule(
            name=rule_info[const.NAME],
            description=rule_info[const.DESCRIPTION],
            component=component_info,
            parameter=parameter,
            profile=profile,
            check=check,
        )

    def _extract_rule_info(self, row: Dict[str, str]) -> Dict[str, str]:
        """Extract rule information from a CSV row."""
        return {
            "name": row.get(csv_to_oscal_cd.RULE_ID, ""),
            "description": row.get(csv_to_oscal_cd.RULE_DESCRIPTION, ""),
        }

    def _extract_profile(self, row: Dict[str, str]) -> Profile:
        """Extract profile information from a CSV row."""
        controls_list = row.get(csv_to_oscal_cd.CONTROL_ID_LIST, "").split(" ")
        return Profile(
            description=row.get(csv_to_oscal_cd.PROFILE_DESCRIPTION, ""),
            href=row.get(csv_to_oscal_cd.PROFILE_SOURCE, ""),
            include_controls=[
                Control(id=control_id.strip()) for control_id in controls_list
            ],
        )

    def _extract_parameter(self, row: Dict[str, str]) -> Optional[Parameter]:
        """Extract parameter information from a CSV row."""
        parameter_name = row.get(csv_to_oscal_cd.PARAMETER_ID, None)
        if parameter_name:
            return Parameter(
                name=parameter_name,
                description=row.get(csv_to_oscal_cd.PARAMETER_DESCRIPTION, ""),
                alternative_values=json.loads(
                    row.get(csv_to_oscal_cd.PARAMETER_VALUE_ALTERNATIVES, "{}")
                ),
                default_value=row.get(csv_to_oscal_cd.PARAMETER_VALUE_DEFAULT, ""),
            )
        return None

    def _extract_check(self, row: Dict[str, str]) -> Optional[Check]:
        """Extract check information from a CSV row."""
        check_name = row.get(csv_to_oscal_cd.CHECK_ID, None)
        if check_name:
            return Check(
                name=check_name,
                description=row.get(csv_to_oscal_cd.CHECK_DESCRIPTION, ""),
            )
        return None

    def _extract_component_info(self, row: Dict[str, str]) -> ComponentInfo:
        """Extract component information from a CSV row."""
        return ComponentInfo(
            name=row.get(csv_to_oscal_cd.COMPONENT_TITLE, ""),
            type=row.get(csv_to_oscal_cd.COMPONENT_TYPE, ""),
            description=row.get(csv_to_oscal_cd.COMPONENT_DESCRIPTION, ""),
        )


class FromRulesCSVTransformer(FromRulesTransformer):
    """
    Interface for CSV transformer from Rules model.

    Notes: This will transform individual rows of CSV to and from a
    Trestle object with row compliance with the Trestle CSV requirements.
    """

    def __init__(self) -> None:
        """Initialize."""
        super().__init__()

    def transform(self, rule: TrestleRule) -> Dict[str, str]:
        """Transforms TrestleRule into a row of CSV."""
        rule_dict: Dict[str, str] = {
            RULE_ID: rule.name,
            RULE_DESCRIPTION: rule.description,
            NAMESPACE: TRESTLE_GENERIC_NS,
        }
        merged_dict = {
            **rule_dict,
            **self._add_profile(rule.profile),
            **self._add_component_info(rule.component),
        }
        if rule.parameter is not None:
            merged_dict.update(self._add_parameter(rule.parameter))
        if rule.check is not None:
            check: Dict[str, str] = {
                CHECK_ID: rule.check.name,
                CHECK_DESCRIPTION: rule.check.description,
            }
            merged_dict.update(check)
        return merged_dict

    def _add_profile(self, profile: Profile) -> Dict[str, str]:
        """Add a profile to the CSV Row."""
        controls_list: List[str] = [control.id for control in profile.include_controls]
        profile_dict: Dict[str, str] = {
            PROFILE_DESCRIPTION: profile.description,
            PROFILE_SOURCE: profile.href,
            CONTROL_ID_LIST: " ".join(controls_list),
        }
        return profile_dict

    def _add_parameter(self, parameter: Parameter) -> Dict[str, str]:
        """Add a parameter to the CSV Row."""
        parameter_dict: Dict[str, str] = {
            PARAMETER_ID: parameter.name,
            PARAMETER_DESCRIPTION: parameter.description,
            PARAMETER_VALUE_ALTERNATIVES: json.dumps(parameter.alternative_values),
            PARAMETER_VALUE_DEFAULT: parameter.default_value,
        }
        return parameter_dict

    def _add_component_info(self, component_info: ComponentInfo) -> Dict[str, str]:
        """Add a component info to the CSV Row."""
        comp_dict: Dict[str, str] = {
            COMPONENT_TITLE: component_info.name,
            COMPONENT_DESCRIPTION: component_info.description,
            COMPONENT_TYPE: component_info.type,
        }
        return comp_dict


class CSVBuilder:
    """Build a Trestle compliant CSV from a list of TrestleRules."""

    def __init__(self) -> None:
        """Initialize."""
        self._csv_columns: CsvColumn = CsvColumn()
        self._transformer: FromRulesTransformer = FromRulesCSVTransformer()
        self._rows: List[Dict[str, str]] = []
        self._fieldnames: List[str] = self._csv_columns.get_required_column_names()
        self._fieldnames.extend(self._csv_columns.get_optional_column_names())
        self._fieldnames.append(PARAMETER_ID)
        self._fieldnames.append(PARAMETER_DESCRIPTION)
        self._fieldnames.append(PARAMETER_VALUE_ALTERNATIVES)
        self._fieldnames.append(PARAMETER_VALUE_DEFAULT)

    @property
    def row_count(self) -> int:
        """Return the number of rows."""
        return len(self._rows)

    def add_row(self, rule: TrestleRule) -> None:
        """Add a row to the CSV."""
        row = self._transformer.transform(rule)
        self.validate_row(row)
        self._rows.append(row)

    def validate_row(self, row: Dict[str, str]) -> None:
        """Validate a row."""
        # Check that the row has all the required keys
        for key in self._csv_columns.get_required_column_names():
            if key not in row:
                raise RuntimeError(f"Row missing key: {key}")
        # Check that the row has no extra keys
        for key in row.keys():
            if key not in self._fieldnames:
                raise RuntimeError(f"Row has extra key: {key}")

    def write_to_file(self, filepath: pathlib.Path) -> None:
        """Write the CSV to file."""
        logger.debug(f"Writing CSV to {filepath}")
        with open(filepath, mode="w", newline="") as csv_file:
            # The trestle csv_to_oscal_cd task skips the header row and the
            # first row which is meant to have descriptions. We will just write a default right now.
            default_rule: TrestleRule = get_default_rule()
            example_row = self._transformer.transform(default_rule)

            writer = csv.DictWriter(csv_file, fieldnames=self._fieldnames)
            writer.writeheader()
            writer.writerow(example_row)
            for row in self._rows:
                writer.writerow(row)
