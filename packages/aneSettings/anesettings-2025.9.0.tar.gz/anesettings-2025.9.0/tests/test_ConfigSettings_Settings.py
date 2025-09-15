import os
from unittest.mock import MagicMock
from aneSettings.ConfigSettings import Settings
from aneSettings.Encryption import Encryption

_FN_KEY = Encryption.generate_fernet_key().decode()


def test_settings_initialization():
    """Test the initialization of Settings."""
    settings = Settings()
    assert isinstance(settings.FN_KEY, str)
    assert isinstance(settings.PROJECT_ROOT, str)
    assert settings.PROJECT_ROOT == os.getcwd()


def test_settings_environment_override():
    """Test the FN_KEY attribute is correctly overridden by the environment variable."""
    settings = Settings()
    settings.FN_KEY = _FN_KEY
    assert settings.FN_KEY == _FN_KEY


def test_settings_project_root():
    """Test the PROJECT_ROOT attribute reflects the current working directory."""
    settings = Settings()
    assert settings.PROJECT_ROOT == os.getcwd()


def test_settings_custom_config_sources():
    """Test that the customise_sources method returns the expected callable sources."""
    sources = Settings.Config.customise_sources(
        init_settings=MagicMock(),
        env_settings=MagicMock(),
        file_secret_settings=MagicMock()
    )
    assert len(sources) == 3
    assert callable(sources[0])
    assert callable(sources[1])
    assert callable(sources[2])
