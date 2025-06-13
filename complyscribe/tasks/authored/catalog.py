# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""ComplyScribe functions for catalog authoring"""

import os
import pathlib

from trestle.common.err import TrestleError
from trestle.core.repository import AgileAuthoring

from complyscribe.tasks.authored.base_authored import (
    AuthoredObjectBase,
    AuthoredObjectException,
)


class AuthoredCatalog(AuthoredObjectBase):
    """
    Class for authoring OSCAL catalogs in automation
    """

    def __init__(self, trestle_root: str) -> None:
        """
        Initialize authored catalog.
        """
        super().__init__(trestle_root)

    def assemble(self, markdown_path: str, version_tag: str = "") -> None:
        """Run assemble actions for catalog type at the provided path"""
        trestle_root = pathlib.Path(self.get_trestle_root())
        catalog = os.path.basename(markdown_path)
        authoring = AgileAuthoring(trestle_root)
        try:
            success = authoring.assemble_catalog_markdown(
                name=catalog,
                output=catalog,
                markdown_dir=markdown_path,
                set_parameters=True,
                regenerate=False,
                version=version_tag,
            )
            if not success:
                raise AuthoredObjectException(
                    f"Unknown error occurred while assembling {catalog}"
                )
        except TrestleError as e:
            raise AuthoredObjectException(f"Trestle assemble failed for {catalog}: {e}")

    def regenerate(self, model_path: str, markdown_path: str) -> None:
        """Run assemble actions for catalog type at the provided path"""
        trestle_root = pathlib.Path(self.get_trestle_root())
        authoring = AgileAuthoring(trestle_root)

        catalog = os.path.basename(model_path)
        try:
            success = authoring.generate_catalog_markdown(
                name=catalog,
                output=os.path.join(markdown_path, catalog),
                force_overwrite=False,
                yaml_header=None,
                overwrite_header_values=False,
            )
            if not success:
                raise AuthoredObjectException(
                    f"Unknown error occurred while regenerating {catalog}"
                )
        except TrestleError as e:
            raise AuthoredObjectException(f"Trestle generate failed for {catalog}: {e}")
