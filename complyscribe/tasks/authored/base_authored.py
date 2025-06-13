# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""ComplyScribe base authored object"""

import os
import pathlib
from abc import ABC, abstractmethod

from trestle.common.file_utils import is_valid_project_root


class AuthoredObjectException(Exception):
    """An error during object authoring"""


class AuthoredObjectBase(ABC):
    """
    Abstract base class for OSCAL objects that are authored.
    """

    def __init__(self, trestle_root: str) -> None:
        """Initialize task base and store trestle root path"""
        if not os.path.exists(trestle_root):
            raise AuthoredObjectException(f"Root path {trestle_root} does not exist")

        if not is_valid_project_root(pathlib.Path(trestle_root)):
            raise AuthoredObjectException(
                f"Root path {trestle_root} is not a valid trestle project root"
            )

        self._trestle_root = trestle_root

    def get_trestle_root(self) -> str:
        """Return the trestle root directory"""
        return self._trestle_root

    @abstractmethod
    def assemble(self, markdown_path: str, version_tag: str = "") -> None:
        """Execute assemble for model path"""

    @abstractmethod
    def regenerate(self, model_path: str, markdown_path: str) -> None:
        """Execute regeneration for model path"""
