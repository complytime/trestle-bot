# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2023 Red Hat, Inc.


"""Base transformer for rules."""

# Evaluate if this should be contributed back to trestle

from abc import abstractmethod
from typing import Any

from trestle.transforms.transformer_factory import TransformerBase

from complyscribe.transformers.trestle_rule import TrestleRule


class ToRulesTransformer(TransformerBase):
    """Abstract interface for transforming to rule data."""

    @abstractmethod
    def transform(self, data: Any) -> TrestleRule:
        """Transform to rule data."""


class FromRulesTransformer(TransformerBase):
    """Abstract interface for transforming from rule data."""

    @abstractmethod
    def transform(self, rule: TrestleRule) -> Any:
        """Transform from rule data."""


class RulesTransformerException(Exception):
    """An error during transformation of a rule"""
