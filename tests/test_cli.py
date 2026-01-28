"""
CLI Tests
~~~~~~~~~

This module contains Rent-A-Bot CLI tests.
"""

import os
from unittest.mock import patch

import pytest

from rentabot.cli import find_config_file, main


class TestFindConfigFile:
    """Test configuration file discovery logic."""

    def test_find_config_in_current_dir_rentabot_yaml(self, tmp_path, monkeypatch):
        """Test finding rentabot.yaml in current directory."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "rentabot.yaml"
        config_file.write_text("# test config")

        result = find_config_file()
        assert result == str(config_file)

    def test_find_config_in_current_dir_dot_rentabot_yaml(self, tmp_path, monkeypatch):
        """Test finding .rentabot.yaml in current directory (higher priority)."""
        monkeypatch.chdir(tmp_path)
        dot_config = tmp_path / ".rentabot.yaml"
        dot_config.write_text("# test config")
        other_config = tmp_path / "rentabot.yaml"
        other_config.write_text("# other config")

        result = find_config_file()
        assert result == str(dot_config)

    def test_find_config_in_home_dir(self, tmp_path, monkeypatch):
        """Test finding config in home directory when not in current dir."""
        monkeypatch.chdir(tmp_path)
        home_dir = tmp_path / "fake_home"
        home_dir.mkdir()
        rentabot_dir = home_dir / ".rentabot"
        rentabot_dir.mkdir()
        config_file = rentabot_dir / "config.yaml"
        config_file.write_text("# home config")

        with patch("rentabot.cli.Path.home", return_value=home_dir):
            result = find_config_file()
            assert result == str(config_file)

    def test_find_config_from_env_var(self, tmp_path, monkeypatch):
        """Test finding config from RENTABOT_RESOURCE_DESCRIPTOR env var."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "env_config.yaml"
        config_file.write_text("# env config")
        monkeypatch.setenv("RENTABOT_RESOURCE_DESCRIPTOR", str(config_file))

        result = find_config_file()
        assert result == str(config_file)

    def test_find_config_returns_none_when_not_found(self, tmp_path, monkeypatch):
        """Test that None is returned when no config file is found."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("RENTABOT_RESOURCE_DESCRIPTOR", raising=False)

        with patch("rentabot.cli.Path.home", return_value=tmp_path / "fake_home"):
            result = find_config_file()
            assert result is None

    def test_env_var_ignored_if_file_not_exists(self, tmp_path, monkeypatch):
        """Test that env var is ignored if file doesn't exist."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("RENTABOT_RESOURCE_DESCRIPTOR", "/nonexistent/path.yaml")

        result = find_config_file()
        assert result is None


class TestCLIMain:
    """Test CLI main function."""

    def test_version_flag(self, capsys):
        """Test --version flag displays version and exits."""
        with patch("sys.argv", ["rentabot", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "1.0.0" in captured.out

    def test_help_flag(self, capsys):
        """Test --help flag displays help and exits."""
        with patch("sys.argv", ["rentabot", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "Rent-A-Bot" in captured.out
        assert "--config" in captured.out
        assert "--host" in captured.out
        assert "--port" in captured.out

    @patch("uvicorn.run")
    def test_main_with_explicit_config(self, mock_uvicorn, tmp_path, monkeypatch, capsys):
        """Test main with explicit --config argument."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("# test config")

        with patch("sys.argv", ["rentabot", "--config", str(config_file)]):
            main()

        # Verify config file was set in environment
        assert os.environ["RENTABOT_RESOURCE_DESCRIPTOR"] == str(config_file)

        # Verify uvicorn was called with correct arguments
        mock_uvicorn.assert_called_once_with(
            "rentabot.main:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info",
        )

        # Verify output messages
        captured = capsys.readouterr()
        assert "Using config file" in captured.out
        assert str(config_file) in captured.out

    @patch("uvicorn.run")
    def test_main_with_custom_host_and_port(self, mock_uvicorn, tmp_path, monkeypatch):
        """Test main with custom --host and --port."""
        monkeypatch.chdir(tmp_path)

        with patch("sys.argv", ["rentabot", "--host", "0.0.0.0", "--port", "9000"]):
            main()

        mock_uvicorn.assert_called_once_with(
            "rentabot.main:app",
            host="0.0.0.0",
            port=9000,
            reload=False,
            log_level="info",
        )

    @patch("uvicorn.run")
    def test_main_with_reload_flag(self, mock_uvicorn, tmp_path, monkeypatch):
        """Test main with --reload flag."""
        monkeypatch.chdir(tmp_path)

        with patch("sys.argv", ["rentabot", "--reload"]):
            main()

        mock_uvicorn.assert_called_once()
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["reload"] is True

    @patch("uvicorn.run")
    def test_main_with_log_level(self, mock_uvicorn, tmp_path, monkeypatch):
        """Test main with --log-level argument."""
        monkeypatch.chdir(tmp_path)

        with patch("sys.argv", ["rentabot", "--log-level", "debug"]):
            main()

        mock_uvicorn.assert_called_once()
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["log_level"] == "debug"

    @patch("uvicorn.run")
    @patch("rentabot.cli.find_config_file", return_value=None)
    def test_main_without_config(self, mock_find_config, mock_uvicorn, capsys):
        """Test main when no config file is found."""
        with patch("sys.argv", ["rentabot"]):
            main()

        # Verify message about no config
        captured = capsys.readouterr()
        assert "No config file found" in captured.out

        # Verify uvicorn was still called
        mock_uvicorn.assert_called_once()

    @patch("uvicorn.run")
    def test_main_discovers_config_automatically(self, mock_uvicorn, tmp_path, monkeypatch, capsys):
        """Test that main discovers config file automatically."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".rentabot.yaml"
        config_file.write_text("# auto-discovered config")

        with patch("sys.argv", ["rentabot"]):
            main()

        # Verify config was found and set
        assert os.environ["RENTABOT_RESOURCE_DESCRIPTOR"] == str(config_file)

        captured = capsys.readouterr()
        assert "Using config file" in captured.out
        assert str(config_file) in captured.out

    @patch("uvicorn.run")
    def test_main_short_options(self, mock_uvicorn, tmp_path, monkeypatch):
        """Test main with short option flags."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "config.yaml"
        config_file.write_text("# test")

        with patch("sys.argv", ["rentabot", "-c", str(config_file), "-p", "8080"]):
            main()

        mock_uvicorn.assert_called_once_with(
            "rentabot.main:app",
            host="127.0.0.1",
            port=8080,
            reload=False,
            log_level="info",
        )
