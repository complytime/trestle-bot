# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""ComplyScribe base task for extensible bot pre-tasks"""

import fnmatch
import pathlib
from abc import ABC, abstractmethod
from typing import Callable, Iterable, List, Optional

from trestle.common import const
from trestle.common.file_utils import is_hidden


class TaskException(Exception):
    """An error during task execution"""


class ModelFilter:
    """
    Filter models based on include and exclude patterns.

    Args:
        skip_patterns: List of glob patterns to exclude from processing.
        include_patterns: List of glob patterns to include in processing.

    Note: If a model is in both the include and exclude lists, it will be excluded.
    The skip list is applied first.
    """

    def __init__(self, skip_patterns: List[str], include_patterns: List[str]):
        self._include_model_list: List[str] = include_patterns
        self._skip_model_list: List[str] = [const.TRESTLE_KEEP_FILE] + skip_patterns

    def is_skipped(self, model_path: pathlib.Path) -> bool:
        """Check if the model is skipped through include or skip lists."""
        if any(
            fnmatch.fnmatch(model_path.name, pattern)
            for pattern in self._skip_model_list
        ):
            return True
        elif any(
            fnmatch.fnmatch(model_path.name, pattern)
            for pattern in self._include_model_list
        ):
            return False
        else:
            return True


class TaskBase(ABC):
    """
    Abstract base class for tasks with a work directory.
    """

    def __init__(self, working_dir: str, model_filter: Optional[ModelFilter]) -> None:
        """
        Initialize base task.

        Args:
            working_dir: Working directory to complete operations in.
            model_filter: Model filter to use for this task.
        """
        self._working_dir = working_dir
        self.filter: Optional[ModelFilter] = model_filter

    @property
    def working_dir(self) -> str:
        """Return the working directory"""
        return self._working_dir

    def iterate_models(self, directory_path: pathlib.Path) -> Iterable[pathlib.Path]:
        """Iterate over the models in the working directory"""
        filtered_paths: Iterable[pathlib.Path]

        if self.filter is not None:
            is_skipped: Callable[[pathlib.Path], bool] = self.filter.is_skipped
            filtered_paths = list(
                filter(
                    lambda p: not is_skipped(p) and (not is_hidden(p) or p.is_dir()),
                    pathlib.Path.iterdir(directory_path),
                )
            )
        else:
            filtered_paths = list(
                filter(
                    lambda p: not is_hidden(p) or p.is_dir(),
                    pathlib.Path.iterdir(directory_path),
                )
            )

        return filtered_paths.__iter__()

    @abstractmethod
    def execute(self) -> int:
        """Execute the task and return the exit code"""
        pass
