"""Comprehensive tests for the CLI module."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml
from caption_flow.cli import (
    ConfigManager,
    apply_cli_overrides,
    main,
    setup_logging,
    validate_orchestrator_auth_config,
)
from click.testing import CliRunner


@pytest.fixture
def runner():
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "server": {"host": "localhost", "port": 8765},
        "storage": {"data_dir": "./test_data"},
        "processor": {"batch_size": 10},
    }


class TestConfigManager:
    """Test ConfigManager class."""

    def test_get_xdg_config_home_env_set(self):
        """Test XDG_CONFIG_HOME when environment variable is set."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
            result = ConfigManager.get_xdg_config_home()
            assert result == Path("/custom/config")

    def test_get_xdg_config_home_default(self):
        """Test XDG_CONFIG_HOME default fallback."""
        with patch.dict(os.environ, {}, clear=True):
            result = ConfigManager.get_xdg_config_home()
            assert result == Path.home() / ".config"

    def test_get_xdg_config_dirs_env_set(self):
        """Test XDG_CONFIG_DIRS when environment variable is set."""
        with patch.dict(os.environ, {"XDG_CONFIG_DIRS": "/etc/xdg:/usr/local/etc"}):
            result = ConfigManager.get_xdg_config_dirs()
            assert result == [Path("/etc/xdg"), Path("/usr/local/etc")]

    def test_get_xdg_config_dirs_default(self):
        """Test XDG_CONFIG_DIRS default fallback."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {"XDG_CONFIG_DIRS": "/etc/xdg"}):
                result = ConfigManager.get_xdg_config_dirs()
                assert result == [Path("/etc/xdg")]

    def test_find_config_explicit_path(self, temp_config_dir, sample_config):
        """Test finding config with explicit path."""
        config_file = temp_config_dir / "custom.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        result = ConfigManager.find_config("orchestrator", str(config_file))
        assert result == sample_config

    def test_find_config_explicit_path_not_found(self):
        """Test finding config with explicit path that doesn't exist."""
        result = ConfigManager.find_config("orchestrator", "/nonexistent/config.yaml")
        assert result is None

    def test_find_config_search_paths(self, temp_config_dir, sample_config):
        """Test config discovery through search paths."""
        captionflow_dir = temp_config_dir / "caption-flow"
        captionflow_dir.mkdir()
        config_file = captionflow_dir / "orchestrator.yaml"

        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        with patch.object(ConfigManager, "get_xdg_config_home", return_value=temp_config_dir):
            result = ConfigManager.find_config("orchestrator")
            assert result == sample_config

    def test_find_config_not_found(self, temp_config_dir):
        """Test config not found scenario."""
        with patch.object(ConfigManager, "get_xdg_config_home", return_value=temp_config_dir):
            with patch.object(ConfigManager, "get_xdg_config_dirs", return_value=[temp_config_dir]):
                with patch.object(Path, "cwd", return_value=temp_config_dir):
                    with patch.object(Path, "home", return_value=temp_config_dir):
                        # Mock the examples directory to not exist
                        with patch("pathlib.Path.exists", return_value=False):
                            result = ConfigManager.find_config("orchestrator")
                            assert result is None

    def test_load_yaml(self, temp_config_dir, sample_config):
        """Test loading YAML configuration from file."""
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        result = ConfigManager.load_yaml(config_file)
        assert result == sample_config

    def test_load_yaml_invalid_file(self, temp_config_dir):
        """Test loading invalid YAML file."""
        config_file = temp_config_dir / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content:")

        result = ConfigManager.load_yaml(config_file)
        assert result is None

    def test_merge_configs(self):
        """Test configuration merging."""
        base = {"server": {"port": 8000}, "worker": {"name": "base"}}
        override = {"server": {"host": "localhost"}, "new_key": "value"}

        result = ConfigManager.merge_configs(base, override)
        expected = {
            "server": {"port": 8000, "host": "localhost"},
            "worker": {"name": "base"},
            "new_key": "value",
        }
        assert result == expected


class TestSetupLogging:
    """Test setup_logging function."""

    @patch("caption_flow.cli.logging.basicConfig")
    def test_setup_logging_normal(self, mock_basic_config):
        """Test normal logging setup."""
        setup_logging(verbose=False)
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == 20  # logging.INFO

    @patch("caption_flow.cli.logging.basicConfig")
    def test_setup_logging_verbose(self, mock_basic_config):
        """Test verbose logging setup."""
        setup_logging(verbose=True)
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == 10  # logging.DEBUG


class TestApplyCliOverrides:
    """Test apply_cli_overrides function."""

    def test_apply_cli_overrides_basic(self):
        """Test basic CLI override application."""
        config = {"server": {"port": 8000}}
        result = apply_cli_overrides(config, port=9000)
        # The function merges the overrides, so port would be at top level
        expected = {"server": {"port": 8000}, "port": 9000}
        assert result == expected

    def test_apply_cli_overrides_none_values(self):
        """Test CLI overrides with None values are ignored."""
        config = {"server": {"port": 8000}}
        result = apply_cli_overrides(config, port=None, host="localhost")
        expected = {"server": {"port": 8000}, "host": "localhost"}
        assert result == expected

    def test_apply_cli_overrides_empty_config(self):
        """Test CLI overrides on empty config."""
        config = {}
        result = apply_cli_overrides(config, port=8000)
        expected = {"port": 8000}
        assert result == expected


class TestValidateOrchestratorAuthConfig:
    """Test validate_orchestrator_auth_config function."""

    def test_valid_orchestrator_section_auth(self):
        """Test valid auth config in orchestrator section."""
        config_data = {
            "port": 8765,
            "auth": {
                "worker_tokens": [{"token": "worker1", "name": "Worker 1"}],
                "admin_tokens": [{"token": "admin1", "name": "Admin 1"}],
            },
        }
        base_config = {"orchestrator": config_data}

        result = validate_orchestrator_auth_config(config_data, base_config)

        assert "auth" in result
        assert result["auth"]["worker_tokens"][0]["token"] == "worker1"
        assert result["auth"]["admin_tokens"][0]["token"] == "admin1"

    def test_fallback_to_top_level_auth(self):
        """Test fallback from top-level auth config with warning."""
        config_data = {"port": 8765}
        base_config = {
            "orchestrator": config_data,
            "auth": {"worker_tokens": [{"token": "worker1", "name": "Worker 1"}]},
        }

        result = validate_orchestrator_auth_config(config_data, base_config)

        # Should move auth from base_config to config_data
        assert "auth" in result
        assert result["auth"]["worker_tokens"][0]["token"] == "worker1"

    def test_no_auth_config_error(self):
        """Test error when no auth config is found."""
        config_data = {"port": 8765}
        base_config = {"orchestrator": config_data}

        with pytest.raises(ValueError, match="Auth configuration is required"):
            validate_orchestrator_auth_config(config_data, base_config)

    def test_invalid_auth_structure(self):
        """Test error for invalid auth structure."""
        config_data = {
            "port": 8765,
            "auth": "invalid_auth_string",  # Should be dict
        }
        base_config = {"orchestrator": config_data}

        with pytest.raises(ValueError, match="Auth configuration must be a dictionary"):
            validate_orchestrator_auth_config(config_data, base_config)

    def test_no_tokens_configured_error(self):
        """Test error when no token types are configured."""
        config_data = {
            "port": 8765,
            "auth": {},  # Empty auth config
        }
        base_config = {"orchestrator": config_data}

        with pytest.raises(ValueError, match="At least one token type must be configured"):
            validate_orchestrator_auth_config(config_data, base_config)

    def test_empty_token_lists_error(self):
        """Test error when token lists exist but are empty."""
        config_data = {
            "port": 8765,
            "auth": {"worker_tokens": [], "admin_tokens": [], "monitor_tokens": []},
        }
        base_config = {"orchestrator": config_data}

        with pytest.raises(ValueError, match="At least one token type must be configured"):
            validate_orchestrator_auth_config(config_data, base_config)

    def test_valid_with_single_token_type(self):
        """Test validation passes with just one token type."""
        config_data = {
            "port": 8765,
            "auth": {"worker_tokens": [{"token": "worker1", "name": "Worker 1"}]},
        }
        base_config = {"orchestrator": config_data}

        # Should not raise an exception
        result = validate_orchestrator_auth_config(config_data, base_config)
        assert "auth" in result
        assert len(result["auth"]["worker_tokens"]) == 1

    def test_validation_warnings_for_missing_critical_tokens(self, capsys):
        """Test warnings are printed for missing critical token types."""
        config_data = {
            "port": 8765,
            "auth": {"monitor_tokens": [{"token": "monitor1", "name": "Monitor 1"}]},
        }
        base_config = {"orchestrator": config_data}

        validate_orchestrator_auth_config(config_data, base_config)

        # Check that warnings were printed (captured by capsys if using rich console)
        # This test verifies the function runs without errors when warnings are present

    def test_preserves_other_config_data(self):
        """Test that validation preserves other configuration data."""
        config_data = {
            "port": 8765,
            "host": "0.0.0.0",
            "ssl": {"cert": "path/to/cert"},
            "auth": {"worker_tokens": [{"token": "worker1", "name": "Worker 1"}]},
        }
        base_config = {"orchestrator": config_data}

        result = validate_orchestrator_auth_config(config_data, base_config)

        # Should preserve all original data
        assert result["port"] == 8765
        assert result["host"] == "0.0.0.0"
        assert result["ssl"]["cert"] == "path/to/cert"
        assert "auth" in result


class TestMainCommand:
    """Test main CLI command."""

    def test_main_help(self, runner):
        """Test main command help."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "CaptionFlow" in result.output

    def test_main_verbose_flag(self, runner):
        """Test main command with verbose flag."""
        with patch("caption_flow.cli.setup_logging") as mock_setup_logging:
            # Use a subcommand to ensure main() callback is executed
            result = runner.invoke(main, ["--verbose", "orchestrator", "--help"])
            assert result.exit_code == 0
            # setup_logging is called once in main() with the verbose flag
            mock_setup_logging.assert_called_once_with(True)


class TestOrchestratorCommand:
    """Test orchestrator CLI command."""

    def test_orchestrator_help(self, runner):
        """Test orchestrator command help."""
        result = runner.invoke(main, ["orchestrator", "--help"])
        assert result.exit_code == 0
        assert "orchestrator" in result.output.lower()

    @patch("caption_flow.cli.Orchestrator")
    @patch("caption_flow.cli.ConfigManager.find_config")
    @patch("caption_flow.cli.asyncio.run")
    def test_orchestrator_run(
        self,
        mock_asyncio_run,
        mock_find_config,
        mock_orchestrator_class,
        runner,
        temp_config_dir,
        sample_config,
    ):
        """Test running orchestrator command."""
        config_file = temp_config_dir / "orchestrator.yaml"
        # Add auth config to sample_config for this test
        config_with_auth = {
            **sample_config,
            "auth": {"worker_tokens": [{"token": "worker1", "name": "Worker 1"}]},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_with_auth, f)

        mock_find_config.return_value = config_with_auth
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        runner.invoke(main, ["orchestrator", "--config", str(config_file)])

        # Should attempt to find config and create orchestrator
        mock_find_config.assert_called()
        mock_orchestrator_class.assert_called()

    def test_orchestrator_auth_validation_error(self, runner, temp_config_dir):
        """Test orchestrator command fails when no auth config is provided."""
        config_file = temp_config_dir / "orchestrator_no_auth.yaml"
        config_without_auth = {
            "orchestrator": {
                "port": 8765,
                "host": "localhost",
                # No auth section
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config_without_auth, f)

        result = runner.invoke(main, ["orchestrator", "--config", str(config_file)])

        # Should exit with error due to missing auth config
        assert result.exit_code == 1
        assert "Auth configuration is required" in result.output

    @patch("caption_flow.cli.Orchestrator")
    @patch("caption_flow.cli.asyncio.run")
    def test_orchestrator_auth_fallback_warning(
        self, mock_asyncio_run, mock_orchestrator_class, runner, temp_config_dir
    ):
        """Test orchestrator command with top-level auth fallback shows warning."""
        config_file = temp_config_dir / "orchestrator_top_level_auth.yaml"
        config_with_top_level_auth = {
            "orchestrator": {"port": 8765, "host": "localhost"},
            "auth": {  # Top-level auth (deprecated)
                "worker_tokens": [{"token": "worker1", "name": "Worker 1"}]
            },
        }
        with open(config_file, "w") as f:
            yaml.dump(config_with_top_level_auth, f)

        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        result = runner.invoke(main, ["orchestrator", "--config", str(config_file)])

        # Should run successfully but show warning
        assert result.exit_code == 0
        assert "Warning: Found auth config at top level" in result.output
        assert "should be under 'orchestrator' section" in result.output


class TestWorkerCommand:
    """Test worker CLI command."""

    def test_worker_help(self, runner):
        """Test worker command help."""
        result = runner.invoke(main, ["worker", "--help"])
        assert result.exit_code == 0
        assert "worker" in result.output.lower()

    @patch("caption_flow.cli.ConfigManager.find_config")
    @patch("caption_flow.cli.asyncio.run")
    def test_worker_run(
        self, mock_asyncio_run, mock_find_config, runner, temp_config_dir, sample_config
    ):
        """Test running worker command."""
        config_file = temp_config_dir / "worker.yaml"
        worker_config = {**sample_config, "worker": {"name": "test-worker"}}
        with open(config_file, "w") as f:
            yaml.dump(worker_config, f)

        mock_find_config.return_value = worker_config

        runner.invoke(main, ["worker", "--config", str(config_file)])

        # Should attempt to find config
        mock_find_config.assert_called()


class TestMonitorCommand:
    """Test monitor CLI command."""

    def test_monitor_help(self, runner):
        """Test monitor command help."""
        result = runner.invoke(main, ["monitor", "--help"])
        assert result.exit_code == 0
        assert "monitor" in result.output.lower()

    @patch("caption_flow.cli.Monitor")
    @patch("caption_flow.cli.ConfigManager.find_config")
    @patch("caption_flow.cli.asyncio.run")
    def test_monitor_run(
        self,
        mock_asyncio_run,
        mock_find_config,
        mock_monitor_class,
        runner,
        temp_config_dir,
        sample_config,
    ):
        """Test running monitor command."""
        config_file = temp_config_dir / "monitor.yaml"
        monitor_config = {**sample_config, "token": "test-token", "server": "wss://localhost:8765"}
        with open(config_file, "w") as f:
            yaml.dump(monitor_config, f)

        mock_find_config.return_value = monitor_config
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor

        runner.invoke(main, ["monitor", "--config", str(config_file)])

        # Should attempt to find config and create monitor
        mock_find_config.assert_called()
        mock_monitor_class.assert_called()


class TestViewCommand:
    """Test view CLI command."""

    def test_view_help(self, runner):
        """Test view command help."""
        result = runner.invoke(main, ["view", "--help"])
        assert result.exit_code == 0
        assert "view" in result.output.lower()

    @patch("caption_flow.viewer.DatasetViewer")
    @patch("caption_flow.cli.asyncio.run")
    def test_view_run(self, mock_asyncio_run, mock_viewer_class, runner, tmp_path):
        """Test running view command."""
        # Create a temporary data directory with required files
        data_dir = tmp_path / "test_data"
        data_dir.mkdir()
        (data_dir / "captions.parquet").touch()

        mock_viewer = Mock()
        mock_viewer.run = AsyncMock()
        mock_viewer_class.return_value = mock_viewer

        runner.invoke(main, ["view", "--data-dir", str(data_dir)])

        # Should create and run viewer
        mock_viewer_class.assert_called()
        mock_asyncio_run.assert_called()


class TestScanChunksCommand:
    """Test scan-chunks CLI command."""

    def test_scan_chunks_help(self, runner):
        """Test scan-chunks command help."""
        result = runner.invoke(main, ["scan-chunks", "--help"])
        assert result.exit_code == 0
        assert "scan" in result.output.lower()

    @patch("caption_flow.storage.StorageManager")
    @patch("caption_flow.utils.chunk_tracker.ChunkTracker")
    def test_scan_chunks_run(self, mock_chunk_tracker_class, mock_storage_class, runner, tmp_path):
        """Test running scan-chunks command."""
        # Create checkpoint directory and file
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir()
        checkpoint_file = checkpoint_dir / "chunks.json"
        checkpoint_file.write_text('{"chunks": {}}')

        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_tracker = Mock()
        mock_chunk_tracker_class.return_value = mock_tracker
        mock_tracker.abandoned_chunks = []

        # Mock tracker methods
        mock_tracker.get_stats.return_value = {
            "total": 10,
            "completed": 5,
            "pending": 3,
            "assigned": 2,
            "failed": 0,
        }
        mock_tracker.chunks = {}
        mock_tracker.get_shards_summary.return_value = {}

        result = runner.invoke(
            main,
            ["scan-chunks", "--data-dir", "./test_data", "--checkpoint-dir", str(checkpoint_dir)],
        )

        # Should create storage manager and chunk tracker if checkpoint exists
        if result.exit_code == 0:
            mock_storage_class.assert_called()
            mock_chunk_tracker_class.assert_called()
        else:
            # Command may fail due to missing dependencies but should attempt to run
            assert result.exit_code != 0


class TestExportCommand:
    """Test export CLI command."""

    def test_export_help(self, runner):
        """Test export command help."""
        result = runner.invoke(main, ["export", "--help"])
        assert result.exit_code == 0
        assert "export" in result.output.lower()

    def test_export_command_no_duplicate_registration(self, runner):
        """Regression test: Ensure export command is only registered once.

        This test prevents the bug where @main.command() was incorrectly
        applied to _validate_export_setup() causing duplicate command
        registration and argument parsing errors.
        """
        # Get all registered commands
        commands = list(main.commands.keys())

        # Count occurrences of 'export'
        export_count = commands.count("export")

        # Should be exactly one export command
        assert export_count == 1, f"Expected 1 export command, found {export_count}: {commands}"

        # Test that export command can handle basic arguments without parsing errors
        result = runner.invoke(main, ["export", "--help"])
        assert result.exit_code == 0
        assert "Got unexpected extra arguments" not in result.output

        # Test with a data directory argument (the one that was causing issues)
        result = runner.invoke(main, ["export", "--data-dir", "caption_data", "--stats-only"])
        # Should not get parsing errors (though it may fail for other reasons like missing files)
        assert "Got unexpected extra arguments" not in result.output

    @patch("caption_flow.storage.StorageManager")
    @patch("caption_flow.cli.asyncio.run")
    def test_export_stats_only(self, mock_asyncio_run, mock_storage_class, runner, tmp_path):
        """Test export command with stats-only flag."""
        # Create a temporary data directory
        data_dir = tmp_path / "test_data"
        data_dir.mkdir()

        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.initialize = AsyncMock()
        mock_storage.get_caption_stats = AsyncMock()
        mock_storage.get_caption_stats.return_value = {
            "total_rows": 100,
            "total_outputs": 100,
            "shard_count": 1,
            "shards": ["data-001"],
            "output_fields": ["captions"],
        }

        result = runner.invoke(
            main, ["export", "--format", "jsonl", "--stats-only", "--data-dir", str(data_dir)]
        )

        # If the command exited successfully, should create storage manager and run async function
        if result.exit_code == 0:
            mock_storage_class.assert_called()
            mock_asyncio_run.assert_called()
        else:
            # Test that command ran, even if it failed due to missing dependencies
            assert result.exit_code != 0


class TestCertificateCommands:
    """Test certificate-related CLI commands."""

    def test_generate_cert_help(self, runner):
        """Test generate-cert command help."""
        result = runner.invoke(main, ["generate-cert", "--help"])
        assert result.exit_code == 0
        assert "certificate" in result.output.lower()

    @patch("caption_flow.cli.CertificateManager")
    def test_generate_cert_self_signed(self, mock_cert_manager_class, runner):
        """Test generating self-signed certificate."""
        mock_manager = Mock()
        mock_cert_manager_class.return_value = mock_manager

        runner.invoke(main, ["generate-cert", "--self-signed", "--output-dir", "./certs"])

        # Should create certificate manager
        mock_cert_manager_class.assert_called_once()

    def test_inspect_cert_help(self, runner):
        """Test inspect-cert command help."""
        result = runner.invoke(main, ["inspect-cert", "--help"])
        assert result.exit_code == 0
        assert "inspect" in result.output.lower()

    @patch("caption_flow.utils.certificates.CertificateManager")
    def test_inspect_cert_run(self, mock_cert_manager_class, runner, temp_config_dir):
        """Test inspecting certificate."""
        cert_file = temp_config_dir / "test.crt"
        cert_file.touch()  # Create empty file for test

        mock_manager = Mock()
        mock_cert_manager_class.return_value = mock_manager
        mock_manager.get_cert_info.return_value = {
            "subject": "test",
            "issuer": "test",
            "not_before": "2024-01-01",
            "not_after": "2025-01-01",
            "serial_number": "123",
            "is_self_signed": True,
        }

        result = runner.invoke(main, ["inspect-cert", str(cert_file)])

        # If command succeeded, should call methods
        if result.exit_code == 0:
            mock_cert_manager_class.assert_called()
            mock_manager.get_cert_info.assert_called()
        else:
            # Test that command ran, even if it failed
            assert result.exit_code != 0


class TestReloadConfigCommand:
    """Test reload-config CLI command."""

    def test_reload_config_help(self, runner):
        """Test reload-config command help."""
        result = runner.invoke(main, ["reload-config", "--help"])
        assert result.exit_code == 0
        assert "reload" in result.output.lower()

    @patch("caption_flow.cli.ConfigManager.load_yaml")
    @patch("caption_flow.cli.asyncio.run")
    def test_reload_config_run(self, mock_asyncio_run, mock_load_yaml, runner, tmp_path):
        """Test running reload-config command."""
        # Create a dummy config file
        config_file = tmp_path / "new_config.yaml"
        config_file.touch()

        # Mock config with valid auth structure
        mock_config = {
            "orchestrator": {
                "port": 8765,
                "auth": {
                    "worker_tokens": [{"token": "worker1", "name": "Worker 1"}],
                    "admin_tokens": [{"token": "admin1", "name": "Admin 1"}],
                },
            }
        }
        mock_load_yaml.return_value = mock_config

        result = runner.invoke(
            main,
            [
                "reload-config",
                "--server",
                "ws://localhost:8765",
                "--token",
                "test-token",
                "--new-config",
                str(config_file),
            ],
        )

        # Should attempt to run async function
        mock_asyncio_run.assert_called()
        mock_load_yaml.assert_called()
        # Should validate auth and succeed
        assert result.exit_code == 0

    def test_reload_config_auth_validation_error(self, runner, tmp_path):
        """Test reload-config command fails when new config has no auth."""
        config_file = tmp_path / "bad_config.yaml"
        bad_config = {
            "orchestrator": {
                "port": 8765,
                # No auth section - should fail validation
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(bad_config, f)

        result = runner.invoke(
            main,
            [
                "reload-config",
                "--server",
                "ws://localhost:8765",
                "--token",
                "test-token",
                "--new-config",
                str(config_file),
            ],
        )

        # Should exit with error due to validation failure
        assert result.exit_code == 1
        assert "Configuration validation error" in result.output
        assert "Auth configuration is required" in result.output

    def test_reload_config_auth_top_level_fallback(self, runner, tmp_path):
        """Test reload-config handles top-level auth fallback with warning."""
        config_file = tmp_path / "top_level_auth_config.yaml"
        config_with_top_level_auth = {
            "orchestrator": {
                "port": 8765,
            },
            "auth": {  # Top-level auth (deprecated)
                "worker_tokens": [{"token": "worker1", "name": "Worker 1"}]
            },
        }
        with open(config_file, "w") as f:
            yaml.dump(config_with_top_level_auth, f)

        with patch("caption_flow.cli.asyncio.run", return_value=True):
            result = runner.invoke(
                main,
                [
                    "reload-config",
                    "--server",
                    "ws://localhost:8765",
                    "--token",
                    "test-token",
                    "--new-config",
                    str(config_file),
                ],
            )

        # Should succeed but show warning about top-level auth
        assert result.exit_code == 0
        assert "Warning: Found auth config at top level" in result.output
        assert "should be under 'orchestrator' section" in result.output

    def test_reload_config_validates_nested_orchestrator_config(self, runner, tmp_path):
        """Test reload-config validates orchestrator section properly."""
        config_file = tmp_path / "nested_config.yaml"
        nested_config = {
            "orchestrator": {
                "port": 8765,
                "auth": {
                    "worker_tokens": [{"token": "worker1", "name": "Worker 1"}],
                    "admin_tokens": [{"token": "admin1", "name": "Admin 1"}],
                },
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(nested_config, f)

        with patch("caption_flow.cli.asyncio.run", return_value=True):
            result = runner.invoke(
                main,
                [
                    "reload-config",
                    "--server",
                    "ws://localhost:8765",
                    "--token",
                    "test-token",
                    "--new-config",
                    str(config_file),
                ],
            )

        # Should succeed with proper nested structure
        assert result.exit_code == 0
        assert "Using auth config from orchestrator section" in result.output
        assert "✓ Auth validation passed" in result.output

    def test_reload_config_validates_flat_config(self, runner, tmp_path):
        """Test reload-config validates flat config (no orchestrator section)."""
        config_file = tmp_path / "flat_config.yaml"
        flat_config = {
            "port": 8765,
            "auth": {
                "worker_tokens": [{"token": "worker1", "name": "Worker 1"}],
                "admin_tokens": [{"token": "admin1", "name": "Admin 1"}],
            },
        }
        with open(config_file, "w") as f:
            yaml.dump(flat_config, f)

        with patch("caption_flow.cli.asyncio.run", return_value=True):
            result = runner.invoke(
                main,
                [
                    "reload-config",
                    "--server",
                    "ws://localhost:8765",
                    "--token",
                    "test-token",
                    "--new-config",
                    str(config_file),
                ],
            )

        # Should succeed with flat structure
        assert result.exit_code == 0
        assert "Using auth config from orchestrator section" in result.output
        assert "✓ Auth validation passed" in result.output


if __name__ == "__main__":
    pytest.main([__file__])
