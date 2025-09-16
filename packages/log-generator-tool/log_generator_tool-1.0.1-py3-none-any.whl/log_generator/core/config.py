"""
Configuration management system for the log generator.

This module provides the ConfigurationManager class that handles loading,
saving, and validating configuration files in YAML and JSON formats.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from .exceptions import ConfigurationError


class ConfigurationManager:
    """
    Manages configuration loading, saving, and validation for the log generator.

    Supports both YAML and JSON configuration files with schema validation
    and default value application.
    """

    # Default configuration values
    DEFAULT_CONFIG = {
        "log_generator": {
            "global": {
                "output_format": "multi_file",
                "output_path": "./logs",
                "generation_interval": 0.1,
                "random_interval": False,
                "total_logs": 10000,
                "multi_file": {
                    "file_pattern": "{log_type}_{date}.log",
                    "date_format": "%Y%m%d",
                    "separate_by_type": True,
                },
                "virtual_time": True,
                "start_time": None,
            },
            "log_types": {
                "nginx_access": {
                    "enabled": True,
                    "frequency": 0.4,
                    "patterns": ["combined", "common"],
                    "custom_fields": {
                        "ip_ranges": ["192.168.1.0/24", "10.0.0.0/8"],
                        "status_codes": {200: 0.7, 404: 0.15, 500: 0.1, 403: 0.05},
                        "user_agents": [
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                            "curl/7.68.0",
                        ],
                    },
                },
                "nginx_error": {
                    "enabled": True,
                    "frequency": 0.05,
                    "error_levels": ["error", "warn", "crit"],
                },
                "syslog": {
                    "enabled": True,
                    "frequency": 0.15,
                    "facilities": ["kern", "mail", "daemon", "auth"],
                    "severities": ["info", "notice", "warning", "err"],
                },
                "fastapi": {
                    "enabled": True,
                    "frequency": 0.15,
                    "log_levels": ["INFO", "DEBUG", "WARNING", "ERROR"],
                    "endpoints": ["/api/users", "/api/orders", "/health", "/metrics"],
                },
                "custom": {
                    "enabled": False,
                    "frequency": 0.2,
                    "template": "{timestamp} [{level}] {message}",
                    "fields": {
                        "timestamp": "datetime",
                        "level": ["INFO", "WARN", "ERROR"],
                        "message": "sentence",
                    },
                },
            },
        }
    }

    # Required configuration keys
    REQUIRED_KEYS = ["log_generator", "log_generator.global", "log_generator.log_types"]

    # Valid output formats
    VALID_OUTPUT_FORMATS = ["file", "console", "network", "json", "multi_file"]

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._config: Dict[str, Any] = {}
        self._config_path: Optional[str] = None

    def load_config(self, path: str) -> Dict[str, Any]:
        """
        Load configuration from a YAML or JSON file.

        Args:
            path: Path to the configuration file

        Returns:
            Loaded configuration dictionary

        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        config_path = Path(path)

        if not config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {path}",
                error_code="CONFIG_FILE_NOT_FOUND",
            )

        # Check file format before opening
        if config_path.suffix.lower() not in [".yaml", ".yml", ".json"]:
            raise ConfigurationError(
                f"Unsupported configuration file format: {config_path.suffix}",
                error_code="UNSUPPORTED_FORMAT",
            )

        try:
            with open(config_path, "r", encoding="utf-8") as file:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    config = yaml.safe_load(file)
                elif config_path.suffix.lower() == ".json":
                    config = json.load(file)
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Failed to parse YAML configuration: {e}",
                error_code="YAML_PARSE_ERROR",
            )
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Failed to parse JSON configuration: {e}",
                error_code="JSON_PARSE_ERROR",
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration file: {e}", error_code="FILE_READ_ERROR"
            )

        if config is None:
            config = {}

        # Apply default values
        config = self._apply_defaults(config)

        # Validate configuration
        self.validate_config(config)

        self._config = config
        self._config_path = path

        return config

    def save_config(self, config: Dict[str, Any], path: str) -> None:
        """
        Save configuration to a YAML or JSON file.

        Args:
            config: Configuration dictionary to save
            path: Path where to save the configuration file

        Raises:
            ConfigurationError: If file cannot be saved
        """
        config_path = Path(path)

        # Validate configuration before saving
        self.validate_config(config)

        try:
            # Create directory if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as file:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    yaml.dump(
                        config,
                        file,
                        default_flow_style=False,
                        allow_unicode=True,
                        indent=2,
                    )
                elif config_path.suffix.lower() == ".json":
                    json.dump(config, file, indent=2, ensure_ascii=False)
                else:
                    raise ConfigurationError(
                        f"Unsupported configuration file format: {config_path.suffix}",
                        error_code="UNSUPPORTED_FORMAT",
                    )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration file: {e}", error_code="FILE_WRITE_ERROR"
            )

        self._config = config
        self._config_path = path

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure and values.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ConfigurationError(
                "Configuration must be a dictionary", error_code="INVALID_CONFIG_TYPE"
            )

        # Check required keys
        for key_path in self.REQUIRED_KEYS:
            if not self._has_nested_key(config, key_path):
                raise ConfigurationError(
                    f"Missing required configuration key: {key_path}",
                    error_code="MISSING_REQUIRED_KEY",
                )

        # Validate global settings
        global_config = config.get("log_generator", {}).get("global", {})
        self._validate_global_config(global_config)

        # Validate log types
        log_types = config.get("log_generator", {}).get("log_types", {})
        self._validate_log_types_config(log_types)

        return True

    def get_log_type_config(self, log_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific log type.

        Args:
            log_type: Name of the log type

        Returns:
            Configuration dictionary for the log type

        Raises:
            ConfigurationError: If log type is not configured
        """
        if not self._config:
            raise ConfigurationError(
                "No configuration loaded", error_code="NO_CONFIG_LOADED"
            )

        log_types = self._config.get("log_generator", {}).get("log_types", {})

        if log_type not in log_types:
            raise ConfigurationError(
                f"Log type '{log_type}' not found in configuration",
                error_code="LOG_TYPE_NOT_FOUND",
            )

        return log_types[log_type].copy()

    def get_global_config(self) -> Dict[str, Any]:
        """
        Get global configuration settings.

        Returns:
            Global configuration dictionary

        Raises:
            ConfigurationError: If no configuration is loaded
        """
        if not self._config:
            raise ConfigurationError(
                "No configuration loaded", error_code="NO_CONFIG_LOADED"
            )

        return self._config.get("log_generator", {}).get("global", {}).copy()

    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration.

        Returns:
            Complete configuration dictionary
        """
        import copy

        return copy.deepcopy(self._config) if self._config else {}

    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply default values to configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with defaults applied
        """
        return self._deep_merge(self.DEFAULT_CONFIG.copy(), config)

    def _deep_merge(
        self, default: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, with override taking precedence.

        Args:
            default: Default dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = default.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _has_nested_key(self, config: Dict[str, Any], key_path: str) -> bool:
        """
        Check if a nested key exists in the configuration.

        Args:
            config: Configuration dictionary
            key_path: Dot-separated key path (e.g., "log_generator.global")

        Returns:
            True if key exists, False otherwise
        """
        keys = key_path.split(".")
        current = config

        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]

        return True

    def _validate_global_config(self, global_config: Dict[str, Any]) -> None:
        """
        Validate global configuration settings.

        Args:
            global_config: Global configuration dictionary

        Raises:
            ConfigurationError: If global configuration is invalid
        """
        # Validate output format
        output_format = global_config.get("output_format")
        if output_format not in self.VALID_OUTPUT_FORMATS:
            raise ConfigurationError(
                f"Invalid output format '{output_format}'. "
                f"Valid formats: {', '.join(self.VALID_OUTPUT_FORMATS)}",
                error_code="INVALID_OUTPUT_FORMAT",
            )

        # Validate generation interval
        interval = global_config.get("generation_interval")
        if not isinstance(interval, (int, float)) or interval <= 0:
            raise ConfigurationError(
                "generation_interval must be a positive number",
                error_code="INVALID_GENERATION_INTERVAL",
            )

        # Validate total logs
        total_logs = global_config.get("total_logs")
        if not isinstance(total_logs, int) or total_logs < 0:
            raise ConfigurationError(
                "total_logs must be a non-negative integer",
                error_code="INVALID_TOTAL_LOGS",
            )

    def _validate_log_types_config(self, log_types: Dict[str, Any]) -> None:
        """
        Validate log types configuration.

        Args:
            log_types: Log types configuration dictionary

        Raises:
            ConfigurationError: If log types configuration is invalid
        """
        if not log_types:
            raise ConfigurationError(
                "At least one log type must be configured",
                error_code="NO_LOG_TYPES_CONFIGURED",
            )

        total_frequency = 0.0
        enabled_count = 0

        for log_type, config in log_types.items():
            if not isinstance(config, dict):
                raise ConfigurationError(
                    f"Log type '{log_type}' configuration must be a dictionary",
                    error_code="INVALID_LOG_TYPE_CONFIG",
                )

            # Check if enabled
            enabled = config.get("enabled", False)
            if enabled:
                enabled_count += 1

                # Validate frequency
                frequency = config.get("frequency", 0.0)
                if (
                    not isinstance(frequency, (int, float))
                    or frequency < 0
                    or frequency > 1
                ):
                    raise ConfigurationError(
                        f"Log type '{log_type}' frequency must be between 0 and 1",
                        error_code="INVALID_FREQUENCY",
                    )

                total_frequency += frequency

        if enabled_count == 0:
            raise ConfigurationError(
                "At least one log type must be enabled",
                error_code="NO_LOG_TYPES_ENABLED",
            )

        if total_frequency > 1.0:
            raise ConfigurationError(
                f"Total frequency of enabled log types ({total_frequency:.2f}) "
                "cannot exceed 1.0",
                error_code="FREQUENCY_EXCEEDS_LIMIT",
            )
