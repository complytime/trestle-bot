# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

from typing import Tuple

import ssg.controls
from git import Repo
from trestle.oscal.catalog import Group

from trestlebot.tasks.sync_cac_catalog_task import control_cac_to_oscal


def test_control_cac_to_oscal_lists_non_empty(tmp_repo: Tuple[str, Repo]) -> None:
    cac_control = ssg.controls.Control()
    cac_control.id = "AC-1"
    cac_control.levels = ["high", "moderate", "low"]
    cac_control.notes = "Section a: AC-1(a) is an organizational control outside the scope of OpenShift configuration.\n\nSection b: AC-1(b) is an organizational control outside the scope of OpenShift configuration."
    cac_control.title = "AC-1 - ACCESS CONTROL POLICY AND PROCEDURES"
    cac_control.description = """The organization:
 a. Develops, documents, and disseminates to [Assignment: organization-defined personnel or roles]:
   1. An access control policy that addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and
   2. Procedures to facilitate the implementation of the access control policy and associated access controls; and
 b. Reviews and updates the current:
   1. Access control policy [Assignment: organization-defined frequency]; and
   2. Access control procedures [Assignment: organization-defined frequency].

Supplemental Guidance: This control addresses the establishment of policy and procedures for the effective implementation of selected security controls and control enhancements in the AC family. Policy and procedures reflect applicable federal laws, Executive Orders, directives, regulations, policies, standards, and guidance. Security program policies and procedures at the organization level may make the need for system-specific policies and procedures unnecessary. The policy can be included as part of the general information security policy for organizations or conversely, can be represented by multiple policies reflecting the complex nature of certain organizations. The procedures can be established for the security program in general and for particular information systems, if needed. 

The organizational risk management strategy is a key factor in establishing policy and procedures. Related control: PM-9.
Control Enhancements: None.
References: NIST Special Publications 800-12, 800-100.

AC-1 (b) (1) [at least annually] 
AC-1 (b) (2) [at least annually or whenever a significant change occurs]"""
    cac_control.rationale = None
    cac_control.automated = "no"
    cac_control.status = "not applicable"
    cac_control.mitigation = None
    cac_control.artifact_description = None
    cac_control.status_justification = None
    cac_control.fixtext = None
    cac_control.check = None
    cac_control.controls = []
    cac_control.tickets = []
    cac_control.original_title = None
    cac_control.related_rules = []
    cac_control.rules = []
    parent = Group(id="ac", title="REPLACE_ME")
    oscal_control = control_cac_to_oscal(cac_control, "ac", ["1"], parent)
    assert oscal_control is not None
    assert len(oscal_control.params) == 3
    assert len(oscal_control.props) == 2
    assert len(oscal_control.parts) == 2


def test_control_cac_to_oscal_lists_empty(tmp_repo: Tuple[str, Repo]) -> None:
    cac_control = ssg.controls.Control()
    cac_control.id = "AC-1"
    cac_control.levels = ["high", "moderate", "low"]
    cac_control.notes = "Section a: AC-1(a) is an organizational control outside the scope of OpenShift configuration.\n\nSection b: AC-1(b) is an organizational control outside the scope of OpenShift configuration."
    cac_control.title = "AC-1 - ACCESS CONTROL POLICY AND PROCEDURES"
    cac_control.description = None  # empty params and parts
    cac_control.rationale = None
    cac_control.automated = "no"
    cac_control.status = "not applicable"
    cac_control.mitigation = None
    cac_control.artifact_description = None
    cac_control.status_justification = None
    cac_control.fixtext = None
    cac_control.check = None
    cac_control.controls = []
    cac_control.tickets = []
    cac_control.original_title = None
    cac_control.related_rules = []
    cac_control.rules = []
    parent = Group(id="ac", title="REPLACE_ME")
    oscal_control = control_cac_to_oscal(cac_control, "ac", ["1"], parent)
    assert oscal_control is not None
    assert oscal_control.params is None, "empty list should be None"
    assert oscal_control.parts is None, "empty list should be None"
