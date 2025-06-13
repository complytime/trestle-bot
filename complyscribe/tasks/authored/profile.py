# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""ComplyScribe functions for profile authoring"""

import os
import pathlib
import shutil
from copy import deepcopy
from typing import Dict, List, Optional, Set, Type

import trestle.core.generators as gens
import trestle.oscal.catalog as cat
import trestle.oscal.profile as prof
from trestle.common import const
from trestle.common.common_types import TypeWithParts
from trestle.common.err import TrestleError, TrestleNotFoundError
from trestle.common.load_validate import (
    load_validate_model_name,
    load_validate_model_path,
)
from trestle.common.model_utils import ModelUtils
from trestle.core.catalog.catalog_interface import CatalogInterface
from trestle.core.control_interface import ControlInterface
from trestle.core.models.file_content_type import FileContentType
from trestle.core.repository import AgileAuthoring
from trestle.oscal.common import IncludeAll

from complyscribe.tasks.authored.base_authored import (
    AuthoredObjectBase,
    AuthoredObjectException,
)


class AuthoredProfile(AuthoredObjectBase):
    """
    Class for authoring OSCAL Profiles in automation
    """

    def __init__(self, trestle_root: str) -> None:
        """
        Initialize authored profiles object.
        """
        super().__init__(trestle_root)

    def assemble(self, markdown_path: str, version_tag: str = "") -> None:
        """Run assemble actions for profile type at the provided path"""
        trestle_root = pathlib.Path(self.get_trestle_root())
        authoring = AgileAuthoring(trestle_root)

        profile = os.path.basename(markdown_path)

        try:
            success = authoring.assemble_profile_markdown(
                name=profile,
                output=profile,
                markdown_dir=markdown_path,
                set_parameters=True,
                regenerate=False,
                version=version_tag,
                sections=None,
                required_sections=None,
                allowed_sections=None,
            )
            if not success:
                raise AuthoredObjectException(
                    f"Unknown error occurred while assembling {profile}"
                )
        except TrestleError as e:
            raise AuthoredObjectException(f"Trestle assemble failed for {profile}: {e}")

    def regenerate(self, model_path: str, markdown_path: str) -> None:
        """Run assemble actions for profile type at the provided path"""
        trestle_root = pathlib.Path(self.get_trestle_root())
        authoring = AgileAuthoring(trestle_root)

        profile = os.path.basename(model_path)
        try:
            success = authoring.generate_profile_markdown(
                name=profile,
                output=os.path.join(markdown_path, profile),
                force_overwrite=False,
                yaml_header=None,
                overwrite_header_values=False,
                sections=None,
                required_sections=None,
            )
            if not success:
                raise AuthoredObjectException(
                    f"Unknown error occurred while regenerating {profile}"
                )
        except TrestleError as e:
            raise AuthoredObjectException(f"Trestle generate failed for {profile}: {e}")

    def create_or_update(
        self, import_path: str, profile_name: str, with_ids: Optional[List[str]] = None
    ) -> bool:
        """
        Create or update a profile in place with data.

        Args:
            import_path: Reference to imported catalog or profile (ex. catalogs/example/catalog.json)
            profile_name: Output profile name
            with_ids: Optionally include controls ids

        Returns:
            A boolean values to denote whether the profile was written out.
        """
        trestle_root: pathlib.Path = pathlib.Path(self.get_trestle_root())
        profile_path = ModelUtils.get_model_path_for_name_and_class(
            trestle_root,
            profile_name,
            prof.Profile,
            FileContentType.JSON,
        )

        if not profile_path.exists():
            self.create_new_default(
                import_path=import_path, profile_name=profile_name, with_ids=with_ids
            )
            return True
        else:
            profile: prof.Profile = load_validate_model_path(trestle_root, profile_path)
            existing_profile = deepcopy(profile)
            profile.metadata.title = profile_name
            trestle_import_path = const.TRESTLE_HREF_HEADING + import_path
            existing_import = next(
                (imp for imp in profile.imports if imp.href == trestle_import_path),
                None,
            )
            if not existing_import:
                existing_import = gens.generate_sample_model(prof.Import)

            AuthoredProfile._update_imports(
                import_path=trestle_import_path,
                profile_import=existing_import,
                include_controls=with_ids,
            )

            if not ModelUtils.models_are_equivalent(existing_profile, profile):
                ModelUtils.update_last_modified(profile)
                profile.oscal_write(path=profile_path)
                return True
        return False

    def create_new_default(
        self, import_path: str, profile_name: str, with_ids: Optional[List[str]] = None
    ) -> None:
        """
        Create new profile with default info

        Args:
            import_path: Reference to imported catalog or profile (ex. catalogs/example/catalog.json)
            profile_name: Output profile name
            with_ids: Optionally include controls ids

        Notes:
            This will attempt to read the output profile at the current name
            and modify it. If one does not exist, a new profile will be created
            with the specified name. The provided import will overwrite the first
            import in the list.

        """
        trestle_root: pathlib.Path = pathlib.Path(self.get_trestle_root())

        profile_data: Type[prof.Profile]
        existing_prof_data_path: Optional[pathlib.Path]

        # Attempt to load the existing profile if not found create a new instance
        try:
            profile_data, prof_data_path = load_validate_model_name(
                trestle_root,
                profile_name,
                prof.Profile,
                FileContentType.JSON,
            )
            existing_prof_data_path = pathlib.Path(prof_data_path)
        except TrestleNotFoundError:
            profile_data = gens.generate_sample_model(prof.Profile)  # type: ignore
            existing_prof_data_path = ModelUtils.get_model_path_for_name_and_class(
                trestle_root,
                profile_name,
                prof.Profile,
                FileContentType.JSON,
            )
            if existing_prof_data_path is None:
                raise AuthoredObjectException(
                    f"Error defining workspace name for profile {profile_name}"
                )

        profile_data.metadata.title = profile_name
        # Overwrite imports
        profile_import = gens.generate_sample_model(prof.Import)
        trestle_import_path = const.TRESTLE_HREF_HEADING + import_path
        AuthoredProfile._update_imports(
            import_path=trestle_import_path,
            profile_import=profile_import,
            include_controls=with_ids,
        )
        profile_data.imports = [profile_import]

        # Set up default values for merge settings.
        merge_object: prof.Merge = gens.generate_sample_model(prof.Merge)
        combine_object: prof.Combine = gens.generate_sample_model(prof.Combine)
        combine_object.method = prof.CombinationMethodValidValues.merge
        merge_object.combine = combine_object
        merge_object.as_is = True

        profile_data.merge = merge_object

        profile_path = pathlib.Path(existing_prof_data_path)
        if profile_path.parent.exists():
            shutil.rmtree(str(profile_path.parent))

        ModelUtils.update_last_modified(profile_data)  # type: ignore

        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_data.oscal_write(path=profile_path)  # type: ignore

    @staticmethod
    def _update_imports(
        import_path: str,
        profile_import: prof.Import,
        include_controls: Optional[List[str]] = None,
    ) -> None:
        profile_import.href = import_path
        if not include_controls:
            profile_import.include_all = gens.generate_sample_model(IncludeAll)
        else:
            profile_import.include_controls = [
                prof.SelectControl(with_ids=sorted(include_controls))
            ]
        return profile_import


class CatalogControlResolver:
    """Helper class find control ids in OSCAL catalogs based on the label property."""

    def __init__(self) -> None:
        """Initialize."""
        self.all_controls: Set[str] = set()
        self._controls_by_label: Dict[str, str] = dict()

    def load(self, catalog: cat.Catalog) -> None:
        """Load the catalog."""
        for control in CatalogInterface(catalog).get_all_controls_from_dict():
            self.all_controls.add(control.id)
            label = ControlInterface.get_label(control)
            if label:
                self._controls_by_label[label] = control.id
                self._handle_parts(control)

    def _handle_parts(
        self,
        control: TypeWithParts,
    ) -> None:
        """Handle parts of a control."""
        if control.parts:
            for part in control.parts:
                if not part.id:
                    continue
                self.all_controls.add(part.id)
                label = ControlInterface.get_label(part)
                # Avoiding key collision here. The higher level control object will take
                # precedence.
                if label and label not in self._controls_by_label.keys():
                    self._controls_by_label[label] = part.id
                self._handle_parts(part)

    def get_id(self, control_label: str) -> Optional[str]:
        """
        Validate that the control id exists in the catalog and return the id

        Args:
            control_label (str): values of the control id or label to search for

        Returns:
            The control-id if found, else None.
        """
        if control_label in self._controls_by_label.keys():
            return self._controls_by_label.get(control_label)
        elif control_label in self.all_controls:
            # This means what was passed is already a valid
            # control id.
            return control_label
        return None
