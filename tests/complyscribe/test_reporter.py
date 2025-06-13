# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Test for general reporting logic"""

from unittest.mock import patch

from complyscribe.reporter import BotResults, ResultsReporter


def test_results_reporter_with_commit() -> None:
    """Test results reporter"""
    results = BotResults(changes=[], commit_sha="123456", pr_number=2)

    with patch("builtins.print") as mock_print:
        ResultsReporter().report_results(results)
        mock_print.assert_called_once_with(
            "\nCommit Hash: 123456\nPull Request Number: 2"
        )


def test_results_reporter_no_commit() -> None:
    """Test results reporter with no commit"""
    results = BotResults(changes=[], commit_sha="", pr_number=0)

    with patch("builtins.print") as mock_print:
        ResultsReporter().report_results(results)
        mock_print.assert_called_once_with("No changes detected")


def test_results_reporter_with_changes() -> None:
    """Test results reporter with changes"""
    results = BotResults(changes=["file1"], commit_sha="", pr_number=0)

    with patch("builtins.print") as mock_print:
        ResultsReporter().report_results(results)
        mock_print.assert_called_once_with("\nChanges:\nfile1")
