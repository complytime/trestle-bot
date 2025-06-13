# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Transform rules from existing Compliance as Code locations into OSCAL properties."""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from ssg.products import load_product_yaml, product_yaml_path
from ssg.profiles import get_profiles_from_products
from ssg.rules import find_rule_dirs_in_paths, get_rule_dir_id, get_rule_dir_yaml
from ssg.variables import (
    get_variable_options,
    get_variable_property,
    get_variables_from_profiles,
)
from ssg.yaml import open_and_macro_expand_from_dir
from trestle.common.const import TRESTLE_GENERIC_NS
from trestle.core.generators import generate_sample_model
from trestle.oscal.common import Property
from trestle.tasks.csv_to_oscal_cd import (
    PARAMETER_DESCRIPTION,
    PARAMETER_ID,
    PARAMETER_VALUE_ALTERNATIVES,
    RULE_DESCRIPTION,
    RULE_ID,
    _RuleSetIdMgr,
)


logger = logging.getLogger(__name__)

TRESTLE_CD_NS = f"{TRESTLE_GENERIC_NS}/cd"


def get_component_info(product_name: str, cac_path: str) -> Tuple[str, str]:
    """Get the product name from product yml file via the SSG library."""
    if product_name and cac_path:
        product_yml_path = product_yaml_path(cac_path, product_name)
        product = load_product_yaml(product_yml_path)
        component_title = product._primary_data.get("product")
        component_description = product._primary_data.get("full_name")
        return (component_title, component_description)
    else:
        raise ValueError("component_title is empty or None")


def transform_property(prop: Property) -> Dict[str, str]:
    return {
        "name": prop.name,
        "ns": prop.ns,
        "value": prop.value,
        "remarks": prop.remarks,
    }


def get_validation_component_mapping(props: Property) -> List[Dict[str, str]]:
    """
    Adds a new "Check_Id" and "Check_Description" to the props based on the
    "Rule_Id" value and "Rule_Description".

    Args:
        props (Property): The input of Property.

    Returns:
        List[Dict]: The updated list with the new "Check_Id" and
        "Check_Description" entry.
    """
    transformed_list = [transform_property(prop) for prop in props]
    rule_check_mapping = []
    for prop in transformed_list:
        rule_check_mapping.append(prop)
        if prop["name"] == "Rule_Id":
            check_id_entry = {
                "name": "Check_Id",
                "ns": prop["ns"],
                "value": prop["value"],
                "remarks": prop["remarks"],
            }
        if prop["name"] == "Rule_Description":
            check_description_entry = {
                "name": "Check_Description",
                "ns": prop["ns"],
                "value": prop["value"],
                "remarks": prop["remarks"],
            }
            # Append the Check entry follow Rule_Description
            rule_check_mapping.append(check_id_entry)
            rule_check_mapping.append(check_description_entry)
        # If this rule has paramters, append the Check entry follow paramters
        if prop["name"] == "Parameter_Value_Alternatives":
            rule_check_mapping.remove(check_id_entry)
            rule_check_mapping.remove(check_description_entry)
            rule_check_mapping.append(check_id_entry)
            rule_check_mapping.append(check_description_entry)
    return rule_check_mapping


def add_prop(name: str, value: str, remarks: Optional[str] = None) -> Property:
    """Add a property to a set of rule properties."""
    prop = generate_sample_model(Property)
    prop.name = name
    prop.value = value
    if remarks:
        prop.remarks = remarks
    prop.ns = TRESTLE_CD_NS  # type: ignore
    return prop


def get_benchmark_root(root: str, product: str) -> str:
    """Get the benchmark root."""
    product_yml_path = product_yaml_path(root, product)
    product_yaml = load_product_yaml(product_yml_path)
    product_dir = product_yaml.get("product_dir")
    benchmark_root = os.path.join(product_dir, product_yaml.get("benchmark_root"))
    return benchmark_root


def get_profile_params(root: str, product: str, profile_id: str) -> Dict[str, Any]:
    profiles = get_profiles_from_products(root, [product], sorted=True)
    params = {}
    for profile in profiles:
        if profile.profile_id == profile_id:
            params = get_variables_from_profiles([profile])
            break
    return params


class ParamInfo:
    """Stores rule parameter information."""

    def __init__(self, param_id: str, description: str) -> None:
        """Initialize."""
        self._id = param_id
        self._description = description
        self._value = ""
        self._options: Dict[str, str] = dict()

    @property
    def id(self) -> str:
        """Get the id."""
        return self._id

    @property
    def description(self) -> str:
        """Get the description."""
        return self._description

    @property
    def selected_value(self) -> str:
        """Get the selected value."""
        return self._value

    @property
    def options(self) -> Dict[str, str]:
        """Get the options."""
        return self._options

    def set_selected_value(self, value: str) -> None:
        """Set the selected value."""
        self._value = value

    def set_options(self, value: Dict[str, str]) -> None:
        """Set the options."""
        self._options = value


class RuleInfo:
    """Stores rule information."""

    def __init__(self, rule_id: str, rule_dir: str) -> None:
        """Initialize."""
        self._id = rule_id
        self._description = ""
        self._rule_dir = rule_dir
        self._parameters: List[ParamInfo] = list()

    @property
    def id(self) -> str:
        """Get the id."""
        return self._id

    @property
    def description(self) -> str:
        """Get the description."""
        return self._description

    @property
    def rule_dir(self) -> str:
        """Get the rule directory."""
        return self._rule_dir

    def add_description(self, value: str) -> None:
        """Add a rule description."""
        self._description = value

    def add_parameter(self, value: ParamInfo) -> None:
        """Add a rule parameter."""
        self._parameters.append(value)


class RulesTransformer:
    """Transforms rules into properties for creating component definitions."""

    def __init__(
        self,
        root: str,
        product: str,
        profile: str,
    ) -> None:
        """Initialize."""
        self.root = root
        self.product = product

        benchmark_root = get_benchmark_root(root, self.product)
        self.rules_dirs_for_product: Dict[str, str] = dict()
        for dir_path in find_rule_dirs_in_paths([benchmark_root]):
            rule_id = get_rule_dir_id(dir_path)
            self.rules_dirs_for_product[rule_id] = dir_path

        self._rules_by_id: Dict[str, RuleInfo] = dict()
        self.profile_id = os.path.basename(profile).split(".profile")[0]
        self.profile_params = get_profile_params(root, product, self.profile_id)

    def _new_param_obj(self, param_id: str) -> ParamInfo:
        param_description = get_variable_property(self.root, param_id, "description")
        param_obj = ParamInfo(param_id, param_description)
        return param_obj

    def _get_params(self, root: str, rule_obj: RuleInfo) -> None:
        # Here need to add params only in this rule.
        for param_id, param_data in self.profile_params.items():
            param_obj = self._new_param_obj(param_id)
            selected_value = param_data[self.product][self.profile_id]
            param_obj.set_selected_value(selected_value)
            options = get_variable_options(root, param_id)
            param_obj.set_options(options)
            rule_obj.add_parameter(param_obj)

    def add_rules(self, rules: List[str]) -> None:
        """
        Load a set of rules into rule objects based on ids and
        add them to the rules_by_id dictionary.
        Args:
            rules: A list of rule ids.
        Notes: This attempt to load all rules and will raise an error if any fail.
        """
        rule_errors: List[str] = list()
        for rule_id in rules:
            error = self._add_rule(rule_id)
            if error:
                rule_errors.append(error)

        if len(rule_errors) > 0:
            raise RuntimeError(
                f"Error loading rules: \
                    \n{', '.join(rule_errors)}"
            )

    def _add_rule(self, rule_id: str) -> Optional[str]:
        """Add a single rule to the rules_by_id dictionary."""
        try:
            if rule_id not in self._rules_by_id:
                rule_obj = self._new_rule_obj(rule_id)
                self._load_rule_yaml(rule_obj)
                self._rules_by_id[rule_id] = rule_obj
        except ValueError as e:
            return f"Could not find rule {rule_id}: {e}"
        except FileNotFoundError as e:
            return f"Could not load rule {rule_id}: {e}"
        return None

    def _new_rule_obj(self, rule_id: str) -> RuleInfo:
        """Create a new rule object."""
        rule_dir = self._from_product_dir(rule_id)
        if not rule_dir:
            raise ValueError(f"Could not find rule {rule_id} directory.")
            # Or skip here if not found?
        rule_obj = RuleInfo(rule_id, rule_dir)
        return rule_obj

    def _from_product_dir(self, rule_id: str) -> Optional[str]:
        """Locate the rule dir in the product directory."""
        if rule_id not in self.rules_dirs_for_product:
            return None
        return self.rules_dirs_for_product.get(rule_id)

    def _load_rule_yaml(self, rule_obj: RuleInfo) -> None:
        """
        Update the rule object with the rule yaml data.

        Args:
            rule_obj: The rule object where collection rule data is stored.
        """
        product_yml_path = product_yaml_path(self.root, self.product)
        product_yaml = load_product_yaml(product_yml_path)
        rule_file = get_rule_dir_yaml(rule_obj.rule_dir)
        rule_yaml = open_and_macro_expand_from_dir(
            rule_file, self.root, substitutions_dict=product_yaml._data_as_dict
        )

        rule_obj.add_description(rule_yaml["title"].replace("\n", " ").strip())
        self._get_params(self.root, rule_obj)

    @staticmethod
    def _get_params_properties(
        ruleset: str, param_info: ParamInfo, suffix: str
    ) -> List[Property]:
        """Get a set of parameter properties for a rule object."""
        id_prop = add_prop(PARAMETER_ID + suffix, param_info.id, ruleset)
        description_prop = add_prop(
            PARAMETER_DESCRIPTION + suffix,
            param_info.description.replace("\n", " ").strip(),
            ruleset,
        )
        alternative_prop = add_prop(
            PARAMETER_VALUE_ALTERNATIVES + suffix,
            str(param_info.options),
            ruleset,
        )
        return [id_prop, description_prop, alternative_prop]

    def _get_rule_properties(self, ruleset: str, rule_obj: RuleInfo) -> List[Property]:
        """Get a set of rule properties for a rule object."""
        rule_properties: List[Property] = list()
        # Add rule properties for the ruleset
        rule_properties.append(add_prop(RULE_ID, rule_obj.id, ruleset))
        rule_properties.append(
            add_prop(RULE_DESCRIPTION, rule_obj.description, ruleset)
        )
        for index, param in enumerate(rule_obj._parameters):
            suffix = "" if len(rule_obj._parameters) == 1 else f"_{index}"
            rule_properties.extend(self._get_params_properties(ruleset, param, suffix))

        return rule_properties

    def get_rule_id_props(self, rule_ids: List[str]) -> List[Property]:
        """Get the rule props with rule ids."""
        props: List[Property] = [add_prop(RULE_ID, rule_id) for rule_id in rule_ids]
        return props

    def get_all_rule_objs(self) -> Dict[str, RuleInfo]:
        return self._rules_by_id

    def transform(self, rule_objs: List[RuleInfo]) -> List[Property]:
        """Get the rules properties for a set of rule ids."""
        rule_properties: List[Property] = list()

        start_val = -1
        for i, rule_obj in enumerate(rule_objs):
            rule_set_mgr = _RuleSetIdMgr(start_val + i, len(rule_objs))
            rule_set_props = self._get_rule_properties(
                rule_set_mgr.get_next_rule_set_id(), rule_obj
            )
            rule_properties.extend(rule_set_props)
        return rule_properties
