# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Common utility functions."""
from typing import Any, Dict


def populate_if_dict_field_not_exist(
    data: Dict[str, Any], field_name: str, default_value: Any
) -> Any:
    """
    Set field with default value if a dict field does not exist,
    if filed exists, this is a no-op
    return field value
    """
    if data.get(field_name) is None:
        data[field_name] = default_value

    return data[field_name]
