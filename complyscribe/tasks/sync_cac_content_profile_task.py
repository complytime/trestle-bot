# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.
import logging
import pathlib
from typing import List, Set

from ssg.controls import Control, Policy  # type: ignore
from trestle.common.load_validate import load_validate_model_path

from complyscribe import const
from complyscribe.tasks.authored.profile import AuthoredProfile, CatalogControlResolver
from complyscribe.tasks.base_task import TaskBase, TaskException
from complyscribe.utils import load_controls_manager


logger = logging.getLogger(__name__)


class SyncCacContentProfileTask(TaskBase):
    def __init__(
        self,
        cac_content_root: str,
        product: str,
        oscal_catalog: str,
        policy_id: str,
        filter_by_level: List[str],
        authored_profile: AuthoredProfile,
    ):
        """
        Initializes the SyncCacContentProfileTask.

        Args:
            cac_content_root (str): The root directory of the CAC content repository that will
            access specified policy ids.
            product (str): The product name for the CAC content repository and Oscal Profile.
            oscal_catalog (str): The catalog used for extracting policy ids and
            Profile data.
            policy_id (str): The control file that includes control ids and their associated levels to
            create OSCAL Profiles.
            filter_by_level (list): The optional flag indicating a specific level to filter controls
            in policy ids.
            authored_profile (AuthoredProfile): Task that leverages oscal to author OSCAL Profiles
            in complyscribe.

        """
        self.cac_content_root = cac_content_root
        self.product = product
        self.oscal_catalog = oscal_catalog
        self.policy_id = policy_id
        self.filter_by_level = filter_by_level
        self.authored_profile = authored_profile
        working_dir = self.authored_profile.get_trestle_root()
        self.catalog_helper = CatalogControlResolver()
        super().__init__(working_dir=working_dir, model_filter=None)

    def get_control_ids_by_level(
        self, policy_id: str, filter_by_level: List[str]
    ) -> None:
        """
        Collecting control file product data by input of policy id and optional filter by level.
        This method gets default levels based on policy id and updates based on `filter_by_level`.
        The optional `filter_by_level` will be leveraged to produce OSCAL Profile for
        desired baseline level.

        Args:
            policy_id (str): Policy ID for sourcing control file.
            filter_by_level: List[str]: User indicated baseline level that will be used to
            filter control files.
        """
        control_manager = load_controls_manager(self.cac_content_root, self.product)

        # accessing control file within content/controls
        # ControlsManager() object can access methods for handling controls.

        policy: Policy = control_manager._get_policy(policy_id)
        levels: Set[str] = set()
        for level in policy.levels:
            levels.add(level.id)
        if filter_by_level:
            levels = levels.intersection(filter_by_level)
            if not levels:
                raise TaskException(
                    f"Specified levels {' '.join(filter_by_level)} do not match found "
                    + f"levels in {policy_id}."
                )

        if not levels:
            logger.debug("No levels detected. Create profile with all controls.")
            all_controls = control_manager.get_all_controls(policy_id)
            self.create_oscal_profile(all_controls, "all")
        else:
            logger.debug(f"Organizing controls based on levels {''.join(levels)}")
            for level in levels:
                eligible_controls = control_manager.get_all_controls_of_level(
                    policy_id, level
                )
                self.create_oscal_profile(eligible_controls, level)
                # make oscal profile
                logger.debug(f"Creating oscal profile using {eligible_controls}.")

    def create_oscal_profile(
        self,
        controls: List[Control],
        level: str,
    ) -> None:
        """
        Args:
            controls (List[Control]): List of controls to include in the profile based on level handling.
            level (str): used for updating title of OSCAL Profile based on filter_by_level user input.
        Returns:
            None. Follows through by using AuthoredProfile task to create or update OSCAL Profiles.
        """
        # Step 1: If filter by level returns eligible controls, create OSCAL profile with suffix
        # change based on level
        # Step 2: Fill in with control id, loading from eligible controls and all controls
        name_update = f"{self.product}-{self.policy_id}-{level}"
        # If the import_path is not valid then create new default
        # (based on tasks/authored/profile.py)
        # Otherwise the existing copy is held as a deep copy and will be accessible
        # even if changing profile inputs
        # Checks for importing model types (catalog, baseline)
        # AuthoredProfile will update based on existing_import
        # label properties for controls are a common way to store the control formatted for display.
        # This is the way they are represented in control files.
        resolved_controls: List[str] = list()
        for control in controls:
            control_id = self.catalog_helper.get_id(control.id)
            if not control_id:
                logger.debug(f"{control.id} not found in catalog")
                continue
            resolved_controls.append(control_id)

        if not resolved_controls:
            raise TaskException(
                f"No controls in {self.policy_id} found in {self.oscal_catalog}"
            )
        written = self.authored_profile.create_or_update(
            self.oscal_catalog, name_update, resolved_controls
        )
        if not written:
            logger.info(f"No update for profile {name_update}")

    def execute(self) -> int:
        # calling to get_control_ids _by_level and checking for valid control file name
        try:
            catalog = load_validate_model_path(
                pathlib.Path(self.working_dir), pathlib.Path(self.oscal_catalog)
            )
            self.catalog_helper.load(catalog)
            self.get_control_ids_by_level(self.policy_id, self.filter_by_level)
        except KeyError as e:
            raise TaskException(
                f"The control file associated with {self.policy_id} does not exist."
            ) from e
        return const.SUCCESS_EXIT_CODE
