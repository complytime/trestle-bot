# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""ComplyScribe functions for SSP authoring"""

import json
import logging
import os
import pathlib
from typing import Any, Dict, List, Optional

from trestle.common.const import SSP_MAIN_COMP_NAME
from trestle.common.err import TrestleError
from trestle.common.model_utils import ModelUtils
from trestle.core.commands.author.ssp import SSPFilter
from trestle.core.commands.common.return_codes import CmdReturnCodes
from trestle.core.repository import AgileAuthoring
from trestle.oscal.component import ComponentDefinition
from trestle.oscal.profile import Profile

from complyscribe.const import (
    COMPDEF_KEY_NAME,
    LEVERAGED_SSP_KEY_NAME,
    PROFILE_KEY_NAME,
    YAML_HEADER_PATH_KEY_NAME,
)
from complyscribe.tasks.authored.base_authored import (
    AuthoredObjectBase,
    AuthoredObjectException,
)


logger = logging.getLogger(__name__)


class SSPIndex:
    """
    Class for managing the SSP index that stores relationship data by Trestle name
    for SSPs.
    """

    def __init__(self, index_path: str) -> None:
        """
        Initialize ssp index.
        """
        self._index_path = index_path
        self.profile_by_ssp: Dict[str, str] = {}
        self.comps_by_ssp: Dict[str, List[str]] = {}
        self.leveraged_ssp_by_ssp: Dict[str, str] = {}
        self.yaml_header_by_ssp: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load the index from the index file"""
        # Try to load the current file. If it does not exist,
        # create an empty JSON file.
        try:
            with open(self._index_path, "r") as file:
                json_data = json.load(file)

            for ssp_name, ssp_info in json_data.items():
                try:
                    profile = ssp_info[PROFILE_KEY_NAME]
                    component_definitions = ssp_info[COMPDEF_KEY_NAME]
                except KeyError:
                    raise AuthoredObjectException(
                        f"SSP {ssp_name} entry is missing profile or component data"
                    )

                if profile is not None and component_definitions is not None:
                    self.profile_by_ssp[ssp_name] = profile
                    self.comps_by_ssp[ssp_name] = component_definitions

                if LEVERAGED_SSP_KEY_NAME in ssp_info:
                    self.leveraged_ssp_by_ssp[ssp_name] = ssp_info[
                        LEVERAGED_SSP_KEY_NAME
                    ]

                if YAML_HEADER_PATH_KEY_NAME in ssp_info:
                    self.yaml_header_by_ssp[ssp_name] = ssp_info[
                        YAML_HEADER_PATH_KEY_NAME
                    ]

        except FileNotFoundError:
            with open(self._index_path, "w") as file:
                json.dump({}, file)

    def reload(self) -> None:
        """Reload the index from the index file"""
        self.profile_by_ssp = {}
        self.comps_by_ssp = {}
        self.leveraged_ssp_by_ssp = {}
        self.yaml_header_by_ssp = {}
        self._load()

    def get_comps_by_ssp(self, ssp_name: str) -> List[str]:
        """Return list of compdefs associated with the SSP"""
        try:
            return self.comps_by_ssp[ssp_name]
        except KeyError:
            raise AuthoredObjectException(
                f"SSP {ssp_name} does not exists in the index"
            )

    def get_profile_by_ssp(self, ssp_name: str) -> str:
        """Return the profile associated with the SSP"""
        try:
            return self.profile_by_ssp[ssp_name]
        except KeyError:
            raise AuthoredObjectException(
                f"SSP {ssp_name} does not exists in the index"
            )

    def get_leveraged_by_ssp(self, ssp_name: str) -> Optional[str]:
        """Return the optional leveraged SSP used with the SSP"""
        try:
            return self.leveraged_ssp_by_ssp[ssp_name]
        except KeyError:
            logging.debug(f"key {ssp_name} does not exist")
            return None

    def get_yaml_header_by_ssp(self, ssp_name: str) -> Optional[str]:
        """Return the optional yaml header path used with the SSP"""
        try:
            return self.yaml_header_by_ssp[ssp_name]
        except KeyError:
            logging.debug(f"key {ssp_name} does not exist")
            return None

    def add_new_ssp(
        self,
        ssp_name: str,
        profile_name: str,
        compdefs: List[str],
        leveraged_ssp: Optional[str] = None,
        extra_yaml_header: Optional[str] = None,
    ) -> None:
        """Add a new ssp to the index"""
        self.profile_by_ssp[ssp_name] = profile_name
        self.comps_by_ssp[ssp_name] = compdefs
        if leveraged_ssp:
            self.leveraged_ssp_by_ssp[ssp_name] = leveraged_ssp
        if extra_yaml_header:
            self.yaml_header_by_ssp[ssp_name] = extra_yaml_header

    def write_out(self) -> None:
        """Write SSP index back to the index file"""
        data: Dict[str, Any] = {}

        for ssp_name, profile_name in self.profile_by_ssp.items():
            ssp_info: Dict[str, Any] = {
                PROFILE_KEY_NAME: profile_name,
                COMPDEF_KEY_NAME: self.comps_by_ssp[ssp_name],
                LEVERAGED_SSP_KEY_NAME: self.leveraged_ssp_by_ssp.get(ssp_name, None),
                YAML_HEADER_PATH_KEY_NAME: self.yaml_header_by_ssp.get(ssp_name, None),
            }

            data[ssp_name] = ssp_info

        with open(self._index_path, "w") as file:
            json.dump(data, file, indent=4)


class AuthoredSSP(AuthoredObjectBase):
    """
    Class for authoring OSCAL SSPs in automation
    """

    def __init__(self, trestle_root: str, ssp_index: SSPIndex) -> None:
        """
        Initialize authored ssps object.
        """
        self.ssp_index = ssp_index
        super().__init__(trestle_root)

    def assemble(self, markdown_path: str, version_tag: str = "") -> None:
        """Run assemble actions for ssp type at the provided path"""
        ssp = os.path.basename(markdown_path)

        comps = self.ssp_index.get_comps_by_ssp(ssp)
        component_str = ",".join(comps)

        trestle_root = pathlib.Path(self.get_trestle_root())
        authoring = AgileAuthoring(trestle_root)

        try:
            success = authoring.assemble_ssp_markdown(
                name=ssp,
                output=ssp,
                markdown_dir=markdown_path,
                regenerate=False,
                version=version_tag,
                compdefs=component_str,
            )
            if not success:
                raise AuthoredObjectException(
                    f"Unknown error occurred while assembling {ssp}"
                )
        except TrestleError as e:
            raise AuthoredObjectException(f"Trestle assemble failed for {ssp}: {e}")

    def regenerate(self, model_path: str, markdown_path: str) -> None:
        """Run regenerate actions for ssp type at the provided path"""

        ssp = os.path.basename(model_path)
        comps: List[str] = self.ssp_index.get_comps_by_ssp(ssp)
        component_str = ",".join(comps)

        profile = self.ssp_index.get_profile_by_ssp(ssp)

        leveraged_ssp = self.ssp_index.get_leveraged_by_ssp(ssp) or ""
        yaml_header = self.ssp_index.get_yaml_header_by_ssp(ssp) or ""

        trestle_root = pathlib.Path(self.get_trestle_root())
        authoring = AgileAuthoring(trestle_root)

        try:
            success = authoring.generate_ssp_markdown(
                output=os.path.join(markdown_path, ssp),
                force_overwrite=False,
                yaml_header=yaml_header,
                overwrite_header_values=False,
                compdefs=component_str,
                profile=profile,
                leveraged_ssp=leveraged_ssp,
                include_all_parts=True,
            )
            if not success:
                raise AuthoredObjectException(
                    f"Unknown error occurred while regenerating {ssp}"
                )
        except TrestleError as e:
            raise AuthoredObjectException(f"Trestle generate failed for {ssp}: {e}")

    def create_new_default(
        self,
        ssp_name: str,
        profile_name: str,
        compdefs: List[str],
        markdown_path: str,
        leveraged_ssp: Optional[str] = None,
        yaml_header: Optional[str] = None,
    ) -> None:
        """
        Create new ssp with index

        Args:
            ssp_name: Output name for ssp
            profile_name: Profile to import controls from
            compdefs: List of component definitions to import
            markdown_path: Top-level markdown path to write to
            leveraged_ssp: Optional leveraged ssp name for inheritance view editing
            yaml_header: Optional yaml header path for customizing the header

        Notes:
            This will generate SSP markdown and an index entry for a new managed SSP.
        """

        # Verify that the profile and compdefs exist
        trestle_root_str = self.get_trestle_root()
        trestle_root = pathlib.Path(trestle_root_str)
        profile_path = ModelUtils.get_model_path_for_name_and_class(
            trestle_root, profile_name, Profile
        )
        if profile_path is None:
            raise AuthoredObjectException(
                f"Profile {profile_name} does not exist in the workspace."
            )

        for compdef in compdefs:
            compdef_path = ModelUtils.get_model_path_for_name_and_class(
                trestle_root, compdef, ComponentDefinition
            )
            if compdef_path is None:
                raise AuthoredObjectException(
                    f"Component Definition {compdef} does not exist in the workspace."
                )

        self.ssp_index.add_new_ssp(
            ssp_name, profile_name, compdefs, leveraged_ssp, yaml_header
        )
        self.ssp_index.write_out()

        # Pass the ssp_name as the model base path.
        # We don't need the model dir for SSP generation.
        return self.regenerate(ssp_name, markdown_path)

    def create_new_with_filter(
        self,
        ssp_name: str,
        input_ssp: str,
        version: str = "",
        profile_name: str = "",
        main_comp_only: bool = False,
        compdefs: Optional[List[str]] = None,
        implementation_status: Optional[List[str]] = None,
        control_origination: Optional[List[str]] = None,
    ) -> None:
        """
        Create new ssp from an ssp with filters.

        Args:
            ssp_name: Output name for ssp
            input_ssp: Input ssp to filter
            version: Optional version to include in the output ssp
            profile_name:  Optional profile to filter by
            main_comp_only: Optional flag to include only the main component in the output ssp
            compdefs: Optional list of component definitions to filter by.
            The main component is added by default.
            implementation_status: Optional implementation status to filter by
            control_origination: Optional control origination to filter by

        Notes:
            The purpose of this function is to allow users to create a new SSP for reporting
            purposes without having to modify the source SSP.
        """

        # Create new ssp by filtering input ssp
        trestle_root = self.get_trestle_root()
        trestle_path = pathlib.Path(trestle_root)
        ssp_filter: SSPFilter = SSPFilter()

        components_title: Optional[List[str]] = None
        if compdefs:
            components_title = [SSP_MAIN_COMP_NAME]
            for comp_def_name in compdefs:
                comp_def, _ = ModelUtils.load_model_for_class(
                    trestle_path, comp_def_name, ComponentDefinition
                )
                components_title.extend(
                    [component.title for component in comp_def.components]
                )
        elif main_comp_only:
            components_title = [SSP_MAIN_COMP_NAME]

        try:
            exit_code = ssp_filter.filter_ssp(
                trestle_root=trestle_path,
                ssp_name=input_ssp,
                profile_name=profile_name,
                out_name=ssp_name,
                regenerate=True,
                components=components_title,
                version=version,
                implementation_status=implementation_status,
                control_origination=control_origination,
            )

            if exit_code != CmdReturnCodes.SUCCESS.value:
                raise AuthoredObjectException(
                    f"Unknown error occurred while filtering {input_ssp}"
                )
        except TrestleError as e:
            raise AuthoredObjectException(
                f"Trestle filtering failed for {input_ssp}: {e}"
            )
