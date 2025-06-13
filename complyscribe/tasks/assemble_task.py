# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""ComplyScribe Assembly Tasks"""

import logging
import os
import pathlib
from typing import Optional

from complyscribe import const
from complyscribe.tasks.authored.base_authored import (
    AuthoredObjectBase,
    AuthoredObjectException,
)
from complyscribe.tasks.base_task import ModelFilter, TaskBase, TaskException


logger = logging.getLogger(__name__)


class AssembleTask(TaskBase):
    """
    Assemble Markdown into OSCAL content
    """

    def __init__(
        self,
        authored_object: AuthoredObjectBase,
        markdown_dir: str,
        version: str = "",
        model_filter: Optional[ModelFilter] = None,
    ) -> None:
        """
        Initialize assemble task.

        Args:
            authored_object: Object can assembled OSCAL content into JSON
            markdown_dir: Location of directory to write Markdown in
            model_filter: Optional filter to apply to the task to include or exclude models
            from processing
        """

        self._authored_object = authored_object
        self._markdown_dir = markdown_dir
        self._version = version
        working_dir = self._authored_object.get_trestle_root()
        super().__init__(working_dir, model_filter)

    def execute(self) -> int:
        """Execute task"""
        return self._assemble()

    def _assemble(self) -> int:
        """
        Assemble all objects in markdown directory

        Returns:
          0 on success, raises an exception if not successful
        """
        search_path = os.path.join(self.working_dir, self._markdown_dir)
        if not os.path.exists(search_path):
            raise TaskException(f"Markdown directory {search_path} does not exist")

        for model in self.iterate_models(pathlib.Path(search_path)):
            # Construct model path from markdown path. AuthoredObject already has
            # the working dir data as part of object construction.
            logger.info(f"Assembling model {model}")
            model_base_name = os.path.basename(model)
            model_path = os.path.join(self._markdown_dir, model_base_name)
            try:
                self._authored_object.assemble(
                    markdown_path=model_path, version_tag=self._version
                )
            except AuthoredObjectException as e:
                raise TaskException(f"Assemble task failed for model {model_path}: {e}")

        return const.SUCCESS_EXIT_CODE
