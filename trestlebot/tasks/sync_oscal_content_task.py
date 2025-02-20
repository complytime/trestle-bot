# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Trestle Bot Sync OSCAL models to cac content Tasks"""
import logging
import os.path
import pathlib
from typing import Any, Dict, List

from ssg.profiles import ProfileSelections, get_profiles_from_products
from ssg.variables import get_variable_options
from ssg.yaml import ordered_dump, ordered_load
from trestle.common.model_utils import ModelUtils
from trestle.core.models.file_content_type import FileContentType
from trestle.oscal.component import ComponentDefinition, DefinedComponent, SetParameter

from trestlebot.const import FRAMEWORK_SHORT_NAME, SUCCESS_EXIT_CODE
from trestlebot.tasks.base_task import TaskBase


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
            elif (
                parameter.param_id in profile_variables
                and profile_variables[parameter.param_id] not in parameter.values
            ):
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

    def validate_new_variables_exists(self) -> None:
        """
        Validate new variables need to added exists in cac content, remove from parameters_add
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
                if v not in all_options.values():
                    logger.warning(
                        f"variable {parameter.param_id} not have {v} option in cac content"
                    )
                    self._parameters_add.remove(parameter)

    def __str__(self) -> str:
        return (
            f"Parameters added: {self.parameters_add}, Parameters updated: {self.parameters_update},"
            f" Parameters remove: {self.parameters_remove}"
        )


def populate_default_if_field_not_exist(
    data: Dict[str, Any], field_name: str, default_value: Any
) -> Any:
    """
    Set field with default value if a dict field is not exists
    """
    if data.get(field_name) is None:
        data[field_name] = default_value

    return data[field_name]


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

    @staticmethod
    def read_ordered_data_from_yaml(file_path: pathlib.Path) -> Dict[str, Any]:
        """
        Read data from yaml file while preserving the order of dictionaries
        """
        with open(file_path, "r") as f:
            r = ordered_load(f)
        return r

    @staticmethod
    def write_ordered_data_to_yaml(
        file_path: pathlib.Path, data: Dict[str, Any]
    ) -> None:
        """
        Serializes a Python object into a YAML stream, preserving the order of dictionaries.
        """
        with open(file_path, "w") as f:
            ordered_dump(data, f)

    def _handle_parameter_change(
        self, variables: List[str], rule_list: List[str], add: bool = True
    ) -> None:
        """
        Update parameters change in cac content model
        """
        for variable in variables:
            v_id, v_value = variable.split("=")
            if v_id in self.parameter_diff_info.parameters_remove:
                # remove variable
                rule_list.remove(variable)
            elif v_id in self.parameter_diff_info.parameters_update:
                # update variable
                rule_list.remove(variable)
                for v in self.parameter_diff_info.parameters_update[v_id]:
                    rule_list.append(f"{v_id}={v}")

        # add variable
        if not add:
            return

        for p in self.parameter_diff_info.parameters_add:
            for v in p.values:
                rule_list.append(f"{p.param_id}={v}")

    def _handle_controls_field(self, controls_data: List[Dict[str, Any]]) -> None:
        """
        Handle control file's controls field update
        """
        for control in controls_data:
            sub_control = control.get("controls", [])
            # recursively deal the sub controls of a control
            if sub_control:
                self._handle_controls_field(sub_control)

            # get rules field
            rules = populate_default_if_field_not_exist(control, "rules", [])
            variables = []
            for rule in rules:
                if "=" in rule:
                    # variable
                    variables.append(rule)
                else:
                    # rule
                    pass

            self._handle_parameter_change(variables, rules, add=False)

    def sync_to_control_file(self, control_file_path: pathlib.Path) -> None:
        """
        Sync component definition data to control file
        """
        control_file_data = self.read_ordered_data_from_yaml(control_file_path)
        controls = control_file_data.get("controls", [])
        self._handle_controls_field(controls)
        self.write_ordered_data_to_yaml(control_file_path, control_file_data)

    def sync(self, profile_id: str) -> None:
        profile_path = pathlib.Path(
            os.path.join(
                self.cac_content_root,
                "products",
                self.product,
                "profiles",
                f"{profile_id}.profile",
            )
        )
        # get profile data from yaml
        profile_data = self.read_ordered_data_from_yaml(profile_path)

        selections = populate_default_if_field_not_exist(profile_data, "selections", [])
        extends = profile_data.get("extends", "")
        # recursively deal the extends profile
        if extends:
            self.sync(extends)

        # Handle selections field, update profile file
        policy_ids = []
        variables = []
        for selection in selections:
            if ":" in selection:
                # control file
                policy_ids.append(selection.split(":", maxsplit=1)[0])
            elif "=" in selection:
                # variable
                variables.append(selection)
            else:
                # rule
                pass

        # handle variables
        self._handle_parameter_change(variables, selections)

        # save profile change
        self.write_ordered_data_to_yaml(profile_path, profile_data)

        # update control file
        for policy_id in policy_ids:
            control_file_path = pathlib.Path(
                os.path.join(self.control_dir, f"{policy_id}.yml")
            )
            self.sync_to_control_file(control_file_path)

    def execute(self) -> int:
        # get component definition path according to product name
        cd_json_path = ModelUtils.get_model_path_for_name_and_class(
            self.working_dir, self.product, ComponentDefinition, FileContentType.JSON
        )

        component_definition = ComponentDefinition.oscal_read(cd_json_path)
        logger.debug(f"Sync {cd_json_path}")

        # find the component to sync
        component: DefinedComponent
        for cd in component_definition.components:
            if cd.title == self.product:
                component = cd
                break
        else:
            raise RuntimeError(f"Component {self.product} not found in {cd_json_path}")
        logger.debug(f"Sync component {component.title}")

        # handle multiple control_implementations
        for control_implementation in component.control_implementations:
            # find profile id in pros field
            for property_obj in control_implementation.props:
                if property_obj.name == FRAMEWORK_SHORT_NAME:
                    profile_id = property_obj.value
                    break
            else:
                raise RuntimeError(
                    f"profile_id not found for component {component.title}"
                )

            logger.debug(f"Found cac profile id: {profile_id}")

            # check parameters diff
            profiles = get_profiles_from_products(self.cac_content_root, [self.product])
            profile_selection_obj: ProfileSelections
            for profile in profiles:
                if profile.profile_id == profile_id:
                    # print(profile.rules)
                    logger.debug(f"profile variables: {profile.variables}")
                    profile_selection_obj = profile
                    break

            diff = ParameterDiffInfo(
                self.cac_content_root,
                profile_selection_obj.variables,
                control_implementation.set_parameters,
            )
            diff.validate_new_variables_exists()
            logger.debug(f"parameters diff: {diff}")
            self.parameter_diff_info = diff
            # sync
            self.sync(profile_id)

        return SUCCESS_EXIT_CODE
