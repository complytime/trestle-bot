# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.

"""Configure logger for complyscribe and trestle."""

import argparse
import logging
import sys
from typing import List

import trestle.common.log as trestle_log


_logger = logging.getLogger("complyscribe")


def set_log_level(level: int = logging.INFO) -> None:
    """Set the log level from the args for trestle and complyscribe."""

    configure_logger(level)

    # Setup the trestle logger, it expects an argparse Namespace with a verbose int
    verbose = 1 if level == logging.DEBUG else 0
    args = argparse.Namespace(verbose=verbose)
    trestle_log.set_log_level_from_args(args=args)


def configure_logger(level: int = logging.INFO, propagate: bool = False) -> None:
    """Configure the logger."""
    # Prevent extra message
    _logger.propagate = propagate
    _logger.setLevel(level=level)
    for handler in configure_handlers():
        _logger.addHandler(handler)


def configure_handlers() -> List[logging.Handler]:
    """Configure the handlers."""
    # Create a StreamHandler to send non-error logs to stdout
    stdout_info_handler = logging.StreamHandler(sys.stdout)
    stdout_info_handler.setLevel(logging.INFO)
    stdout_info_handler.addFilter(trestle_log.SpecificLevelFilter(logging.INFO))

    stdout_debug_handler = logging.StreamHandler(sys.stdout)
    stdout_debug_handler.setLevel(logging.DEBUG)
    stdout_debug_handler.addFilter(trestle_log.SpecificLevelFilter(logging.DEBUG))

    # Create a StreamHandler to send error logs to stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)

    # Create a formatter and set it on both handlers
    detailed_formatter = logging.Formatter(
        "%(name)s:%(lineno)d %(levelname)s: %(message)s"
    )
    stdout_debug_handler.setFormatter(detailed_formatter)
    stderr_handler.setFormatter(detailed_formatter)
    return [stdout_debug_handler, stdout_info_handler, stderr_handler]
