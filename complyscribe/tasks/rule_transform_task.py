# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""ComplyScribe Rule Transform Tasks"""

import configparser
import logging
import os
import pathlib
from typing import List, Optional

import trestle.common.const as trestle_const
from trestle.tasks.base_task import TaskOutcome
from trestle.tasks.csv_to_oscal_cd import CsvToOscalComponentDefinition

import complyscribe.const as const
from complyscribe.tasks.base_task import ModelFilter, TaskBase, TaskException
from complyscribe.transformers.base_transformer import RulesTransformerException
from complyscribe.transformers.csv_transformer import CSVBuilder
from complyscribe.transformers.yaml_transformer import ToRulesYAMLTransformer


logger = logging.getLogger(__name__)


class RuleTransformTask(TaskBase):
    """
    Transform rules into OSCAL content.
    """

    def __init__(
        self,
        working_dir: str,
        rules_view_dir: str,
        rule_transformer: ToRulesYAMLTransformer,
        model_filter: Optional[ModelFilter] = None,
    ) -> None:
        """
        Initialize transform task.

        Args:
            working_dir: Working directory to complete operations in
            rule_view_dir: Location of directory containing components with to read rules from
            rule_transformer: Transformer to use for rule transformation to TrestleRule
            model_filter: Optional filter to apply to the task to include or exclude models
            from processing.

        Notes:
            The rule_view_dir is expected to be a directory containing directories of
            components definitions. Each component definition directory is
            expected to contain a directories separated by component name. Each component directory is
            expected to contain rule files in YAML format.
        """

        self._rule_view_dir = rules_view_dir
        self._rule_transformer: ToRulesYAMLTransformer = rule_transformer
        super().__init__(working_dir, model_filter)

    def execute(self) -> int:
        """Execute task"""
        return self._transform()

    def _transform(self) -> int:
        """
        Transform rule objects in the rules view into an OSCAL component definitions.

        Returns:
         0 on success, raises an exception if not successful
        """
        working_path: pathlib.Path = pathlib.Path(self.working_dir)
        search_path: pathlib.Path = working_path.joinpath(self._rule_view_dir)

        for compdef in self.iterate_models(search_path):
            self._transform_components(compdef)

        return const.SUCCESS_EXIT_CODE

    def _transform_components(self, component_definition_path: pathlib.Path) -> None:
        """Transform components into an OSCAL component definition."""
        csv_builder: CSVBuilder = CSVBuilder()
        logger.info(
            f"Transforming rules for component definition {component_definition_path.name}"
        )

        # To report all rule errors at once, we collect them in a list and
        # pretty print them in a raised exception
        transformation_errors: List[str] = []
        for component in self.iterate_models(component_definition_path):
            logger.debug(f"Transforming rules for component {component.name}")
            for rule_path in self.iterate_models(component):
                # Load the rule into memory as a stream to process
                rule_stream = rule_path.read_text()

                try:
                    rule = self._rule_transformer.transform(rule_stream)
                    csv_builder.add_row(rule)
                except RulesTransformerException as e:
                    transformation_errors.append(f"{rule_path.as_posix()}: {e}")

        if len(transformation_errors) > 0:
            transformation_error_str = "\n".join(transformation_errors)
            raise TaskException(
                f"Failed to transform rules for component definition {component_definition_path.name}: \
                    {transformation_error_str}"
            )
        if csv_builder.row_count == 0:
            raise TaskException(
                f"No rules found for component definition {component_definition_path.name}"
            )

        # Write the CSV to disk
        working_path: pathlib.Path = pathlib.Path(self.working_dir)
        csv_file_name: str = f"{component_definition_path.name}.csv"
        csv_path: pathlib.Path = working_path.joinpath(csv_file_name)
        csv_builder.write_to_file(csv_path)

        # Build config for CSV to OSCAL task
        config = configparser.ConfigParser()

        section_name = "task.csv-to-oscal-cd"
        component_def_name = os.path.basename(component_definition_path)
        config[section_name] = {
            "title": f"Component definition for {component_def_name}",
            "version": "1.0",
            "csv-file": f"{csv_file_name}",
            "output-dir": f"{trestle_const.MODEL_DIR_COMPDEF}/{component_def_name}",
            "output-overwrite": "true",
        }

        original_directory = os.getcwd()
        try:
            os.chdir(self.working_dir)
            section_proxy: configparser.SectionProxy = config[section_name]
            csv_to_oscal_task = CsvToOscalComponentDefinition(section_proxy)
            task_outcome = csv_to_oscal_task.execute()
            if task_outcome != TaskOutcome.SUCCESS:
                raise TaskException(
                    f"Failed to transform rules to OSCAL component definition for {component_def_name}"
                )
        except Exception as e:
            raise TaskException(f"Transform failed for {component_def_name}: {e}")

        finally:
            os.chdir(original_directory)
