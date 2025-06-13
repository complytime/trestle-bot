# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""ComplyScribe Sync OSCAL models to cac content Tasks"""
import logging
import os.path
import pathlib
import re
from typing import Dict, List, Optional, Set, Tuple

from ruamel.yaml.comments import CommentedMap, CommentedOrderedMap
from ruamel.yaml.scanner import ScannerError
from ssg.constants import BENCHMARKS
from ssg.controls import Status
from ssg.profiles import ProfileSelections, get_profiles_from_products
from ssg.rules import find_rule_dirs, get_rule_dir_id
from ssg.variables import get_variable_files, get_variable_options
from trestle.common.const import (
    IMPLEMENTATION_STATUS,
    RULE_ID,
    STATUS_ALTERNATIVE,
    STATUS_IMPLEMENTED,
    STATUS_NOT_APPLICABLE,
    STATUS_PARTIAL,
    STATUS_PLANNED,
)
from trestle.common.model_utils import ModelUtils
from trestle.core.models.file_content_type import FileContentType
from trestle.core.profile_resolver import ProfileResolver
from trestle.oscal.common import Property
from trestle.oscal.component import (
    ComponentDefinition,
    ControlImplementation,
    DefinedComponent,
    ImplementedRequirement,
    SetParameter,
)

from complyscribe.const import FRAMEWORK_SHORT_NAME, SUCCESS_EXIT_CODE
from complyscribe.tasks.authored.profile import CatalogControlResolver
from complyscribe.tasks.base_task import TaskBase
from complyscribe.utils import (
    get_comments_from_yaml_data,
    get_field_comment,
    populate_if_dict_field_not_exist,
    read_cac_yaml_ordered,
    to_literal_scalar_string,
    write_cac_yaml_ordered,
)


logger = logging.getLogger(__name__)

# OSCAL control status to cac control status mapping
OSCAL_TO_CAC_STATUS_MAPPING = {
    STATUS_IMPLEMENTED: [
        Status.INHERENTLY_MET,
        Status.DOCUMENTATION,
        Status.AUTOMATED,
        Status.SUPPORTED,
    ],
    STATUS_ALTERNATIVE: [Status.DOES_NOT_MEET, Status.MANUAL, Status.PENDING],
    STATUS_PARTIAL: [Status.PARTIAL],
    STATUS_NOT_APPLICABLE: [Status.NOT_APPLICABLE],
    STATUS_PLANNED: [Status.PLANNED],
}


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

    def _add_new_option_to_var_file(self, var_id: str, var_value: str) -> None:
        """
        Add new option to var file
        """
        for v_file in get_variable_files(self.cac_content_root):
            if f"{var_id}.var" in v_file:
                try:
                    data = read_cac_yaml_ordered(pathlib.Path(v_file))
                    data["options"].update({var_value: var_value})
                    write_cac_yaml_ordered(pathlib.Path(v_file), data)
                    logger.info(
                        f"Added new option {var_value}: {var_value} to {v_file}"
                    )
                except ScannerError:
                    # currently some var file contains Jinja2 macros,
                    # temporarily ignore this exception
                    logger.warning(
                        f"process {v_file} failed, this file may contains Jinja2 marcos"
                    )

                break

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
                    # add new option to var file
                    self._add_new_option_to_var_file(parameter.param_id, v)

        for param_id, param_values in self._parameters_update.items():
            all_options = get_variable_options(self.cac_content_root, param_id)

            for v in param_values:
                if v not in all_options:
                    # add new option to var file
                    self._add_new_option_to_var_file(param_id, v)

    def __str__(self) -> str:
        return (
            f"Parameters added: {self.parameters_add}, Parameters updated: {self.parameters_update},"
            f" Parameters removed: {self.parameters_remove}"
        )


class SyncOscalCdTask(TaskBase):
    """Sync OSCAL component definition to cac content task."""

    def __init__(
        self,
        cac_content_root: pathlib.Path,
        working_dir: str,
        product: str,
        oscal_profile: str,
    ) -> None:
        """Initialize task."""
        super().__init__(working_dir, None)
        self.cac_content_root = cac_content_root
        self.product = product
        self.oscal_profile = oscal_profile
        self.control_dir = os.path.join(self.cac_content_root, "controls")
        self.parameter_diff_info: ParameterDiffInfo = ParameterDiffInfo(
            self.cac_content_root, {}, []
        )
        self.implemented_requirement_dict: Dict[str, ImplementedRequirement] = {}
        self.catalog_helper: CatalogControlResolver = CatalogControlResolver()
        self.all_rule_ids_from_cac: List[str] = list()
        self.rule_ids_from_oscal: Set[str] = set()

    @staticmethod
    def get_oscal_component_rule_ids(
        component_props: Optional[List[Property]],
    ) -> Set[str]:
        r: Set[str] = set()
        if not component_props:
            return r
        for prop in component_props:
            if prop.name == RULE_ID:
                r.add(prop.value)
        return r

    def get_all_cac_rule_ids(self) -> List[str]:
        """
        Get all rules ids from CaC content repo
        """
        r = list()
        for benchmark in BENCHMARKS:
            for rule_dir in find_rule_dirs(
                str(self.cac_content_root.joinpath(benchmark).resolve())
            ):
                r.append(get_rule_dir_id(rule_dir))

        return r

    def _parse_single_variable(self, variable: str) -> Tuple[List[str], Optional[str]]:
        """
        Parse single variable from cac content
        """
        v_id, _ = variable.split("=")
        removed_variable = []
        update_variable_value = None
        if v_id in self.parameter_diff_info.parameters_update:
            # update variable value
            for v in self.parameter_diff_info.parameters_update[v_id]:
                update_variable_value = f"{v_id}={v}"
        elif v_id in self.parameter_diff_info.parameters_remove:
            # remove variable
            removed_variable.append(variable)

        return removed_variable, update_variable_value

    def _update_missing_rule_in_memory(
        self, cac_control: CommentedOrderedMap, missing_rules: List[str]
    ) -> None:
        """
        Add comment to control file for missing rule
        """
        # collect all comments in current control, to avoid adding a duplicate comment
        exist_comments = get_comments_from_yaml_data(cac_control)

        rule_list = cac_control["rules"]

        # deal with missing rules
        for missing_rule in missing_rules:
            logger.warning(
                f"rule {missing_rule} not exists in cac content repo: {self.cac_content_root}"
                f" when trying to add to control: {cac_control['id']}"
            )
            comment = f"TODO: Need to implement rule {missing_rule}"
            # check if missing rule comment already exists
            if [True for c in exist_comments if comment in c]:
                continue

            # add comment for missing rule
            if rule_list:
                # rules field is non-empty
                rule_list.yaml_set_comment_before_after_key(0, before=comment)
            else:
                # rules field is empty list
                cac_control.yaml_set_comment_before_after_key("rules", before=comment)

    def _update_status(
        self, cac_control: CommentedMap, oscal_control: ImplementedRequirement
    ) -> None:
        """
        update cac control status according to OSCAL control status
        """
        oscal_status = None
        for prop in oscal_control.props:
            if prop.name == IMPLEMENTATION_STATUS:
                oscal_status = prop.value

        if oscal_status is None:
            return

        cac_status = cac_control["status"]
        mapping_status = OSCAL_TO_CAC_STATUS_MAPPING[oscal_status]
        if cac_status in mapping_status:
            return
        elif len(mapping_status) == 1:
            cac_control["status"] = mapping_status[0]
            logger.info(
                f"Changing cac control {cac_control['id']} status to {mapping_status[0]}"
            )
        else:
            # add comment
            exist_comments = get_comments_from_yaml_data(cac_control)
            comment = f"The status should be updated to one of {mapping_status}"
            # check if comment already exists
            if [True for c in exist_comments if comment in c]:
                return
            cac_control.yaml_set_comment_before_after_key("status", before=comment)
            logger.info(
                f"Adding comment to cac control {cac_control['id']} due to status change ambiguous"
            )

    def _update_cac_notes(
        self, cac_control: CommentedMap, oscal_control: ImplementedRequirement
    ) -> None:
        """
        Sync OSCAL statements field to CaC notes field
        """
        notes = cac_control.get("notes")
        if not notes and not oscal_control.statements:
            return

        statements = oscal_control.statements if oscal_control.statements else []

        notes = populate_if_dict_field_not_exist(cac_control, "notes", "")
        # combine OSCAL statements
        combined_statements = "\n".join(
            [
                f"Section {statement.statement_id.split('_smt.')[-1]}: {statement.description}"
                for statement in statements
            ]
        )

        split_notes = re.split("Section [a-zA-Z]", notes, maxsplit=1)
        if len(split_notes) == 1:
            split_note = split_notes[0]
            if re.search(r"Section [a-zA-Z]:.+", split_note) or not split_note:
                cac_control["notes"] = to_literal_scalar_string(combined_statements)
            elif split_note and combined_statements:
                cac_control["notes"] = to_literal_scalar_string(
                    split_note + "\n" + combined_statements
                )
        else:
            old_notes_without_section = (
                split_notes[1]
                if re.search(r"Section [a-zA-Z]:.+", split_notes[0])
                else split_notes[0]
            )
            cac_control["notes"] = to_literal_scalar_string(
                old_notes_without_section + combined_statements
            )

    def _update_control_file_change_in_memory(
        self, cac_control: CommentedMap, oscal_control: ImplementedRequirement
    ) -> None:
        """
        In memory update cac control file changes
        """
        rule_list = populate_if_dict_field_not_exist(cac_control, "rules", [])

        removed_variable = []
        cac_rule_list = []
        for rule_index, rule in enumerate(rule_list):
            if "=" in rule:
                # variable
                removed, update_variable = self._parse_single_variable(rule)
                removed_variable.extend(removed)
                rule_list[rule_index] = update_variable if update_variable else rule
            else:
                # rule
                cac_rule_list.append(rule)

        # remove variables
        for v in removed_variable:
            rule_list.remove(v)

        oscal_control_rules = [
            prop.value for prop in oscal_control.props if prop.name == RULE_ID
        ]
        # remove rule
        for rule in set(cac_rule_list).difference(set(oscal_control_rules)):
            rule_list.remove(rule)
            logger.info(f"Remove rule {rule} from control: {cac_control['id']}")

        # add rule
        missing_rules = []
        for rule in set(oscal_control_rules).difference(set(cac_rule_list)):
            if rule in self.all_rule_ids_from_cac:
                rule_list.append(rule)
                logger.info(f"Add rule {rule} to control: {cac_control['id']}")
            else:
                missing_rules.append(rule)

        # if rules field is empty and there is comments under rules field,
        # move old comments above rules field to avoid yaml file format error
        old_rules_comments = get_field_comment(cac_control, "rules")
        if not rule_list and old_rules_comments:
            del cac_control.ca.items["rules"]
            for comment in old_rules_comments:
                cac_control.yaml_set_comment_before_after_key(
                    "rules", before=comment.lstrip("#")
                )

        # handle missing rule
        self._update_missing_rule_in_memory(cac_control, missing_rules)

        # handle status change
        self._update_status(cac_control, oscal_control)

        # Sync OSCAL statements field to CaC notes field
        self._update_cac_notes(cac_control, oscal_control)

    def _update_profile_change_in_memory(
        self, profile_data: CommentedMap, profile_id: str
    ) -> List[str]:
        """
        In memory update cac profile changes
        return: policy id list
        """
        selections = populate_if_dict_field_not_exist(profile_data, "selections", [])

        policy_ids = []
        removed_variable = []
        removed_rules = []
        for rule_index, rule in enumerate(selections):
            if ":" in rule:
                # policy
                policy_ids.append(rule.split(":", maxsplit=1)[0])
            elif "=" in rule:
                # variable
                removed, update_variable = self._parse_single_variable(rule)
                removed_variable.extend(removed)
                selections[rule_index] = update_variable if update_variable else rule
            else:
                # rule
                if rule not in self.rule_ids_from_oscal:
                    removed_rules.append(rule)

        # remove variables
        for v in removed_variable:
            selections.remove(v)

        # add variables
        for p in self.parameter_diff_info.parameters_add:
            for v in p.values:
                selections.append(f"{p.param_id}={v}")

        # remove rules
        for r in removed_rules:
            selections.remove(r)
            logger.info(f"remove rule {r} from cac profile {profile_id}")

        return policy_ids

    def _handle_controls_field(self, controls_data: List[CommentedMap]) -> None:
        """
        Handle control file's controls field update
        """
        for control in controls_data:
            sub_control = control.get("controls", [])
            # recursively deal the sub controls of a control
            if sub_control:
                self._handle_controls_field(sub_control)

            oscal_control_id = self.catalog_helper.get_id(control["id"])

            if oscal_control_id not in self.implemented_requirement_dict:
                continue

            oscal_control = self.implemented_requirement_dict[oscal_control_id]
            self._update_control_file_change_in_memory(control, oscal_control)

    def sync_to_control_file(self, control_file_path: pathlib.Path) -> None:
        """
        Sync component definition data to control file
        """
        control_file_data = read_cac_yaml_ordered(control_file_path)
        controls = control_file_data.get("controls", [])
        self._handle_controls_field(controls)
        write_cac_yaml_ordered(control_file_path, control_file_data)

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
        profile_data = read_cac_yaml_ordered(profile_path)

        # Handle selections field, update profile file
        policy_ids = self._update_profile_change_in_memory(profile_data, profile_id)

        # save profile change
        write_cac_yaml_ordered(profile_path, profile_data)

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
            self.working_dir,
            os.path.join(self.product, self.oscal_profile),
            ComponentDefinition,
            FileContentType.JSON,
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

        self.all_rule_ids_from_cac = self.get_all_cac_rule_ids()
        self.rule_ids_from_oscal = self.get_oscal_component_rule_ids(component.props)

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

            oscal_parameters = control_implementation.set_parameters
            diff = ParameterDiffInfo(
                self.cac_content_root,
                profile_selection_obj.variables,
                [] if oscal_parameters is None else oscal_parameters,
            )
            diff.validate_variables()
            logger.info(f"parameters diff: {diff}")
            self.parameter_diff_info = diff
            # sync
            self.sync(profile_id)

        return SUCCESS_EXIT_CODE
