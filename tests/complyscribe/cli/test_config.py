# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.


"""Unit tests for CLI config module"""
import pathlib

import pytest
import yaml

from complyscribe.cli.config import (
    ComplyScribeConfig,
    ComplyScribeConfigError,
    UpstreamsConfig,
    load_from_file,
    make_config,
    write_to_file,
)


@pytest.fixture
def config_obj() -> ComplyScribeConfig:
    return ComplyScribeConfig(
        repo_path="/tmp",
        markdown_dir="markdown",
        upstreams=UpstreamsConfig(sources=["repo@main"]),
    )


def test_invalid_config_raises_errors() -> None:
    """Test create config with invalid directory to raise error."""

    with pytest.raises(ComplyScribeConfigError) as ex:
        _ = make_config(dict(repo_path="0"))

    assert (
        str(ex.value)
        == "Invalid config value for repo_path. Path does not point to a directory."
    )


def test_make_config_raises_no_errors(tmp_init_dir: str) -> None:
    """Test create a valid config object."""
    values = {
        "repo_path": tmp_init_dir,
        "markdown_dir": "markdown",
        "committer_name": "committer-name",
        "committer_email": "committer-email",
        "upstreams": {"sources": ["https://test@main"], "skip_validation": True},
    }
    config = make_config(values)
    assert isinstance(config, ComplyScribeConfig)
    assert config.upstreams is not None
    assert config.upstreams.sources == ["https://test@main"]
    assert config.upstreams.skip_validation is True
    assert config.repo_path == pathlib.Path(tmp_init_dir)
    assert config.markdown_dir == values["markdown_dir"]
    assert config.committer_name == values["committer_name"]
    assert config.committer_email == values["committer_email"]


def test_config_write_to_file(
    config_obj: ComplyScribeConfig, tmp_init_dir: str
) -> None:
    """Test config is written to yaml file."""
    filepath = pathlib.Path(tmp_init_dir).joinpath("config.yml")
    write_to_file(config_obj, filepath)
    with open(filepath, "r") as f:
        yaml_data = yaml.safe_load(f)

    assert yaml_data == config_obj.to_yaml_dict()


def test_config_load_from_file(
    config_obj: ComplyScribeConfig, tmp_init_dir: str
) -> None:
    """Test config is read from yaml file into config object."""
    filepath = pathlib.Path(tmp_init_dir).joinpath("config.yml")
    with filepath.open("w") as config_file:
        yaml.dump(config_obj.to_yaml_dict(), config_file)

    config = load_from_file(filepath)
    assert isinstance(config, ComplyScribeConfig)
    assert config == config_obj
