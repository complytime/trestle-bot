# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""ComplyScribe Regenerate Tasks"""

import logging
import os
import pathlib
from typing import Optional

from complyscribe import const
from complyscribe.tasks.authored import types
from complyscribe.tasks.authored.base_authored import (
    AuthoredObjectBase,
    AuthoredObjectException,
)
from complyscribe.tasks.base_task import ModelFilter, TaskBase, TaskException


logger = logging.getLogger(__name__)


class RegenerateTask(TaskBase):
    """
    Regenerate Trestle Markdown from OSCAL JSON content changes
    """

    def __init__(
        self,
        authored_object: AuthoredObjectBase,
        markdown_dir: str,
        model_filter: Optional[ModelFilter] = None,
    ) -> None:
        """
        Initialize regenerate task.

        Args:
            authored_object: Object that can regenerate Markdown content from JSON
            markdown_dir: Location of directory to write Markdown in
            model_filter: Optional filter to apply to the task to include or exclude models
            from processing.
        """

        self._authored_object = authored_object
        self._markdown_dir = markdown_dir
        working_dir = self._authored_object.get_trestle_root()
        super().__init__(working_dir, model_filter)

    def execute(self) -> int:
        """Execute task"""
        return self._regenerate()

    def _regenerate(self) -> int:
        """
        Regenerate all objects in model JSON directory

        Returns:
         0 on success, raises an exception if not successful
        """
        model_dir = types.get_trestle_model_dir(self._authored_object)

        search_path = os.path.join(self.working_dir, model_dir)
        for model in self.iterate_models(pathlib.Path(search_path)):
            logger.info(f"Regenerating model {model}")
            model_base_name = os.path.basename(model)
            model_path = os.path.join(model_dir, model_base_name)

            try:
                self._authored_object.regenerate(
                    model_path=model_path, markdown_path=self._markdown_dir
                )
            except AuthoredObjectException as e:
                raise TaskException(f"Regenerate task failed for model {model}: {e}")

        return const.SUCCESS_EXIT_CODE
