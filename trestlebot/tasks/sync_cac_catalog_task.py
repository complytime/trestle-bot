# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Red Hat, Inc.

"""Trestle Bot Sync CaC Catalog Tasks"""

from __future__ import annotations

import itertools
import logging
import os
import pathlib
import re
from typing import List, Optional

import ssg
from ssg.controls import Policy
from trestle.common import const as common_const
from trestle.common.model_utils import ModelUtils
from trestle.core.generators import generate_sample_model
from trestle.core.models.file_content_type import FileContentType
from trestle.oscal import common
from trestle.oscal.catalog import Catalog, Control, Group

from trestlebot import const
from trestlebot.tasks.base_task import TaskBase


logger = logging.getLogger(__name__)


def get_oscal_control_title(
    cac_control_id: str, cac_control_title: Optional[str], parent_title: Optional[str]
) -> str:
    if not cac_control_title:
        return cac_control_id
    if cac_control_title.startswith(cac_control_id):  # No removeprefix in py3.8
        prefix_len = len(cac_control_id)
        title = cac_control_title[prefix_len:]
    else:
        title = cac_control_title
    title = re.sub(r"^\W*", "", title)
    if parent_title:
        group, _, section = title.partition("|")
        group = group.strip()
        if group.lower() in parent_title.lower():
            title = section
            title = title.strip()
    title = re.sub(r"^\W*", "", title)
    title = title.title()
    return title


def control_cac_to_oscal(
    cac_control: ssg.controls.Control,
    group_id: str,
    oscal_path: List[str],
    parent: Optional[Control | Group] = None,
) -> Control:
    # 1. Create control and populate basics
    oscal_control = generate_sample_model(Control)
    if oscal_path:
        control_id_str = ".".join(oscal_path)
        cac_control_id = "-".join([group_id, control_id_str])
    else:
        cac_control_id = group_id
    oscal_control.id = cac_control_id
    oscal_control.class_ = "CAC_IMPORT"
    oscal_title = get_oscal_control_title(
        cac_control.id, cac_control.title, parent.title if parent else None
    )
    oscal_control.title = oscal_title
    oscal_control.props = []
    oscal_control.params = []
    oscal_control.parts = []
    if oscal_path:
        sort_control_path = ".".join(part.zfill(2) for part in oscal_path)
        sort_id = f"{group_id}-{sort_control_path}"
    else:
        sort_id = group_id
    oscal_control.props.append(
        # Use original id to ease transforming back to CaC
        common.Property(name=common_const.LABEL, value=cac_control.id)
    )
    oscal_control.props.append(
        common.Property(name=common_const.SORT_ID, value=sort_id)
    )

    # 2. Populate params
    if cac_control.description:
        assignments = re.findall(r"\[Assignment: (.*?)]", cac_control.description) or []
        assignment_ids = []
        for param_n, assignment in enumerate(assignments, 1):
            assignment_ids.append(f"{cac_control_id}_prm_{param_n}")
        for assignment_id, assignment in zip(assignment_ids, assignments):
            oscal_control.params.append(
                common.Parameter(id=assignment_id, label=assignment)
            )
        statement = re.search(r"(.*)$", cac_control.description, re.MULTILINE)
        if statement:
            statement_text = statement.group(1)
            for assignment_id, assignment in zip(assignment_ids, assignments):
                statement_text = statement_text.replace(
                    assignment, " {{ insert: param, " + assignment_id + " }} "
                )
                statement_text = statement_text.replace(
                    f"{cac_control_id}_prm_{assignment_id}", ""
                )
            oscal_control.parts.append(
                common.Part(id=f"{cac_control_id}_smt", name=common_const.STATEMENT)
            )

        guidance = re.search(
            r"^(?:Supplemental )?Guidance: (.*?)$",
            cac_control.description,
            re.MULTILINE,
        )
        if guidance:
            # TODO: add guidance const to trestle
            oscal_control.parts.append(
                common.Part(
                    id=f"{cac_control_id}_gdn", name="guidance", prose=guidance.group(1)
                )
            )
    return oscal_control


class SyncCacCatalogTask(TaskBase):
    """Sync CaC policy controls to OSCAL catalog task."""

    cac_content_root: pathlib.Path
    policy_id: str
    oscal_catalog: str

    def __init__(
        self,
        cac_content_root: pathlib.Path,
        policy_id: str,
        oscal_catalog: str,
        working_dir: str,
    ) -> None:
        """Initialize CaC catalog sync task."""
        super().__init__(working_dir, None)
        self.cac_content_root = cac_content_root
        self.policy_id = policy_id
        self.oscal_catalog = oscal_catalog
        self.rules: List[str] = []

    def _load_policy_controls(self) -> Policy:
        """Load a CaC policy."""
        cac_controls_path = self.cac_content_root / "controls"
        for policy_yaml in itertools.chain(
            cac_controls_path.rglob("*.[Yy][Mm][Ll]"),
            cac_controls_path.rglob("*.[Yy][Aa][Mm][Ll]"),
        ):
            if policy_yaml.is_file():
                try:
                    policy = Policy(policy_yaml)
                    policy.load()
                    if policy.id == self.policy_id:
                        return policy
                except Exception as e:
                    logger.debug("Failed to load Policy %s", policy_yaml, exc_info=e)
        raise RuntimeError(
            "Failed to load CaC policy controls."
            f" No policy with id {self.policy_id} found."
        )

    def _sync_catalog(
        self,
        oscal_catalog: Catalog,
        policy: Policy,
    ) -> None:
        """Update an OSCAL catalog from a CaC Policy."""
        for cac_control in policy.controls:
            # 1. extract oscal-compatible identifiers
            group_id, *control_path = [
                x.lower() for x in re.findall(r"\w+", cac_control.id)
            ]
            # 2. find the correct place in oscal
            # 2a. find the group
            group = None
            # Warning: the line below is only compatible with pydantic 1
            # and will need to be updated if trestle updates to pydantic 2
            if Group.__fields__["id"].type_.regex.match(group_id) is None:
                group_id = f"{policy.id}_{group_id}"
            for g in oscal_catalog.groups:
                if g.id == group_id:
                    group = g
                    break
            # 2b. If the group doesn't exist, create it
            if not group:
                group = generate_sample_model(Group)
                group.id = group_id
                oscal_catalog.groups.append(group)
            if not group.controls:
                group.controls = []
            parent = group
            # 3. If this is a nested control, get the parent control
            is_nested_control = len(control_path) > 1
            if is_nested_control:
                # search the controls for the next path until the last path part
                for parent_path_len in range(1, len(control_path)):
                    parent_id = f"{group_id}-{'.'.join(control_path[:parent_path_len])}"
                    found = False
                    for control in parent.controls:
                        if control.id == parent_id:
                            if not control.controls:
                                control.controls = []
                            parent = control
                            found = True
                            break
                    if not found:
                        # insert an empty parent control
                        control = generate_sample_model(Control)
                        control.controls = []
                        control.id = parent_id
                        parent.controls.append(control)
                        parent = control
            # 4. Find the associated oscal control to the cac control
            # 4a. Map the cac control onto a new oscal control
            new_control = control_cac_to_oscal(
                cac_control, group_id, control_path, parent
            )
            # 4b. Find a control to merge into
            matched_control = None
            for control in parent.controls:
                if control.id == new_control.id:
                    matched_control = control
                    break
            # 4c. Merge mapped cac control into oscal control
            # (note: CatalogAPI.merge_catalog doesn't work for this)
            if not matched_control:
                parent.controls.append(new_control)
            else:
                # 4c1. params
                if new_control.params:
                    for new_param in new_control.params:
                        if matched_control.params:
                            matched_params = [mp.id for mp in matched_control.params]
                            if new_param.id not in matched_params:
                                matched_control.params.append(new_param)
                # 4c2. props
                if new_control.props:
                    for new_prop in new_control.props:
                        if matched_control.props:
                            matched_props = [mp.name for mp in matched_control.props]
                            if new_prop.name not in matched_props:
                                matched_control.props.append(new_prop)
                # 4c3. links
                if new_control.links:
                    for new_link in new_control.links:
                        if matched_control.links:
                            matched_links = [mp.href for mp in matched_control.links]
                            if new_link.href not in matched_links:
                                matched_control.links.append(new_link)
                # 4c4. parts
                if new_control.parts:
                    for new_part in new_control.parts:
                        if matched_control.parts:
                            matched_parts = [mp.id for mp in matched_control.parts]
                            if new_part.id not in matched_parts:
                                matched_control.parts.append(new_part)

    def _create_or_update_catalog(self, policy: Policy) -> None:
        """Create or update catalog for specified CaC profile."""
        repo_path = pathlib.Path(self.working_dir)
        oscal_json = ModelUtils.get_model_path_for_name_and_class(
            repo_path, self.oscal_catalog, Catalog, FileContentType.JSON
        )
        if oscal_json is None:
            # Should never happen
            raise RuntimeError(
                "get_model_path_for_name_and_class()"
                "was expected to return a Catalog, but the API changed."
            )
        if oscal_json.exists():
            logger.info(f"The catalog for {self.policy_id} exists.")
            oscal_catalog = Catalog.oscal_read(oscal_json)
        else:
            logger.info(f"Creating catalog {self.policy_id}")
            oscal_catalog = generate_sample_model(Catalog)
            oscal_catalog.metadata.title = f"Catalog for {self.policy_id}"
            oscal_catalog.params = []
            oscal_catalog.groups = []
            # oscal_catalog.back_matter = None

        self._sync_catalog(oscal_catalog, policy)

        catalog_dir = pathlib.Path(os.path.dirname(oscal_json))
        catalog_dir.mkdir(exist_ok=True, parents=True)
        oscal_catalog.oscal_write(oscal_json)

        logger.info("CaC catalog sync complete.")

    def execute(self) -> int:
        """Execute task to sync a CaC profile to an OSCAL catalog."""
        policy = self._load_policy_controls()
        self._create_or_update_catalog(policy)
        return const.SUCCESS_EXIT_CODE
