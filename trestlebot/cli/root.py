# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.


"""Main entrypoint for trestlebot"""

import click

from trestlebot.cli.commands.autosync import autosync_cmd
from trestlebot.cli.commands.create import create_cmd
from trestlebot.cli.commands.init import init_cmd
from trestlebot.cli.commands.rules_transform import rules_transform_cmd
from trestlebot.cli.commands.sync_cac_content import (
    sync_cac_catalog_cmd,
    sync_cac_content_cmd,
)
from trestlebot.cli.commands.sync_oscal_content import sync_oscal_content_cmd
from trestlebot.cli.commands.sync_upstreams import sync_upstreams_cmd


EPILOG = "See our docs at https://redhatproductsecurity.github.io/trestle-bot"

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(
    name="trestlebot",
    help="Trestle-bot CLI",
    context_settings=CONTEXT_SETTINGS,
    epilog=EPILOG,
)
@click.pass_context
def root_cmd(ctx: click.Context) -> None:
    """Root command"""


root_cmd.add_command(init_cmd)
root_cmd.add_command(autosync_cmd)
root_cmd.add_command(create_cmd)
root_cmd.add_command(rules_transform_cmd)
root_cmd.add_command(sync_cac_catalog_cmd)
root_cmd.add_command(sync_cac_content_cmd)
root_cmd.add_command(sync_upstreams_cmd)
root_cmd.add_command(sync_oscal_content_cmd)

if __name__ == "__main__":
    root_cmd()
