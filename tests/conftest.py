"""Shared pytest fixtures for rename_project tests."""

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a CliRunner for testing CLI commands."""
    return CliRunner()
