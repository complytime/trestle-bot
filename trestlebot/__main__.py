#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


# Default entrypoint for trestlebot is the root cmd when run with python -m trestlebot

from trestlebot.cli.root import root_cmd


def init() -> None:
    """trestlebot root"""
    if __name__ == "__main__":
        root_cmd()


init()
