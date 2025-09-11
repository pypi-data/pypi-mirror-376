"""Tests for CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from retemplar.cli import app


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


def test_version_command(runner):
    """Test version command."""
    result = runner.invoke(app, ['version'])
    assert result.exit_code == 0
    assert 'retemplar 0.0.0a5' in result.stdout


def test_adopt_command_help(runner):
    """Test adopt command help."""
    result = runner.invoke(app, ['adopt', '--help'])
    assert result.exit_code == 0
    assert 'Attach the repo to a template' in result.stdout


def test_plan_command_help(runner):
    """Test plan command help."""
    result = runner.invoke(app, ['plan', '--help'])
    assert result.exit_code == 0
    assert (
        'Preview structural upgrade plan (cheap, no file diffs).'
        in result.stdout
    )


def test_apply_command_help(runner):
    """Test apply command help."""
    result = runner.invoke(app, ['apply', '--help'])
    assert result.exit_code == 0
    assert 'Apply template changes (with content merge)' in result.stdout


def test_drift_command_help(runner):
    """Test drift command help."""
    result = runner.invoke(app, ['drift', '--help'])
    assert result.exit_code == 0
    assert 'Report drift between' in result.stdout


def test_global_verbose_option(runner, tmp_path: Path):
    """Test global verbose option."""
    result = runner.invoke(
        app,
        ['--repo', str(tmp_path), '--verbose', 'version'],
    )

    assert result.exit_code == 0
