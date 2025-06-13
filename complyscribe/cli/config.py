# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""
ComplyScribe CLI configuration module.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, DirectoryPath, ValidationError


logger = logging.getLogger(__name__)


class ComplyScribeConfigError(Exception):
    """Custom error to better format pydantic exceptions.

    Example pydantic error dict: {'type': str, 'loc': tuple[str], 'msg': str, 'input': str}

    """

    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = list(map(self._format, errors))
        super().__init__(
            f"complyscribe config file contains {len(self.errors)} error(s)."
        )

    def _format(self, err: Dict[str, Any]) -> str:
        """Returns a formatted string with the error details."""
        msg = "Unable to load config."  # default message if we can't parse error

        if err.get("loc"):
            msg = f"Invalid config value for {err['loc'][0]}."
        if err.get("msg"):
            msg += f" {err['msg']}."  # Add error message details if present
        return msg

    def __str__(self) -> str:
        return "".join(self.errors)


class UpstreamsConfig(BaseModel):
    """Data model for upstream sources."""

    sources: List[str]
    include_models: List[str] = ["*"]
    exclude_models: List[str] = []
    skip_validation: bool = False


class ComplyScribeConfig(BaseModel):
    """Data model for complyscribe configuration."""

    repo_path: Optional[DirectoryPath] = None
    markdown_dir: Optional[str] = None
    committer_name: Optional[str] = None
    committer_email: Optional[str] = None
    commit_message: Optional[str] = None
    branch: Optional[str] = None
    ssp_index_file: Optional[str] = None
    upstreams: Optional[UpstreamsConfig] = None

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Returns a dict that can be cleanly written to a yaml file.

        This custom model serializer provides a cleaner dict that can
        be stored as a YAML file.  For example, we want to omit empty values
        from being written to the YAML config file, or we want paths to be
        written as strings, not posix path objects.

        Ex: instead of `ssp_index_file: None` appearing in the YAML, we
        just want to exclude it from the config file all together.  This
        produces a YAML config file that only includes values that have
        been set (or have a default we want to include).

        Values listed in IGNORED_VALUES will be skipped.
        """

        IGNORED_VALUES: List[Any] = [None, "None", []]

        config_dict: Dict[str, Any] = {
            "repo_path": str(self.repo_path),
            "markdown_dir": self.markdown_dir,
            "ssp_index_file": self.ssp_index_file,
            "committer_name": self.committer_name,
            "committer_email": self.committer_email,
            "commit_message": self.commit_message,
            "branch": self.branch,
        }

        if self.upstreams:
            upstreams = {
                "sources": self.upstreams.sources,
                "skip_validation": self.upstreams.skip_validation,
                "include_models": self.upstreams.include_models,
            }
            if self.upstreams.exclude_models:
                upstreams["exclude_models"] = self.upstreams.exclude_models

            config_dict.update({"upstreams": upstreams})

        # Filter out emtpy values to prevent them from appearing in the config
        return dict(
            filter(lambda item: item[1] not in IGNORED_VALUES, config_dict.items())
        )


def load_from_file(file_path: Path) -> Optional[ComplyScribeConfig]:
    """Load yaml file to complyscribe config object"""
    try:
        with open(file_path, "r") as config_file:
            config_yaml = yaml.safe_load(config_file)
            return ComplyScribeConfig(**config_yaml)
    except ValidationError as ex:
        raise ComplyScribeConfigError(ex.errors())
    except (FileNotFoundError, TypeError):
        logger.debug(f"No config file found at {file_path}")
        return None


def write_to_file(config: ComplyScribeConfig, file_path: Path) -> None:
    """Write config object to yaml file"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w") as config_file:
            yaml.dump(config.to_yaml_dict(), config_file)
    except ValidationError as ex:
        raise ComplyScribeConfigError(ex.errors())


def make_config(values: Optional[Dict[str, Any]] = None) -> ComplyScribeConfig:
    """Generates a new complyscribe config object"""
    try:
        if values:
            return ComplyScribeConfig.model_validate(values)
        else:
            return ComplyScribeConfig()
    except ValidationError as ex:
        raise ComplyScribeConfigError(ex.errors())


def update_config(
    config: ComplyScribeConfig, update: Dict[str, Any]
) -> ComplyScribeConfig:
    """Returns a new config object with specified updates."""
    try:
        return config.model_copy(update=update)
    except ValidationError as ex:
        raise ComplyScribeConfigError(ex.errors())
