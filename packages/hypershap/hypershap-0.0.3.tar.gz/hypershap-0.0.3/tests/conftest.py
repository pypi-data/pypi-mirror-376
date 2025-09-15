"""Conftest with all pytest plugins for HyperSHAP."""

from __future__ import annotations

pytest_plugins = [
    "tests.fixtures.simple_setup",
    "tests.fixtures.large_setup",
    "tests.fixtures.multi_data_setup",
]
