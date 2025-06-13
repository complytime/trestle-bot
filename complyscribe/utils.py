# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Common utility functions."""
import os
import pathlib
import textwrap
from typing import Any, List

from ruamel.yaml import YAML, CommentedMap, CommentToken
from ruamel.yaml.scalarstring import LiteralScalarString
from ssg.controls import ControlsManager
from ssg.products import load_product_yaml, product_yaml_path


def populate_if_dict_field_not_exist(
    data: CommentedMap, field_name: str, default_value: Any
) -> Any:
    """
    Set field with default value if a CommentedMap field does not exist,
    if filed exists, this is a no-op
    return field value
    """
    if data.get(field_name) is None:
        # insert new filed to -2 position, avoid extra newline
        data.insert(len(data) - 1, field_name, default_value)

    return data[field_name]


def get_comments_from_yaml_data(yaml_data: Any) -> List[str]:
    """
    Get all comments from yaml_data, yaml_data must be read
    using ruamel.yaml library
    """
    comments: List[str] = []
    if not yaml_data.ca.items:
        return comments

    for _, comment_info in yaml_data.ca.items.items():
        for comment in comment_info:
            if not comment:
                continue

            if isinstance(comment, List):
                for c in comment:
                    if isinstance(c, CommentToken):
                        comments.append(c.value)
            elif isinstance(comment, CommentToken):
                comments.append(comment.value)

    return comments


def get_field_comment(data: CommentedMap, field_name: str) -> List[str]:
    """
    Get comments under specific field from data, data must be read
    using ruamel.yaml library
    """
    result = []
    comments = data.ca.items.get(field_name, [])

    for comment in comments:
        if not comment:
            continue

        if isinstance(comment, List):
            for c in comment:
                if isinstance(c, CommentToken):
                    result.append(c.value)
        elif isinstance(comment, CommentToken):
            result.append(comment.value)

    return result


def read_cac_yaml_ordered(file_path: pathlib.Path) -> Any:
    """
    Read data from CaC content yaml file while preserving the order
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    return yaml.load(file_path)


def write_cac_yaml_ordered(file_path: pathlib.Path, data: Any) -> None:
    """
    Serializes a Python object into a CaC content YAML stream, preserving the order.
    """
    yaml = YAML()
    yaml.indent(mapping=4, sequence=6, offset=4)
    yaml.dump(data, file_path)


def load_controls_manager(cac_content_root: str, product: str) -> ControlsManager:
    """
    Loads and initializes a ControlsManager instance.
    """
    product_yml_path = product_yaml_path(cac_content_root, product)
    product_yaml = load_product_yaml(product_yml_path)
    controls_dir = os.path.join(cac_content_root, "controls")
    control_mgr = ControlsManager(controls_dir, product_yaml)
    control_mgr.load()
    return control_mgr


def to_literal_scalar_string(s: str) -> LiteralScalarString:
    """
    Convert a string to a literal scalar string.
    """
    return LiteralScalarString(textwrap.dedent(s))
