import logging
import os
import pathlib
from typing import Any, Dict, List, Set, Tuple

from ssg.controls import ControlsManager, Policy
from trestle.common.const import MODEL_TYPE_PROFILE
from trestle.common.model_utils import ModelUtils
from trestle.core.profile_resolver import ProfileResolver
from trestle.oscal.profile import Profile

from complyscribe.const import SUCCESS_EXIT_CODE
from complyscribe.tasks.authored.profile import CatalogControlResolver
from complyscribe.tasks.base_task import TaskBase
from complyscribe.utils import (
    load_controls_manager,
    read_cac_yaml_ordered,
    write_cac_yaml_ordered,
)


logger = logging.getLogger(__name__)


class SyncOscalProfileTask(TaskBase):
    """Sync OSCAL profile to cac content task."""

    def __init__(
        self,
        cac_content_root: pathlib.Path,
        working_dir: str,
        cac_policy_id: str,
        product: str,
    ) -> None:
        """Initialize task."""
        super().__init__(working_dir, None)
        self.cac_content_root = cac_content_root
        self.cac_policy_id = cac_policy_id
        self.product = product
        self.catalog_helper = CatalogControlResolver()
        self.control_dir = os.path.join(self.cac_content_root, "controls")
        self.cac_control_map: Dict[str, Dict[str, Any]] = dict()
        self.cac_to_oscal_map: Dict[str, str] = dict()
        self.level_with_ancestors: Dict[str, List[str]] = dict()

    def get_oscal_profiles(
        self, trestle_root: pathlib.Path
    ) -> List[Tuple[Profile, pathlib.Path]]:
        """
        Get OSCAL profiles information according to policy id.
        """
        res = []
        dir_name = ModelUtils.model_type_to_model_dir(MODEL_TYPE_PROFILE)
        for d in pathlib.Path(trestle_root.joinpath(dir_name)).iterdir():
            if f"{self.product}-{self.cac_policy_id}" in d.name:
                res.append(
                    ModelUtils.load_model_for_type(
                        trestle_root, MODEL_TYPE_PROFILE, d.name
                    )
                )

        return res

    def get_cac_id_control_map(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Get cac control-id:control-object map from cac control file data
        """
        res = {}
        for control in data.get("controls", []):
            if control.get("controls"):
                res.update(self.get_cac_id_control_map(control))
            res[control["id"]] = control

        return res

    def get_cac_to_oscal_map(self, control_mgr: ControlsManager) -> Dict[str, str]:
        """
        Get cac_control_id to oscal_control_id map
        """
        cac_control_id_to_oscal_control_id_map = {}
        for control in control_mgr.get_all_controls(self.cac_policy_id):
            oscal_control_id = self.catalog_helper.get_id(control.id)
            if oscal_control_id:
                cac_control_id_to_oscal_control_id_map[oscal_control_id] = control.id

        return cac_control_id_to_oscal_control_id_map

    def load_all_controls(self, profiles: List[Tuple[Profile, pathlib.Path]]) -> None:
        """
        Load all controls from OSCAL profiles
        """
        for _, profile_path in profiles:
            profile_resolver = ProfileResolver()
            resolved_catalog = profile_resolver.get_resolved_profile_catalog(
                pathlib.Path(self.working_dir),
                os.path.join(profile_path, "profile.json"),
                block_params=False,
                params_format="[.]",
                show_value_warnings=True,
            )
            self.catalog_helper.load(resolved_catalog)

    def get_level_with_ancestors(
        self, control_mgr: ControlsManager
    ) -> Dict[str, List[str]]:
        """
        Get CaC control file level with ancestors.
        Ancestors list is ordered by level rank, desc
        """
        p: Policy = control_mgr._get_policy(self.cac_policy_id)
        level_with_ancestors = {}
        for level in p.levels:
            level_with_ancestors[level.id] = [
                level.id for level in p.get_level_with_ancestors_sequence(level.id)
            ]

        return level_with_ancestors

    def process_level(self, level: str, add: Set[str], remove: Set[str]) -> None:
        highest_level_chain: List[str] = []
        for _, ancestors_sequence in self.level_with_ancestors.items():
            if (
                level in ancestors_sequence
                and len(ancestors_sequence) > 1
                and len(ancestors_sequence) > len(highest_level_chain)
            ):
                highest_level_chain = ancestors_sequence

        # add level to CaC control
        for add_id in add:
            cac_control = self.cac_control_map[self.cac_to_oscal_map[add_id]]
            cac_control_levels = cac_control["levels"]

            if level not in cac_control_levels:
                cac_control_levels.append(level)

            if not highest_level_chain:
                continue
            # deal with level with inherits_from
            i = highest_level_chain.index(level)
            for higher_level in highest_level_chain[:i]:
                if higher_level in cac_control_levels:
                    cac_control_levels.remove(higher_level)
            # if CaC control already have a lower level, remove current level
            if set(highest_level_chain[i + 1 :]).intersection(  # noqa: E203
                set(cac_control_levels)
            ):
                cac_control_levels.remove(level)

        # remove level from CaC control
        for remove_id in remove:
            cac_control = self.cac_control_map[self.cac_to_oscal_map[remove_id]]
            cac_control_levels = cac_control["levels"]
            if level in cac_control_levels:
                cac_control_levels.remove(level)

            if not highest_level_chain:
                continue
            # deal with level with inherits_from
            i = highest_level_chain.index(level)
            if i - 1 >= 0 and highest_level_chain[i - 1] not in cac_control_levels:
                cac_control_levels.append(highest_level_chain[i - 1])

    def execute(self) -> int:
        policy_path = pathlib.Path(
            os.path.join(self.control_dir, f"{self.cac_policy_id}.yml")
        )
        data = read_cac_yaml_ordered(policy_path)

        # read CaC control file data
        self.cac_control_map = self.get_cac_id_control_map(data)

        control_mgr = load_controls_manager(
            str(self.cac_content_root.resolve()),
            self.product,
        )
        # get level with ancestors
        self.level_with_ancestors = self.get_level_with_ancestors(control_mgr)
        logger.info(f"level with ancestors: {self.level_with_ancestors}")

        # get all oscal profiles according to policy-id
        profiles = self.get_oscal_profiles(pathlib.Path(self.working_dir))
        # load all controls
        self.load_all_controls(profiles)
        # get cac_control_id to oscal_control_id map
        self.cac_to_oscal_map = self.get_cac_to_oscal_map(control_mgr)

        # sort profile according to level ancestors number, low level -> high level
        profiles.sort(
            key=lambda x: len(
                self.level_with_ancestors[
                    x[0].metadata.title.split(self.cac_policy_id + "-")[-1]
                ]
            ),
        )

        # deal with profile from low level to high level
        for profile, _ in profiles:
            level = profile.metadata.title.split(self.cac_policy_id + "-")[-1]
            for import_obj in profile.imports:
                for include_control in import_obj.include_controls:
                    oscal_control_ids = list()
                    for oscal_control_id in include_control.with_ids:
                        oscal_control_ids.append(oscal_control_id.__root__)

                    cac_control_ids = []
                    for control in control_mgr.get_all_controls_of_level(
                        self.cac_policy_id, level
                    ):
                        oscal_control_id = self.catalog_helper.get_id(control.id)
                        if oscal_control_id:
                            cac_control_ids.append(oscal_control_id)

                    add = set(oscal_control_ids).difference(set(cac_control_ids))
                    remove = set(cac_control_ids).difference(set(oscal_control_ids))
                    logger.info(f"processing {level}, add: {add}, remove: {remove}")
                    self.process_level(level, add, remove)

        # write CaC control file data
        write_cac_yaml_ordered(policy_path, data)

        return SUCCESS_EXIT_CODE
