
# aneSettings

aneSettings is a framework for developing scalable applications. It offers a set of core libraries and utilities to streamline the development workflow, enforce security best practices, and improve code maintainability. By supporting modern programming paradigms, it allows developers to build robust and efficient solutions with reduced overhead.

### Key Features:
- Security-First Approach: Built-in security measures to prevent common vulnerabilities.
- Scalability: Optimized to handle high loads and large-scale applications.
- Modularity: Highly modular architecture, allowing seamless integration and customization.
- Ease of Use: Developer-friendly APIs and comprehensive documentation.

### Goals:
- Accelerate development time while maintaining high code quality.
- Provide a flexible foundation to meet diverse application needs.
- Ensure application security without compromising performance.

---

### Core Components:
- **ConfigSettings**: Handles configuration and settings management
- **CustomLogging**: Provides customized logging functionality
- **Encryption**: Offers encryption-related utilities
- **ProjectRoot**: Manages project root detection and path resolution

---

### **_ConfigSettings:_**

```python
# Basic Logging and Config Settings
from aneSettings import logger, config

# Constants
FORMAT_PADDING = 25
SEPARATOR_LINE = "-" * 150


def log_sorted_settings(system_settings):
    """Logs the key-value pairs of sorted settings."""
    for setting_name, setting_value in system_settings:
        logger.info(f'{setting_name:>{FORMAT_PADDING}}: {setting_value}')


if __name__ == '__main__':
    # -------------------------------------------------------------------------------------------------
    # Example of viewing and sorting configuration settings
    # -------------------------------------------------------------------------------------------------
    logger.info(SEPARATOR_LINE)
    sorted_settings = sorted(config)
    log_sorted_settings(sorted_settings)
```

#### **_output_**

```shell
aneSettings | INFO     | ------------------------------------------------------------------------------------------------------------------------------------------------------
aneSettings | INFO     |               ENVIRONMENT: Local
aneSettings | INFO     |                    FN_KEY: pit...-iM2c=
aneSettings | INFO     |               LOG_APPNAME: aneSettings
aneSettings | INFO     |                LOG_FORMAT: {extra[app]} | <level>{level: <8}</level> | <cyan><level>{message}</level></cyan>
aneSettings | INFO     |                 LOG_LEVEL: DEBUG
aneSettings | INFO     |            MSSQL_DATABASE: {default_database}
aneSettings | INFO     |            MSSQL_HOSTNAME: {hostname}
aneSettings | INFO     |            MSSQL_PASSWORD: {password}
aneSettings | INFO     |                MSSQL_PORT: {port}
aneSettings | INFO     |               MSSQL_TRUST: {trust}
aneSettings | INFO     |            MSSQL_USERNAME: {username}
aneSettings | INFO     |              PROJECT_ROOT: /{project_root}/aneSettings
aneSettings | INFO     |              VERSION_CORE: 2025.9.0
```

---

### **_Encryption:_**

```python
# Basic Logging and Encryption
from aneSettings import logger, encryption_service

# Constants
FORMAT_PADDING = 25
SEPARATOR_LINE = "-" * 150


def log_formatted(key, value):
    """Helper to standardize log output."""
    logger.info(f'{key:>{FORMAT_PADDING}}: {value}')


if __name__ == '__main__':
    # -------------------------------------------------------------------------------------------------
    # Example of Encryption Usage
    # -------------------------------------------------------------------------------------------------

    # Data: set and show values
    logger.info(SEPARATOR_LINE)
    secret_data = "Sensitive Information"
    log_formatted(key="Data", value=secret_data)
    encryption_key = encryption_service.key.decode()
    log_formatted(key="Key", value=encryption_key)

    # Encryption: encrypt and decrypt
    logger.info(SEPARATOR_LINE)
    encrypted = encryption_service.encrypt(secret_data)
    log_formatted(key="Encryption successful", value=f"{encrypted != secret_data} - {encrypted.decode()}")

    decrypted = encryption_service.decrypt(encrypted)
    log_formatted(key="Decryption successful", value=f"{decrypted == secret_data} - {decrypted}")

    # Base64: encode and decode
    logger.info(SEPARATOR_LINE)
    b64_encoded = encryption_service.base64_encode(secret_data)
    log_formatted(key="Encode successful", value=f"{b64_encoded != secret_data} - {b64_encoded}")

    b64_decoded = encryption_service.base64_decode(b64_encoded)
    log_formatted(key="Decode successful", value=f"{b64_decoded == secret_data} - {b64_decoded}")

    # Generate a new key to replace the one in .env.settings `fn_key`
    logger.info(SEPARATOR_LINE)
    new_fn_key = encryption_service.generate_fernet_key().decode()
    log_formatted(key="New fn_key", value=f"{new_fn_key}")
    log_formatted(key="", value="Use this key to replace the one in .env.settings `fn_key`")

    logger.info(SEPARATOR_LINE)
```

#### **_output_**

```shell
aneSettings | INFO     | ------------------------------------------------------------------------------------------------------------------------------------------------------
aneSettings | INFO     |                      Data: Sensitive Information
aneSettings | INFO     |                       Key: pitANnjVW1OX2LuVqrWw1H2b69wCewmdARQzr6-iM2c=
aneSettings | INFO     | ------------------------------------------------------------------------------------------------------------------------------------------------------
aneSettings | INFO     |     Encryption successful: True - gAAAAABox0DLjm7IOmFNRio8FYnp5tLVtMqPFpx5qFbbeot_jIUNah8XqLqHhPNmvaw1HpIBe0ebsna7ou8BrVnQ9erv6Fr1VK_O7PC3xDDXQXSEnyA2WhE=
aneSettings | INFO     |     Decryption successful: True - Sensitive Information
aneSettings | INFO     | ------------------------------------------------------------------------------------------------------------------------------------------------------
aneSettings | INFO     |         Encode successful: True - U2Vuc2l0aXZlIEluZm9ybWF0aW9u
aneSettings | INFO     |         Decode successful: True - Sensitive Information
aneSettings | INFO     | ------------------------------------------------------------------------------------------------------------------------------------------------------
aneSettings | INFO     |                New fn_key: RAl2XHZUwXQyZwXdzwVWJGKDDSwyJluh41De9KHw9oI=
aneSettings | INFO     |                          : Use this key to replace the one in .env.settings `fn_key`
```

---

### **_ProjectRoot:_**

```python
# Basic Logging and Project Path Operations
from aneSettings import logger, project_root

# Constants
FORMAT_PADDING = 25
SEPARATOR_LINE = "-" * 150


def log_formatted(key, value):
    """Helper to standardize log output."""
    logger.info(f'{key:>{FORMAT_PADDING}}: {value}')


if __name__ == "__main__":
    # -------------------------------------------------------------------------------------------------
    # Example of Project Path Operations
    # -------------------------------------------------------------------------------------------------

    # Get project-related paths
    root_path = project_root
    config_path = project_root / "config"
    data_path = project_root / "data"

    logger.info(SEPARATOR_LINE)
    log_formatted(key="Project root", value=root_path)
    log_formatted(key="Config path", value=config_path)
    log_formatted(key="Data path", value=data_path)
    logger.info(SEPARATOR_LINE)
```

#### **_output_**

```shell
aneSettings | INFO     | ------------------------------------------------------------------------------------------------------------------------------------------------------
aneSettings | INFO     |              Project root: {project_root}
aneSettings | INFO     |               Config path: {project_root}/config
aneSettings | INFO     |                 Data path: {project_root}/data
aneSettings | INFO     | ------------------------------------------------------------------------------------------------------------------------------------------------------
```