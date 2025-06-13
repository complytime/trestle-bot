#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


# Default entrypoint for complyscribe is the root cmd when run with python -m complyscribe

from complyscribe.cli.root import root_cmd


def init() -> None:
    """complyscribe root"""
    if __name__ == "__main__":
        root_cmd()


init()
