"""
Tests for the CLI module.

This module tests the command-line interface functionality including
command parsing, configuration handling, and basic operations.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from log_generator.cli import app
from log_generator.core.config import ConfigurationManager

# CLI tests optimized for speed


@pytest.fixture
def runner():
    """Shared CLI runner fixture."""
    return CliRunner()


@pytest.fixture
def config_manager():
    """Shared configuration manager fixture."""
    return ConfigurationManager()


@pytest.fixture
def temp_config_file(config_manager):
    """Create a temporary config file for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = os.path.join(temp_dir, "test_config.yaml")
        config_manager.save_config(config_manager.DEFAULT_CONFIG, config_file)
        yield config_file


class TestCLI:
    """Test cases for CLI functionality."""

    def test_cli_help(self, runner):
        """Test that CLI help command works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "log-generator" in result.stdout

    def test_list_types_command(self, runner):
        """Test the list-types command."""
        result = runner.invoke(app, ["list-types"])
        assert result.exit_code == 0
        assert "Available Log Generator Types" in result.stdout

    def test_config_create_command(self, runner):
        """Test configuration file creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "test_config.yaml")

            result = runner.invoke(
                app, ["config", "create", "--file", config_file, "--format", "yaml"]
            )

            assert result.exit_code == 0
            assert Path(config_file).exists()

    def test_config_show_command(self, runner):
        """Test configuration display."""
        result = runner.invoke(app, ["config", "show", "--format", "yaml"])

        assert result.exit_code == 0
        assert "Configuration" in result.stdout

    def test_config_validate_command(self, runner, temp_config_file):
        """Test configuration validation."""
        result = runner.invoke(app, ["config", "validate", "--file", temp_config_file])

        assert result.exit_code == 0
        assert "Configuration file is valid" in result.stdout

    def test_config_validate_invalid_file(self, runner):
        """Test configuration validation with invalid file."""
        result = runner.invoke(
            app, ["config", "validate", "--file", "nonexistent_file.yaml"]
        )

        assert result.exit_code == 1

    @patch("log_generator.cli._engine", None)
    def test_status_no_engine(self, runner):
        """Test status command when no engine is initialized."""
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "No log generation engine initialized" in result.stdout

    @patch("log_generator.cli._engine")
    def test_status_with_engine(self, mock_engine, runner):
        """Test status command with initialized engine."""
        mock_engine.get_statistics.return_value = {
            "total_logs_generated": 100,
            "generation_rate": 10.5,
        }
        mock_engine.is_running.return_value = True

        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Log Generation Status" in result.stdout

    @patch("log_generator.cli._engine", None)
    def test_stop_no_engine(self, runner):
        """Test stop command when no engine is running."""
        result = runner.invoke(app, ["stop"])
        assert result.exit_code == 0
        assert "No log generation engine initialized" in result.stdout

    @patch("log_generator.cli._engine")
    def test_stop_with_engine(self, mock_engine, runner):
        """Test stop command with running engine."""
        mock_engine.is_running.return_value = True

        result = runner.invoke(app, ["stop"])
        assert result.exit_code == 0
        mock_engine.stop_generation.assert_called_once()

    @patch("log_generator.cli._engine", None)
    def test_monitor_no_engine(self, runner):
        """Test monitor command when no engine is running."""
        result = runner.invoke(app, ["monitor"])
        assert result.exit_code == 0
        assert "No log generation engine initialized" in result.stdout

    def test_start_with_invalid_config(self, runner):
        """Test start command with invalid configuration file."""
        result = runner.invoke(app, ["start", "--config", "nonexistent_config.yaml"])

        assert result.exit_code == 1

    def test_start_command_exists(self, runner):
        """Test that start command exists and shows help."""
        result = runner.invoke(app, ["start", "--help"])
        assert result.exit_code == 0
        assert "Start log generation" in result.stdout

    @patch("log_generator.cli._engine", None)
    def test_pause_resume_commands(self, runner):
        """Test pause and resume commands."""
        # Test pause command
        result = runner.invoke(app, ["pause"])
        assert result.exit_code == 0
        assert "No log generation is currently running" in result.stdout

        # Test resume command
        result = runner.invoke(app, ["resume"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.stdout


class TestCLIIntegration:
    """Integration tests for CLI with actual components."""

    def test_config_workflow_and_error_handling(self, runner):
        """Test configuration workflow and error handling in one test."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "integration_config.yaml")

            # Test create and validate
            result = runner.invoke(app, ["config", "create", "--file", config_file])
            assert result.exit_code == 0

            result = runner.invoke(app, ["config", "validate", "--file", config_file])
            assert result.exit_code == 0

            # Test error handling
            result = runner.invoke(app, ["config", "invalid_action"])
            assert result.exit_code == 1


if __name__ == "__main__":
    pytest.main([__file__])
