# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

from typing import Any, Dict, List

from complyscribe.bot import ComplyScribe
from complyscribe.reporter import BotResults
from complyscribe.tasks.base_task import TaskBase


def comma_sep_to_list(string: str) -> List[str]:
    """Convert comma-sep string to list of strings and strip."""
    string = string.strip() if string else ""
    return list(map(str.strip, string.split(","))) if string else []


def run_bot(pre_tasks: List[TaskBase], kwargs: Dict[Any, Any]) -> BotResults:
    """Reusable logic for all commands."""

    # Configure and run the bot
    bot = ComplyScribe(
        working_dir=kwargs["repo_path"],
        branch=kwargs["branch"],
        commit_name=kwargs["committer_name"],
        commit_email=kwargs["committer_email"],
        author_name=kwargs.get("author_name", ""),
        author_email=kwargs.get("author_email", ""),
    )

    return bot.run(
        pre_tasks=pre_tasks,
        patterns=kwargs.get("patterns", ["."]),
        commit_message=kwargs.get(
            "commit_message", "Automatic updates from complyscribe"
        ),
        dry_run=kwargs.get("dry_run", False),
    )
