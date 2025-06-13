# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Results reporting for the ComplyScribe."""

from dataclasses import dataclass
from typing import List


@dataclass
class BotResults:
    """A dataclass to hold the results of the bot run"""

    changes: List[str]
    commit_sha: str
    pr_number: int


class ResultsReporter:
    """
    Base class for reporting the results of the ComplyScribe Bot.
    """

    def report_results(self, results: BotResults) -> None:
        """
        Report the results of the ComplyScribe Bot.

        Args:
            results: BotResults object
        """
        results_str = ""
        if results.commit_sha:
            results_str += f"\nCommit Hash: {results.commit_sha}"

            if results.pr_number:
                results_str += f"\nPull Request Number: {results.pr_number}"
        elif results.changes:
            results_str += "\nChanges:\n"
            results_str += ResultsReporter.get_changes_str(results.changes)
        else:
            results_str = "No changes detected"

        print(results_str)  # noqa: T201

    @staticmethod
    def get_changes_str(changes: List[str]) -> str:
        """
        Return a string representation of the changes.

        Notes: This method is starting off as a simple join of the changes list,
        but is intended to be expanded to provide more detailed information about the changes.
        The goal is consistent representation.
        """
        return "\n".join(changes)
