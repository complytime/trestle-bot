# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Trestle Bot Sync CaC Content Tasks"""

import logging
import os
import pathlib
import re
from typing import Dict, List, Optional, Pattern

# from ssg.products import get_all
from ssg.controls import Control, Status
from ssg.profiles import _load_yaml_profile_file, get_profiles_from_products
from trestle.common.common_types import TypeWithProps
from trestle.common.const import (
    IMPLEMENTATION_STATUS,
    REPLACE_ME,
    TRESTLE_GENERIC_NS,
    TRESTLE_HREF_HEADING,
)
from trestle.common.list_utils import as_list, none_if_empty
from trestle.common.model_utils import ModelUtils
from trestle.core.generators import generate_sample_model
from trestle.core.models.file_content_type import FileContentType
from trestle.core.profile_resolver import ProfileResolver
from trestle.oscal.catalog import Catalog
from trestle.oscal.common import Property
from trestle.oscal.component import (
    ComponentDefinition,
    ControlImplementation,
    DefinedComponent,
    ImplementedRequirement,
    SetParameter,
    Statement,
)

from trestlebot import const
from trestlebot.tasks.authored.profile import CatalogControlResolver
from trestlebot.tasks.base_task import TaskBase
from trestlebot.transformers.cac_transformer import (
    RuleInfo,
    RulesTransformer,
    add_prop,
    get_component_info,
    get_validation_component_mapping,
)
from trestlebot.utils import load_controls_manager


logger = logging.getLogger(__name__)

SECTION_PATTERN = r"Section ([a-z]):"


class OscalStatus:
    """
    Represent the status of a control in OSCAL.

    Notes:
        This transforms the status from SSG to OSCAL in the from
        string method.
    """

    PLANNED = "planned"
    NOT_APPLICABLE = "not-applicable"
    ALTERNATIVE = "alternative"
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"

    @staticmethod
    def from_string(source: str) -> str:
        data = {
            Status.INHERENTLY_MET: OscalStatus.IMPLEMENTED,
            Status.DOES_NOT_MEET: OscalStatus.ALTERNATIVE,
            Status.DOCUMENTATION: OscalStatus.IMPLEMENTED,
            Status.AUTOMATED: OscalStatus.IMPLEMENTED,
            Status.MANUAL: OscalStatus.ALTERNATIVE,
            Status.PLANNED: OscalStatus.PLANNED,
            Status.PARTIAL: OscalStatus.PARTIAL,
            Status.SUPPORTED: OscalStatus.IMPLEMENTED,
            Status.PENDING: OscalStatus.ALTERNATIVE,
            Status.NOT_APPLICABLE: OscalStatus.NOT_APPLICABLE,
        }
        if source not in data.keys():
            raise ValueError(f"Invalid status: {source}. Use one of {data.keys()}")
        return data.get(source)  # type: ignore

    STATUSES = {PLANNED, NOT_APPLICABLE, ALTERNATIVE, IMPLEMENTED, PARTIAL}


class SyncCacContentTask(TaskBase):
    """Sync CaC content to OSCAL component definition task."""

    def __init__(
        self,
        product: str,
        cac_profile: str,
        cac_content_root: str,
        compdef_type: str,
        oscal_profile: str,
        working_dir: str,
    ) -> None:
        """Initialize CaC content sync task."""

        self.product: str = product
        self.cac_profile: str = cac_profile
        self.cac_content_root: str = cac_content_root
        self.compdef_type: str = compdef_type
        self.oscal_profile: str = oscal_profile
        self.rules: List[str] = []
        self.controls: List[Control] = list()
        self.rules_by_id: Dict[str, RuleInfo] = dict()

        self.cac_profile_id = os.path.basename(cac_profile).split(".profile")[0]

        self.profile_href: str = ""
        self.profile_path: str = ""
        self.catalog_helper = CatalogControlResolver()

        super().__init__(working_dir, None)

    def _collect_rules(self) -> None:
        """Collect all rules from the product profile."""
        profiles = get_profiles_from_products(self.cac_content_root, [self.product])
        for profile in profiles:
            if profile.profile_id == self.cac_profile_id:
                self.rules = list(
                    filter(lambda x: x not in profile.unselected_rules, profile.rules)
                )
                break

    def _get_rules_properties(self) -> List[Property]:
        """Create all of the top-level component properties for rules."""
        rules_transformer = RulesTransformer(
            self.cac_content_root,
            self.product,
            self.cac_profile,
        )
        rules_transformer.add_rules(self.rules)
        self.rules_by_id = rules_transformer.get_all_rule_objs()
        rules: List[RuleInfo] = list(self.rules_by_id.values())
        all_rule_properties: List[Property] = rules_transformer.transform(rules)
        return all_rule_properties

    def _add_props(self, oscal_component: DefinedComponent) -> DefinedComponent:
        """Add props to OSCAL component."""
        product_name, full_name = get_component_info(
            self.product, self.cac_content_root
        )
        all_rule_properties = self._get_rules_properties()
        props = none_if_empty(all_rule_properties)
        oscal_component.type = self.compdef_type

        if oscal_component.type == "validation":
            oscal_component.title = "openscap"
            oscal_component.description = "openscap"
            oscal_component.props = get_validation_component_mapping(props)
        else:
            oscal_component.title = product_name
            oscal_component.description = full_name
            oscal_component.props = props
        return oscal_component

    def _get_source(self, profile_name_or_href: str) -> None:
        """Get the href and source of the profile."""
        profile_in_trestle_dir = "://" not in profile_name_or_href
        self.profile_href = profile_name_or_href
        if profile_in_trestle_dir:
            local_path = f"profiles/{profile_name_or_href}/profile.json"
            self.profile_href = TRESTLE_HREF_HEADING + local_path
            self.profile_path = os.path.join(self.working_dir, local_path)
        else:
            self.profile_path = self.profile_href

    def _get_controls(self) -> None:
        """Collect controls selected by profile."""
        controls_manager = load_controls_manager(self.cac_content_root, self.product)
        policies = controls_manager.policies
        profile_yaml = _load_yaml_profile_file(self.cac_profile)
        selections = profile_yaml.get("selections", [])
        for selected in selections:
            if ":" in selected:
                parts = selected.split(":")
                policy_id = parts[0]
                policy = policies.get(policy_id)
                if policy is not None:
                    if len(parts) == 3:
                        levels = [parts[2]]
                    else:
                        levels = [level.id for level in policy.levels]

                    for level in levels:
                        self.controls.extend(
                            controls_manager.get_all_controls_of_level(policy_id, level)
                        )

    @staticmethod
    def _build_sections_dict(
        control_response: str,
        section_pattern: Pattern[str],
    ) -> Dict[str, List[str]]:
        """Find all sections in the control response and build a dictionary of them."""
        lines = control_response.split("\n")

        sections_dict: Dict[str, List[str]] = dict()
        current_section_label = None

        for line in lines:
            match = section_pattern.match(line)

            if match:
                current_section_label = match.group(1)
                sections_dict[current_section_label] = [line]
            elif current_section_label is not None:
                sections_dict[current_section_label].append(line)

        return sections_dict

    @staticmethod
    def _add_response_by_status(
        impl_req: ImplementedRequirement,
        implementation_status: str,
        control_response: str,
    ) -> None:
        """
        Add the response to the implemented requirement depending on the status.

        Notes: Per OSCAL requirements, any status other than implemented and partial should have
        remarks with justification for the status.
        """

        status_prop = add_prop(IMPLEMENTATION_STATUS, implementation_status, "")

        if (
            implementation_status == OscalStatus.IMPLEMENTED
            or implementation_status == OscalStatus.PARTIAL
        ):
            impl_req.description = control_response
        else:
            status_prop.remarks = control_response

        impl_req.props = as_list(impl_req.props)
        impl_req.props.append(status_prop)

    def _create_statement(self, statement_id: str, description: str = "") -> Statement:
        """Create a statement."""
        statement = generate_sample_model(Statement)
        statement.statement_id = statement_id
        if description:
            statement.description = description
        return statement

    def _handle_response(
        self,
        implemented_req: ImplementedRequirement,
        control: Control,
    ) -> None:
        """
        Break down the response into parts.

        Args:
            implemented_req: The implemented requirement to add the response and statements to.
            control_response: The control response to add to the implemented requirement.
        """
        # REPLACE_ME is used as a generic string if no control notes
        control_response = control.notes or REPLACE_ME
        pattern = re.compile(SECTION_PATTERN, re.IGNORECASE)
        sections_dict = self._build_sections_dict(control_response, pattern)
        oscal_status = OscalStatus.from_string(control.status)

        if sections_dict:
            self._add_response_by_status(implemented_req, oscal_status, REPLACE_ME)
            implemented_req.statements = list()
            for section_label, section_content in sections_dict.items():
                # comment these lines due to https://issues.redhat.com/browse/CPLYTM-781
                # statement_id = self.catalog_helper.get_id(
                #     f"{implemented_req.control_id}_smt.{section_label}"
                # )
                # if statement_id is None:
                #     continue
                statement_id = f"{implemented_req.control_id}_smt.{section_label}"
                section_content_str = "\n".join(section_content)
                section_content_str = pattern.sub("", section_content_str)
                statement = self._create_statement(
                    statement_id, section_content_str.strip()
                )
                implemented_req.statements.append(statement)
        else:
            self._add_response_by_status(
                implemented_req, oscal_status, control_response.strip()
            )

    def _process_rule_ids(self, rule_ids: List[str]) -> List[str]:
        """
        Process rule ids.
        Notes: Rule ids with an "=" are parameters and should not be included
        # when searching for rules.
        """
        processed_rule_ids: List[str] = list()
        for rule_id in rule_ids:
            parts = rule_id.split("=")
            if len(parts) == 1:
                processed_rule_ids.append(rule_id)
        return processed_rule_ids

    def _attach_rules(
        self,
        type_with_props: TypeWithProps,
        rule_ids: List[str],
        rules_transformer: RulesTransformer,
    ) -> None:
        """Add rules to a type with props."""
        all_props: List[Property] = as_list(type_with_props.props)
        all_rule_ids = self.rules_by_id.keys()
        error_rules = list(filter(lambda x: x not in all_rule_ids, rule_ids))
        if error_rules:
            raise ValueError(f"Could not find rules: {', '.join(error_rules)}")
        rule_properties: List[Property] = rules_transformer.get_rule_id_props(rule_ids)
        all_props.extend(rule_properties)
        type_with_props.props = none_if_empty(all_props)

    def _add_set_parameters(
        self, control_implementation: ControlImplementation
    ) -> None:
        """Add set parameters to a control implementation."""
        rules: List[RuleInfo] = list(self.rules_by_id.values())
        params = []
        for rule in rules:
            params.extend(rule._parameters)
        param_selections = {param.id: param.selected_value for param in params}

        if param_selections:
            all_set_params: List[SetParameter] = as_list(
                control_implementation.set_parameters
            )
            for param_id, value in param_selections.items():
                set_param = generate_sample_model(SetParameter)
                set_param.param_id = param_id
                set_param.values = [value]
                all_set_params.append(set_param)
            control_implementation.set_parameters = none_if_empty(all_set_params)

    def _create_implemented_requirement(
        self, control: Control, rules_transformer: RulesTransformer
    ) -> Optional[ImplementedRequirement]:
        """Create implemented requirement from a control object"""

        logger.info(f"Creating implemented requirement for {control.id}")
        control_id = self.catalog_helper.get_id(control.id)
        if control_id:
            implemented_req = generate_sample_model(ImplementedRequirement)
            implemented_req.control_id = control_id
            self._handle_response(implemented_req, control)
            # Rules and variables are collected from rules section in control files, but for
            # product agnostic control files some rules are unselected or variables are overridden
            # in the profile level of products and should not be included in transformed content.
            unselected_rules_or_vars = list(
                filter(lambda x: x not in self.rules, control.rules)
            )
            if unselected_rules_or_vars:
                logger.info(
                    f"Unselected rules or vars in {self.cac_profile_id} profile for {self.product}:"
                    f"{', '.join(unselected_rules_or_vars)}"
                )
            only_rules_in_profile = list(
                filter(lambda x: x in self.rules, control.rules)
            )
            rule_ids = self._process_rule_ids(only_rules_in_profile)
            self._attach_rules(implemented_req, rule_ids, rules_transformer)
            return implemented_req
        return None

    def _create_control_implementation(self) -> ControlImplementation:
        """Create control implementation for a component."""
        ci = generate_sample_model(ControlImplementation)
        ci.source = self.profile_href
        all_implement_reqs = list()
        self._get_controls()
        rules_transformer = RulesTransformer(
            self.cac_content_root,
            self.product,
            self.cac_profile,
        )

        for control in self.controls:
            implemented_req = self._create_implemented_requirement(
                control, rules_transformer
            )
            if implemented_req:
                all_implement_reqs.append(implemented_req)
        ci.implemented_requirements = all_implement_reqs
        self._add_set_parameters(ci)

        # Add framework prop for complytime consumption. This should be the
        # originating CaC profile name.
        ci.props = as_list(ci.props)
        frameworkProp = generate_sample_model(Property)
        frameworkProp.name = const.FRAMEWORK_SHORT_NAME
        frameworkProp.value = self.cac_profile_id
        frameworkProp.ns = TRESTLE_GENERIC_NS
        ci.props.append(frameworkProp)

        return ci

    def _add_control_implementations(
        self, oscal_component: DefinedComponent
    ) -> DefinedComponent:
        """Add control implementations to OSCAL component."""
        self._get_source(self.oscal_profile)
        profile_resolver = ProfileResolver()
        resolved_catalog: Catalog = profile_resolver.get_resolved_profile_catalog(
            pathlib.Path(self.working_dir),
            self.profile_path,
            block_params=False,
            params_format="[.]",
            show_value_warnings=True,
        )
        self.catalog_helper.load(resolved_catalog)

        control_implementation: ControlImplementation = (
            self._create_control_implementation()
        )
        oscal_component.control_implementations = [control_implementation]
        return oscal_component

    def _update_compdef(
        self, cd_json: pathlib.Path, oscal_component: DefinedComponent
    ) -> None:
        """Update existed OSCAL component definition."""
        compdef = ComponentDefinition.oscal_read(cd_json)
        components_titles = []
        updated = False
        for index, component in enumerate(compdef.components):
            components_titles.append(component.title)
            # Check if the component exists and needs to be updated
            if component.title == oscal_component.title:
                if not ModelUtils.models_are_equivalent(
                    component.props, oscal_component.props, ignore_all_uuid=True
                ):
                    logger.info(f"Component props of {component.title} has an update")
                    compdef.components[index].props = oscal_component.props
                    updated = True
                if not ModelUtils.models_are_equivalent(
                    component.control_implementations,
                    oscal_component.control_implementations,
                    ignore_all_uuid=True,
                ):
                    logger.info(
                        f"Control implementations of {component.title} has an update"
                    )
                    compdef.components[index].control_implementations = (
                        oscal_component.control_implementations
                    )
                    updated = True
                if updated:
                    break

        if oscal_component.title not in components_titles:
            logger.info(f"Component {oscal_component.title} needs to be added")
            compdef.components.append(oscal_component)
            updated = True

        if updated:
            compdef.metadata.version = str(
                "{:.1f}".format(float(compdef.metadata.version) + 0.1)
            )
            ModelUtils.update_last_modified(compdef)
            compdef.oscal_write(cd_json)
            logger.info(f"Component definition: {cd_json} is updated")
            logger.debug(
                f"Component definition: {cd_json} was updated for {self.product}."
            )
        else:
            logger.info(f"No update in component definition: {cd_json}")

    def _create_compdef(
        self, cd_json: pathlib.Path, oscal_component: DefinedComponent
    ) -> None:
        """Create a component definition in OSCAL."""
        component_definition = generate_sample_model(ComponentDefinition)
        component_definition.metadata.title = f"Component definition for {self.product}"
        component_definition.metadata.version = "1.0"
        component_definition.components = list()
        cd_dir = pathlib.Path(os.path.dirname(cd_json))
        cd_dir.mkdir(exist_ok=True, parents=True)
        component_definition.components.append(oscal_component)
        component_definition.oscal_write(cd_json)
        logger.debug(f"Component definition: {cd_json} was created for {self.product}.")

    def _create_or_update_compdef(self) -> None:
        """Create or update component definition for specified CaC profile."""
        oscal_component = generate_sample_model(DefinedComponent)
        oscal_component = self._add_props(oscal_component)
        oscal_component = self._add_control_implementations(oscal_component)

        repo_path = pathlib.Path(self.working_dir)
        cd_json: pathlib.Path = ModelUtils.get_model_path_for_name_and_class(
            repo_path,
            # Updating the path reference for transformed component-definitions
            f"{self.product}/{self.oscal_profile}",
            ComponentDefinition,
            FileContentType.JSON,
        )
        if cd_json.exists():
            logger.info(f"The component definition for {self.product} exists.")
            self._update_compdef(cd_json, oscal_component)
            logger.debug(
                f"The component definition for {self.product} was updated at {cd_json}."
            )
        else:
            logger.info(f"Creating component definition for product {self.product}")
            self._create_compdef(cd_json, oscal_component)
            logger.debug(
                f"The component definition for {self.product} was created at {cd_json}."
            )

    def execute(self) -> int:
        """Execute task to create or update product component definition."""
        # Check the product existence in CaC content.
        # Comment below due to the hardcoded product_directories in get_all,
        # all_products = list(set().union(*get_all(self.cac_content_root)))
        # if self.product not in all_products:
        #     raise TaskException(f"Product {self.product} does not exist.")

        # Collect all selected rules in product profile
        self._collect_rules()
        # Create or update product component definition
        self._create_or_update_compdef()

        return const.SUCCESS_EXIT_CODE
