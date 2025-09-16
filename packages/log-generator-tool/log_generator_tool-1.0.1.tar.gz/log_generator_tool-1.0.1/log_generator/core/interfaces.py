"""
Core interfaces and abstract base classes for the log generator system.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class LogGenerator(ABC):
    """
    Abstract base class for all log generators.

    This interface defines the contract that all log generators must implement
    to ensure consistency and extensibility across different log types.
    """

    @abstractmethod
    def generate_log(self) -> str:
        """
        Generate a single log entry.

        Returns:
            str: A formatted log entry string
        """
        pass

    def generate_log_with_time(self, timestamp: datetime) -> str:
        """
        Generate a log entry with a specific timestamp (virtual time support).

        Args:
            timestamp: The timestamp to use for the log entry

        Returns:
            str: A formatted log entry string with the specified timestamp
        """
        # Default implementation - subclasses can override for better virtual time support
        return self.generate_log()

    @abstractmethod
    def get_log_pattern(self) -> str:
        """
        Get the regex pattern that matches this log type.

        Returns:
            str: Regular expression pattern for log validation
        """
        pass

    @abstractmethod
    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if a log entry matches the expected format.

        Args:
            log_entry (str): Log entry to validate

        Returns:
            bool: True if log entry is valid, False otherwise
        """
        pass

    def set_custom_fields(self, fields: Dict[str, Any]) -> None:
        """
        Set custom fields for log generation.

        Args:
            fields (Dict[str, Any]): Custom field definitions
        """
        pass

    def get_sample_logs(self, count: int = 5) -> List[str]:
        """
        Generate sample log entries for testing and validation.

        Args:
            count (int): Number of sample logs to generate

        Returns:
            List[str]: List of sample log entries
        """
        return [self.generate_log() for _ in range(count)]


class OutputHandler(ABC):
    """
    Abstract base class for all output handlers.

    This interface defines how generated logs should be output to different
    destinations (file, console, network, etc.).
    """

    @abstractmethod
    def write_log(self, log_entry: str) -> None:
        """
        Write a log entry to the output destination.

        Args:
            log_entry (str): Log entry to write
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the output handler and clean up resources.
        """
        pass

    def flush(self) -> None:
        """
        Flush any buffered output.
        Default implementation does nothing.
        """
        pass


class ConfigurationManager(ABC):
    """
    Abstract base class for configuration management.

    Handles loading, saving, and validating configuration files.
    """

    @abstractmethod
    def load_config(self, path: str) -> Dict[str, Any]:
        """
        Load configuration from file.

        Args:
            path (str): Path to configuration file

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        pass

    @abstractmethod
    def save_config(self, config: Dict[str, Any], path: str) -> None:
        """
        Save configuration to file.

        Args:
            config (Dict[str, Any]): Configuration to save
            path (str): Path to save configuration
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure and values.

        Args:
            config (Dict[str, Any]): Configuration to validate

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_log_type_config(self, log_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific log type.

        Args:
            log_type (str): Log type identifier

        Returns:
            Dict[str, Any]: Log type configuration
        """
        pass


class LogFactory(ABC):
    """
    Abstract factory for creating log generator instances.

    Implements the factory pattern for dynamic log generator creation
    and management.
    """

    @abstractmethod
    def create_generator(self, log_type: str, config: Dict[str, Any]) -> LogGenerator:
        """
        Create a log generator instance for the specified type.

        Args:
            log_type (str): Type of log generator to create
            config (Dict[str, Any]): Configuration for the generator

        Returns:
            LogGenerator: Instance of the requested log generator
        """
        pass

    @abstractmethod
    def register_generator(self, log_type: str, generator_class: type) -> None:
        """
        Register a new log generator type.

        Args:
            log_type (str): Identifier for the log type
            generator_class (type): Class that implements LogGenerator
        """
        pass

    @abstractmethod
    def get_available_types(self) -> List[str]:
        """
        Get list of available log generator types.

        Returns:
            List[str]: List of registered log type identifiers
        """
        pass
