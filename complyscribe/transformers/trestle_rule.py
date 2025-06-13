# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""
Trestle Rule class with pydantic.

Note: Any validation here should be done in the pydantic model and
required for the rule to be valid.
"""


from typing import Dict, List, Optional, Tuple, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
)

from complyscribe import const


class Parameter(BaseModel):
    """Rule parameter model"""

    name: str
    description: str
    alternative_values: Dict[str, str] = Field(..., alias="alternative-values")
    default_value: str = Field(..., alias="default-value")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("default_value", mode="after")
    @classmethod
    def check_default_value(cls, value: str, info: ValidationInfo) -> str:
        """Check if default value is in the alternative values."""
        alternative_values: Dict[str, str] = info.data.get("alternative_values", {})
        if not alternative_values:
            raise ValueError("Alternative values must be provided")

        if value not in alternative_values.values():
            raise ValueError(
                f"Default value {value} must be in the alternative values {alternative_values.values()}"
            )

        # This is required to be listed as a value with a descriptive key and
        # optionally the default key
        default_value_alt = alternative_values.get(const.DEFAULT_KEY, "")
        if not default_value_alt:
            alternative_values[const.DEFAULT_KEY] = value
        else:
            if default_value_alt != value:
                raise ValueError(
                    f"Default value {value} must be in the alternative values {alternative_values}"
                    f" under the key {const.DEFAULT_KEY}"
                )

        return value


class Control(BaseModel):
    """
    Catalog control for rule association

    Note: This can be the control id or statement id.
    """

    id: str


class Profile(BaseModel):
    """Profile source for rule association."""

    description: str
    href: str
    include_controls: List[Control] = Field(..., alias="include-controls")

    model_config = ConfigDict(populate_by_name=True)


class ComponentInfo(BaseModel):
    """Rule component model."""

    name: str
    type: str
    description: str


class Check(BaseModel):
    """Check model for rule validation."""

    name: str
    description: str

    model_config = ConfigDict(populate_by_name=True)


class TrestleRule(BaseModel):
    """Represents a Trestle rule."""

    name: str
    description: str
    component: ComponentInfo
    profile: Profile
    check: Optional[Check] = Field(default=None)
    parameter: Optional[Parameter] = Field(default=None)


def get_default_rule() -> TrestleRule:
    """Create a default rule for template purposes."""
    return TrestleRule(
        name="example rule",
        description="example description",
        component=ComponentInfo(
            name="example component",
            type="service",
            description="example description",
        ),
        profile=Profile(
            description="example profile",
            href="example href",
            include_controls=[Control(id="example")],
        ),
    )


# Adapted from https://docs.pydantic.dev/latest/errors/errors/
def location_to_dot_separation(
    location: Tuple[Union[str, int], ...],
) -> str:  # pragma: no cover
    """Convert a tuple of strings and integers to a dot separated string."""
    path: str = ""
    for i, loc_value in enumerate(location):
        if isinstance(loc_value, str):
            if i > 0:
                path += "."
            path += loc_value
        elif isinstance(loc_value, int):
            path += f"[{loc_value}]"
        else:
            raise TypeError(f"Unexpected type {loc_value} in location tuple")
    return path


def convert_errors(errors: List[ValidationError]) -> str:
    """
    Convert pydantic validation errors into a formatted string.

    Note: All validations for rules should be done in the pydantic model and
    formatted through this function is for display purposes.
    """
    error_count: int = 0
    formatted_errors: List[str] = []

    for validation_error in errors:
        validation_errors = validation_error.errors()
        error_count += len(validation_errors)

        for error in validation_errors:
            location = location_to_dot_separation(error.get("loc"))
            msg = error.get("msg")
            typ = error.get("type")
            formatted_errors.append(
                f"Location: {location}, Type: {typ}, Message: {msg}"
            )

    pretty_errors = "\n".join(formatted_errors)
    return f"{error_count} error(s) found:\n{pretty_errors}"
