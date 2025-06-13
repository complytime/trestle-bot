import logging
import pathlib
from typing import Dict

from ruamel.yaml import CommentedMap
from trestle.common.model_utils import ModelUtils
from trestle.core.catalog.catalog_interface import CatalogInterface
from trestle.core.control_interface import ControlInterface
from trestle.core.models.file_content_type import FileContentType
from trestle.oscal.catalog import Catalog, Control

from complyscribe.const import SUCCESS_EXIT_CODE
from complyscribe.tasks.base_task import TaskBase
from complyscribe.utils import (
    populate_if_dict_field_not_exist,
    read_cac_yaml_ordered,
    write_cac_yaml_ordered,
)


logger = logging.getLogger(__name__)


class SyncOscalCatalogTask(TaskBase):
    """Sync OSCAL catalog to CaC content task."""

    def __init__(
        self,
        cac_content_root: pathlib.Path,
        working_dir: str,
        cac_policy_id: str,
    ) -> None:
        """Initialize task."""
        super().__init__(working_dir, None)
        self.cac_content_root = cac_content_root
        self.cac_policy_id = cac_policy_id
        self.catalog_controls: Dict[str, Control] = {}
        self.control_file_path = pathlib.Path(
            self.cac_content_root, "controls", f"{self.cac_policy_id}.yml"
        )
        self.oscal_to_cac_map: Dict[str, str] = {}

    def get_catalog_controls(self, catalog: Catalog) -> Dict[str, Control]:
        """
        Get all controls from a catalog.
        """
        controls = {
            control.id: control
            for control in CatalogInterface(catalog).get_all_controls_from_catalog(
                recurse=True
            )
        }
        return controls

    def get_oscal_to_cac_map(self, catalog: Catalog) -> Dict[str, str]:
        """
        Get oscal_control_id to cac_control_id map
        """
        result = {}
        for control in CatalogInterface(catalog).get_all_controls_from_catalog(
            recurse=True
        ):
            label = ControlInterface.get_label(control)
            if label:
                result[control.id] = label

        return result

    def sync_description(self, cac_control_map: Dict[str, CommentedMap]) -> None:
        """
        Sync OSCAL catalog parts field to CaC control file description field
        """
        for oscal_control_id, oscal_control in self.catalog_controls.items():
            cac_control_id = self.oscal_to_cac_map.get(oscal_control_id)
            if not cac_control_id:
                continue

            cac_control = cac_control_map.get(cac_control_id)
            if not cac_control:
                continue
            parts_statement = ControlInterface.get_part_prose(
                oscal_control, "statement"
            )
            description = cac_control.get("description")
            if not description and not parts_statement:
                continue

            populate_if_dict_field_not_exist(cac_control, "description", "")
            cac_control["description"] = parts_statement

    def sync_oscal_catalog(self) -> None:
        """
        Sync OSCAL catalog information to CaC control file.
        """
        data = read_cac_yaml_ordered(self.control_file_path)
        cac_control_map = {
            control["id"]: control for control in data.get("controls", [])
        }
        self.sync_description(cac_control_map)
        write_cac_yaml_ordered(self.control_file_path, data)

    def execute(self) -> int:
        oscal_json = ModelUtils.get_model_path_for_name_and_class(
            self.working_dir, self.cac_policy_id, Catalog, FileContentType.JSON
        )

        if not oscal_json.exists():
            raise RuntimeError(f"{oscal_json} does not exist")

        oscal_catalog = Catalog.oscal_read(oscal_json)
        self.catalog_controls = self.get_catalog_controls(oscal_catalog)
        self.oscal_to_cac_map = self.get_oscal_to_cac_map(oscal_catalog)
        self.sync_oscal_catalog()

        return SUCCESS_EXIT_CODE
