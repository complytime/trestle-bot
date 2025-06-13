# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.


"""Testing module for complyscribe rules-transform command"""

import pathlib
from typing import Tuple

from click.testing import CliRunner
from git import Repo

from complyscribe.cli.commands.rules_transform import rules_transform_cmd
from tests.testutils import setup_for_compdef, setup_rules_view


test_comp_name = "test_comp"
test_md = "md_cd"


def test_rules_transform(tmp_repo: Tuple[str, Repo]) -> None:
    """Test rule transform."""
    repo_path_str, repo = tmp_repo

    repo_path = pathlib.Path(repo_path_str)

    setup_for_compdef(repo_path, test_comp_name, test_md)
    setup_rules_view(repo_path, test_comp_name)

    assert not repo_path.joinpath(test_md).exists()

    runner = CliRunner()
    result = runner.invoke(
        rules_transform_cmd,
        [
            "--dry-run",
            "--repo-path",
            repo_path,
            "--markdown-dir",
            test_md,
            "--branch",
            "main",
            "--committer-name",
            "Test User",
            "--committer-email",
            "test@example.com",
        ],
    )

    assert result.exit_code == 0
    assert repo_path.joinpath(test_md).exists()
    commit = next(repo.iter_commits())
    assert len(commit.stats.files) == 9
