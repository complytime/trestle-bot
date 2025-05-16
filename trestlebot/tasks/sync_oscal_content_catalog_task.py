import logging
import pathlib

from trestlebot.const import SUCCESS_EXIT_CODE
from trestlebot.tasks.base_task import TaskBase


logger = logging.getLogger(__name__)


class SyncOscalCatalogTask(TaskBase):
    """Sync OSCAL catalog to cac content task."""

    def __init__(
        self,
        cac_content_root: pathlib.Path,
        working_dir: str,
        cac_policy_id: str,
    ) -> None:
        """Initialize task."""
        super().__init__(working_dir, None)
        self.cac_content_root = cac_content_root
        self.cac_policy_id = cac_policy_id

    def execute(self) -> int:
        return SUCCESS_EXIT_CODE
