from unittest.mock import patch, mock_open

import pytest

from aneSettings.ConfigSettings import ConfigManager


@pytest.fixture
def config_manager_instance():
    """Fixture to initialize ConfigManager instance."""
    validation_rules = {'TEST_KEY': 'ERROR'}
    return ConfigManager(validation_rules=validation_rules)


def test_config_manager_initialization(config_manager_instance):
    """Test initialization of ConfigManager."""
    assert isinstance(config_manager_instance.parameters, dict)
    assert isinstance(config_manager_instance.validation_rules, dict)
    assert isinstance(config_manager_instance.errors, dict)
    assert config_manager_instance.error_occurred is False
    assert isinstance(config_manager_instance.config_dir, str)
    assert isinstance(config_manager_instance.secret_dir, str)


def test_ensure_directory_creation():
    """Test that ConfigManager._ensure_directory creates a directory."""
    with patch("os.makedirs") as mock_makedirs:
        ConfigManager._ensure_directory("/some/path")
        mock_makedirs.assert_called_once_with("/some/path", exist_ok=True)


def test_initialize_file_creates_file():
    """Test that ConfigManager._initialize_file creates a file."""
    with patch("builtins.open", mock_open()) as mock_file, patch("os.path.exists", return_value=False):
        ConfigManager._initialize_file("/some/file", "default content")
        mock_file.assert_called_once_with("/some/file", "w")


def test_initialize_file_does_not_overwrite_existing_file():
    """Test that ConfigManager._initialize_file does not overwrite an existing file."""
    with patch("builtins.open", mock_open()) as mock_file, patch("os.path.exists", return_value=True):
        ConfigManager._initialize_file("/some/file")
        mock_file.assert_not_called()


def test_parse_line_correctly_extracts_key_value():
    """Test that ConfigManager._parse_line extracts key-value pairs properly."""
    line = 'KEY=value # comment'
    result = ConfigManager._parse_line(line)
    assert result == ("KEY", "value")


def test_validate_configuration_identifies_missing_keys(config_manager_instance):
    """Test that ConfigManager.validate_configuration identifies missing validation keys."""
    config_manager_instance.parameters = {}
    config_manager_instance.validate_configuration()

    assert config_manager_instance.error_occurred is True
    assert "TEST_KEY" in config_manager_instance.errors
    assert "details" in config_manager_instance.errors["TEST_KEY"]


def test_error_flag_is_set_for_missing_keys(config_manager_instance):
    """Test that error_occurred is set when validation fails."""
    config_manager_instance.parameters = {}
    config_manager_instance.validate_configuration()
    assert config_manager_instance.error_occurred is True


def test_error_flag_is_unset_on_valid_configuration():
    """Test that error_occurred is not set when configuration is valid."""
    validation_rules = {'KEY': 'ERROR'}
    config_manager_instance = ConfigManager(validation_rules=validation_rules)
    config_manager_instance.parameters = {'KEY': 'value'}
    config_manager_instance.validate_configuration()
    assert config_manager_instance.error_occurred is False
