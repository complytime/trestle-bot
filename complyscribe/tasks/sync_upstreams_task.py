# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.


"""ComplyScribe Sync Upstreams Tasks"""

import argparse
import logging
import pathlib
import tempfile
from typing import List, Optional

from git import GitCommandError, Repo
from trestle.common import file_utils
from trestle.common.const import MODEL_DIR_LIST, VAL_MODE_ALL
from trestle.common.err import TrestleError
from trestle.common.model_utils import ModelUtils
from trestle.core.base_model import OscalBaseModel
from trestle.core.models.file_content_type import FileContentType
from trestle.core.validator import Validator
from trestle.core.validator_factory import validator_factory

from complyscribe import const
from complyscribe.tasks.base_task import ModelFilter, TaskBase, TaskException


logger = logging.getLogger(__name__)


class SyncUpstreamsTask(TaskBase):
    """Sync OSCAL content from upstream git repositories."""

    def __init__(
        self,
        working_dir: str,
        git_sources: List[str],
        model_filter: Optional[ModelFilter] = None,
        validate: bool = True,
    ) -> None:
        """
        Initialize sync upstreams task.

        Args:
            working_dir: Working directory to use for the task. Models from the sources will be copied
            into this directory. It must be a valid trestle project root.
            git_sources: List of upstream git sources to fetch from. Each source is a string
            of the form <repo_url>@<ref> where ref is a git ref such as a tag or branch.
            model_filter: Optional model filter to use for the task. This will filter models from
            being copied from the upstream repositories.
            validate: Optional argument to enable/disable validation of the models after they are copied

        Notes: This task will fetch content from upstream repositories and copy it into the
        trestle workspace. The task WILL overwrite any existing content in the workspace with the same
        name. If it does not exist in the workspace, it will be created. Currently this only supports
        OSCAL artifacts that are stored directly in the repository. This currently does not support
        delete operations.
        """
        if not file_utils.is_valid_project_root(pathlib.Path(working_dir)):
            raise TaskException(
                f"Target workspace {working_dir} is not a valid trestle project root"
            )
        self.sources = git_sources
        self.validate = validate
        super().__init__(working_dir, model_filter)

    def execute(self) -> int:
        """
        Execute task
        Returns:
            0 on success, raises an exception if not successful
        """
        logger.info(f"Syncing from {len(self.sources)} source(s) to {self.working_dir}")
        for source in self.sources:
            self._fetch_oscal_content(source)
        return const.SUCCESS_EXIT_CODE

    def _fetch_oscal_content(self, source: str) -> None:
        """Fetch OSCAL content from upstream sources."""
        repo: Optional[Repo] = None
        logger.info(f"Syncing content from {source}")
        try:
            with tempfile.TemporaryDirectory(dir=self.working_dir) as temporary_git_dir:
                self.validate_source(source)
                repo_url, ref = source.split("@")
                upstream_trestle_workspace: pathlib.Path = pathlib.Path(
                    temporary_git_dir
                )
                Repo.clone_from(repo_url, upstream_trestle_workspace)
                repo = Repo(upstream_trestle_workspace)
                repo.git.checkout(ref)

                validator: Optional[Validator] = None
                if self.validate:
                    args = argparse.Namespace(mode=VAL_MODE_ALL, quiet=True)
                    validator = validator_factory.get(args)

                for model_dir in MODEL_DIR_LIST:
                    self._copy_validate_models(
                        upstream_trestle_workspace,
                        pathlib.Path(self.working_dir),
                        model_dir,
                        validator,
                    )
                logger.info(f"Successfully copied from {source}")
        except ValueError as e:
            raise TaskException(f"Invalid source {source}: {e}")
        except GitCommandError as e:
            raise TaskException(
                f"Git error occurred while fetching content from {source}: {e}"
            )
        except TrestleError as e:
            raise TaskException(
                f"Trestle error occurred while fetching content from {source}: {e}"
            )
        except Exception as e:
            raise TaskException(
                f"Unexpected error while fetching content from {source}: {e}"
            )
        finally:
            if repo is not None:
                repo.close()

    def validate_source(self, source: str) -> None:
        """Validate the source string."""
        if source.count("@") != 1:
            raise ValueError(f"Source {source} must be of the form <repo_url>@<ref>")

    def _copy_validate_models(
        self,
        source_trestle_root: pathlib.Path,
        destination_trestle_root: pathlib.Path,
        model_dir: str,
        validator: Optional[Validator] = None,
    ) -> None:
        """Copy models from upstream source to trestle workspace."""
        model_search_path = source_trestle_root.joinpath(model_dir)
        # The model directories are created by default with trestle init, but
        # they can be deleted.
        if not model_search_path.exists():
            return
        logger.debug(f"Copying models from {model_search_path}")
        for model_path in self.iterate_models(model_search_path):
            model: OscalBaseModel
            _, _, model = ModelUtils.load_distributed(
                model_path.absolute(), source_trestle_root.absolute()
            )

            # Validate the model
            if validator is not None:
                logger.debug(f"Validating model {model_path}")
                if not validator.model_is_valid(model, True, source_trestle_root):
                    raise TrestleError(
                        f"Model {model_path} from {model_search_path} is not valid"
                    )

            # Write model to disk as JSON.
            # The only format supported by the trestle authoring
            # process is JSON.
            model_name = model_path.name
            ModelUtils.save_top_level_model(
                model, destination_trestle_root, model_name, FileContentType.JSON
            )
