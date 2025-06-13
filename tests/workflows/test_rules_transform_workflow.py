# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Test the rules transformation workflow from a Task Class perspective."""

import os
import pathlib

from trestle.common.load_validate import load_validate_model_name
from trestle.oscal import component as comp

import complyscribe.const as const
from complyscribe.tasks.assemble_task import AssembleTask
from complyscribe.tasks.authored.compdef import AuthoredComponentDefinition
from complyscribe.tasks.regenerate_task import RegenerateTask
from complyscribe.tasks.rule_transform_task import RuleTransformTask
from complyscribe.transformers.yaml_transformer import ToRulesYAMLTransformer
from tests.testutils import setup_for_profile


test_component_definition = "test_component_definition"
test_profile = "simplified_nist_profile"
test_md_path = "md_compdef"


def test_rules_transform_workflow(tmp_trestle_dir: str) -> None:
    """Test the rules transformation workflow for component definitions."""

    trestle_root_path = pathlib.Path(tmp_trestle_dir)

    # Environment setup and initial rule generation
    _ = setup_for_profile(trestle_root_path, test_profile, test_profile)

    authored_compdef = AuthoredComponentDefinition(trestle_root=tmp_trestle_dir)
    authored_compdef.create_new_default(
        profile_name=test_profile,
        compdef_name=test_component_definition,
        comp_title="Test",
        comp_description="Test component definition",
        comp_type="service",
    )

    # Transform
    transform = RuleTransformTask(
        tmp_trestle_dir, const.RULES_VIEW_DIR, ToRulesYAMLTransformer()
    )
    transform.execute()

    # Load the component definition
    compdef: comp.ComponentDefinition
    compdef, _ = load_validate_model_name(
        trestle_root_path, test_component_definition, comp.ComponentDefinition
    )

    assert len(compdef.components) == 1
    component = compdef.components[0]

    assert component.title == "Test"
    assert component.description == "Test component definition"
    assert component.type == "service"
    assert len(component.props) == 24
    assert len(component.control_implementations) == 1
    assert (
        component.control_implementations[0].source
        == f"trestle://profiles/{test_profile}/profile.json"
    )

    last_modified = compdef.metadata.last_modified

    # Run regenerate
    regenerate = RegenerateTask(authored_compdef, test_md_path)
    regenerate.execute()

    assert os.path.exists(
        os.path.join(trestle_root_path, test_md_path, test_component_definition)
    )

    # Run assemble
    assemble = AssembleTask(authored_compdef, test_md_path)
    assemble.execute()

    # Load the component definition
    compdef, _ = load_validate_model_name(
        trestle_root_path, test_component_definition, comp.ComponentDefinition
    )

    assert len(compdef.components) == 1
    component = compdef.components[0]

    # Asset last modified is updated, but all expected information is still present
    assert compdef.metadata.last_modified > last_modified

    assert component.title == "Test"
    assert component.description == "Test component definition"
    assert component.type == "service"
    assert len(component.props) == 24
    assert len(component.control_implementations) == 1
    assert (
        component.control_implementations[0].source
        == f"trestle://profiles/{test_profile}/profile.json"
    )
