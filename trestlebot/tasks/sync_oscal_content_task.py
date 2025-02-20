# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Trestle Bot Sync OSCAL models to cac content Tasks"""
import logging
import os.path
import pathlib
from typing import Any, Dict, List

from ruamel.yaml import YAML
from ssg.profiles import ProfileSelections, get_profiles_from_products
from ssg.variables import get_variable_options
from trestle.common.model_utils import ModelUtils
from trestle.core.models.file_content_type import FileContentType
from trestle.core.profile_resolver import ProfileResolver
from trestle.oscal.component import (
    ComponentDefinition,
    ControlImplementation,
    DefinedComponent,
    ImplementedRequirement,
    SetParameter,
)

from trestlebot.const import FRAMEWORK_SHORT_NAME, SUCCESS_EXIT_CODE
from trestlebot.tasks.authored.profile import CatalogControlResolver
from trestlebot.tasks.base_task import TaskBase
from trestlebot.utils import populate_if_dict_field_not_exist


logger = logging.getLogger(__name__)


class ParameterDiffInfo:
    """
    Parameter difference info between OSCAL component definition and cac content
    """

    def __init__(
        self,
        cac_content_root: pathlib.Path,
        profile_variables: Dict[str, str],
        oscal_parameters: List[SetParameter],
    ):
        """
        Deal with parameter difference when init
        """
        self.cac_content_root = cac_content_root
        self._parameters_add: List[SetParameter] = []
        self._parameters_update: Dict[str, List[str]] = {}
        self._parameters_remove: List[str] = [
            v
            for v in profile_variables
            if v not in [parameter.param_id for parameter in oscal_parameters]
        ]
        for parameter in oscal_parameters:
            if parameter.param_id not in profile_variables:
                self._parameters_add.append(parameter)
            elif profile_variables[parameter.param_id] not in parameter.values:
                self._parameters_update[parameter.param_id] = parameter.values

    @property
    def parameters_add(self) -> List[SetParameter]:
        return self._parameters_add

    @property
    def parameters_update(self) -> Dict[str, List[str]]:
        return self._parameters_update

    @property
    def parameters_remove(self) -> List[str]:
        return self._parameters_remove

    def validate_variables(self) -> None:
        """
        Validate new variables need to added/update exists in cac content, remove from parameters_add
        if it's invalid
        """
        for parameter in self._parameters_add:
            all_options = get_variable_options(
                self.cac_content_root, parameter.param_id
            )
            if not all_options:
                logger.warning(
                    f"variable {parameter.param_id} not found in cac content"
                )
                self._parameters_add.remove(parameter)
                continue

            for v in parameter.values:
                if v not in all_options:
                    logger.warning(
                        f"variable {parameter.param_id} not have {v} option in cac content"
                    )
                    parameter.values.remove(v)

        for param_id, param_values in self._parameters_update.items():
            all_options = get_variable_options(self.cac_content_root, param_id)

            for v in param_values:
                if v not in all_options:
                    logger.warning(
                        f"variable {parameter.param_id} not have {v} option in cac content"
                    )
                    self._parameters_update[param_id].remove(v)

    def __str__(self) -> str:
        return (
            f"Parameters added: {self.parameters_add}, Parameters updated: {self.parameters_update},"
            f" Parameters remove: {self.parameters_remove}"
        )


class SyncOscalCdTask(TaskBase):
    """Sync OSCAL component definition to cac content task."""

    def __init__(
        self, cac_content_root: pathlib.Path, working_dir: str, product: str
    ) -> None:
        """Initialize task."""
        super().__init__(working_dir, None)
        self.cac_content_root = cac_content_root
        self.product = product
        self.control_dir = os.path.join(self.cac_content_root, "controls")
        self.parameter_diff_info: ParameterDiffInfo = ParameterDiffInfo(
            self.cac_content_root, {}, []
        )
        self.implemented_requirement_dict: Dict[str, ImplementedRequirement] = {}
        self.catalog_helper: CatalogControlResolver = CatalogControlResolver()

    @staticmethod
    def read_ordered_data_from_yaml(file_path: pathlib.Path) -> Any:
        """
        Read data from yaml file while preserving the order of dictionaries
        """
        yaml = YAML()
        return yaml.load(file_path)

    @staticmethod
    def write_ordered_data_to_yaml(
        file_path: pathlib.Path, data: Any, is_profile: bool = False
    ) -> None:
        """
        Serializes a Python object into a YAML stream, preserving the order of dictionaries.
        """
        yaml = YAML()
        # profile indent
        if is_profile:
            yaml.indent(mapping=4, sequence=4, offset=4)
        yaml.dump(data, file_path)

    def _update_selections_rules_in_memory(
        self, rule_list: List[str], add_params: bool = True
    ) -> List[str]:
        """
        In memory update selections/rules field of cac content
        return: policy id list
        """
        policy_ids = []
        removed_variable = []
        for rule_index, rule in enumerate(rule_list):
            if ":" in rule:
                # policy
                policy_ids.append(rule.split(":", maxsplit=1)[0])
            elif "=" in rule:
                # variable
                v_id, v_value = rule.split("=")
                if v_id in self.parameter_diff_info.parameters_update:
                    # update variable
                    for v in self.parameter_diff_info.parameters_update[v_id]:
                        rule_list[rule_index] = f"{v_id}={v}"
                elif v_id in self.parameter_diff_info.parameters_remove:
                    removed_variable.append(rule)
            else:
                # rule
                pass

        # remove variables
        for v in removed_variable:
            rule_list.remove(v)

        if not add_params:
            return policy_ids

        # add variables
        for p in self.parameter_diff_info.parameters_add:
            for v in p.values:
                rule_list.append(f"{p.param_id}={v}")

        return policy_ids

    def _handle_controls_field(self, controls_data: List[Dict[str, Any]]) -> None:
        """
        Handle control file's controls field update
        """
        for control in controls_data:
            sub_control = control.get("controls", [])
            # recursively deal the sub controls of a control
            if sub_control:
                self._handle_controls_field(sub_control)

            if (
                self.catalog_helper.get_id(control["id"])
                not in self.implemented_requirement_dict
            ):
                continue

            # get rules field
            rules = populate_if_dict_field_not_exist(control, "rules", [])
            self._update_selections_rules_in_memory(rules, add_params=False)

    def sync_to_control_file(self, control_file_path: pathlib.Path) -> None:
        """
        Sync component definition data to control file
        """
        control_file_data = self.read_ordered_data_from_yaml(control_file_path)
        controls = control_file_data.get("controls", [])
        self._handle_controls_field(controls)
        self.write_ordered_data_to_yaml(control_file_path, control_file_data)

    def sync(self, profile_id: str) -> None:
        """
        Sync OSCAL component definition data start from a cac content profile.
        """
        profile_path = pathlib.Path(
            os.path.join(
                self.cac_content_root,
                "products",
                self.product,
                "profiles",
                f"{profile_id}.profile",
            )
        )
        # sync profile
        # get profile data from yaml
        profile_data = self.read_ordered_data_from_yaml(profile_path)

        selections = populate_if_dict_field_not_exist(profile_data, "selections", [])
        extends = profile_data.get("extends", "")
        # recursively deal the extends profile
        if extends:
            self.sync(extends)

        # Handle selections field, update profile file
        # handle variables
        policy_ids = self._update_selections_rules_in_memory(selections)

        # save profile change
        self.write_ordered_data_to_yaml(profile_path, profile_data, is_profile=True)

        # sync control file
        for policy_id in policy_ids:
            control_file_path = pathlib.Path(
                os.path.join(self.control_dir, f"{policy_id}.yml")
            )
            self.sync_to_control_file(control_file_path)

    def make_implemented_requirements_as_dict(
        self, control_implementation: ControlImplementation
    ) -> None:
        """
        Transform OSCAL implemented-requirements field as dict for later use, control-id as key,
        implemented-requirement object as value
        """
        self.implemented_requirement_dict.clear()
        for implemented_requirement in control_implementation.implemented_requirements:
            self.implemented_requirement_dict[implemented_requirement.control_id] = (
                implemented_requirement
            )

    def execute(self) -> int:
        # get component definition path according to product name
        cd_json_path = ModelUtils.get_model_path_for_name_and_class(
            self.working_dir, self.product, ComponentDefinition, FileContentType.JSON
        )

        logger.debug(f"Start to load {cd_json_path}")
        component_definition = ComponentDefinition.oscal_read(cd_json_path)
        if not component_definition:
            raise RuntimeError(f"Read Component Definition from {cd_json_path} failed")

        # find the component to sync
        component: DefinedComponent
        for cd in component_definition.components:
            if cd.title == self.product:
                component = cd
                break
        else:
            raise RuntimeError(f"Component {self.product} not found in {cd_json_path}")
        logger.debug(f"Start to sync component {component.title}")

        # handle multiple control_implementations
        for control_implementation in component.control_implementations:
            # find profile id in 'props' field
            for property_obj in control_implementation.props:
                if property_obj.name == FRAMEWORK_SHORT_NAME:
                    profile_id = property_obj.value
                    break
            else:
                raise RuntimeError(
                    f"profile_id not found for component {component.title}"
                )

            logger.debug(f"Found cac profile id: {profile_id}")
            self.make_implemented_requirements_as_dict(control_implementation)
            # use CatalogControlResolver to get control id map between cac and OSCAL
            catalog_helper = CatalogControlResolver()
            profile_resolver = ProfileResolver()
            resolved_catalog = profile_resolver.get_resolved_profile_catalog(
                pathlib.Path(self.working_dir),
                control_implementation.source,
                block_params=False,
                params_format="[.]",
                show_value_warnings=True,
            )
            catalog_helper.load(resolved_catalog)
            self.catalog_helper = catalog_helper

            # check parameters diff
            profiles = get_profiles_from_products(self.cac_content_root, [self.product])
            profile_selection_obj: ProfileSelections
            for profile in profiles:
                if profile.profile_id == profile_id:
                    logger.info(f"profile {profile_id} variables: {profile.variables}")
                    profile_selection_obj = profile
                    break

            diff = ParameterDiffInfo(
                self.cac_content_root,
                profile_selection_obj.variables,
                control_implementation.set_parameters,
            )
            diff.validate_variables()
            logger.info(f"parameters diff: {diff}")
            self.parameter_diff_info = diff
            # sync
            self.sync(profile_id)

        return SUCCESS_EXIT_CODE
