# Version Information
from .__about__ import __version__

# Configuration import
from .ConfigSettings import Settings as ConfigSettings

# Utility imports
from .CustomLogging import logger
from .Encryption import Encryption as EncryptionService
from .ProjectRoot import project_root as get_project_root

# Define module exports
EXPORTS = [
    '__version__',
    'config',
    'logger',
    'encryption_service',
    'project_root'
]

# Initialize core services
config = ConfigSettings()
encryption_service = EncryptionService()
project_root = get_project_root()

# Define module exports
__all__ = EXPORTS
