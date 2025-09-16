"""
Factory for creating output handlers based on configuration.
"""

from pathlib import Path
from typing import Any, Dict, List

from ..outputs.console_handler import ConsoleOutputHandler
from ..outputs.file_handler import FileOutputHandler
from ..outputs.json_handler import JSONOutputHandler
from ..outputs.multi_file_handler import MultiFileOutputHandler
from ..outputs.network_handler import NetworkOutputHandler
from .exceptions import ConfigurationError
from .interfaces import OutputHandler


class OutputHandlerFactory:
    """
    Factory class for creating output handlers based on configuration.
    """

    @staticmethod
    def create_handlers(config: Dict[str, Any]) -> List[OutputHandler]:
        """
        Create output handlers based on configuration.

        Args:
            config: Configuration dictionary

        Returns:
            List of configured output handlers

        Raises:
            ConfigurationError: If configuration is invalid
        """
        handlers = []
        global_config = config.get("log_generator", {}).get("global", {})

        output_format = global_config.get("output_format", "file")
        output_path = global_config.get("output_path", "./logs")

        if output_format == "file":
            # Single file output
            file_path = Path(output_path) / "generated_logs.log"
            handler = FileOutputHandler(
                file_path=file_path,
                rotation_size=global_config.get("rotation_size"),
                rotation_time=global_config.get("rotation_time"),
                max_files=global_config.get("max_files", 10),
            )
            handlers.append(handler)

        elif output_format == "multi_file":
            # Multi-file output (separate files for each log type)
            multi_file_config = global_config.get("multi_file", {})

            handler = MultiFileOutputHandler(
                base_path=output_path,
                file_pattern=multi_file_config.get(
                    "file_pattern", "{log_type}_{date}.log"
                ),
                date_format=multi_file_config.get("date_format", "%Y%m%d"),
                rotation_size=global_config.get("rotation_size"),
                rotation_time=global_config.get("rotation_time"),
                max_files=global_config.get("max_files", 10),
            )
            handlers.append(handler)

        elif output_format == "console":
            # Console output
            handler = ConsoleOutputHandler(
                use_colors=global_config.get("use_colors", True),
                timestamp_format=global_config.get(
                    "timestamp_format", "%Y-%m-%d %H:%M:%S"
                ),
            )
            handlers.append(handler)

        elif output_format == "json":
            # JSON file output
            file_path = Path(output_path) / "generated_logs.json"
            handler = JSONOutputHandler(
                file_path=file_path,
                pretty_print=global_config.get("pretty_print", False),
            )
            handlers.append(handler)

        elif output_format == "network":
            # Network output
            network_config = global_config.get("network", {})
            if not network_config:
                raise ConfigurationError(
                    "Network configuration required for network output format"
                )

            handler = NetworkOutputHandler(
                host=network_config.get("host", "localhost"),
                port=network_config.get("port", 514),
                protocol=network_config.get("protocol", "udp"),
            )
            handlers.append(handler)

        else:
            raise ConfigurationError(f"Unknown output format: {output_format}")

        return handlers

    @staticmethod
    def create_file_handler(file_path: str, **kwargs) -> FileOutputHandler:
        """
        Create a single file output handler.

        Args:
            file_path: Path to the log file
            **kwargs: Additional configuration options

        Returns:
            FileOutputHandler instance
        """
        return FileOutputHandler(file_path=file_path, **kwargs)

    @staticmethod
    def create_multi_file_handler(base_path: str, **kwargs) -> MultiFileOutputHandler:
        """
        Create a multi-file output handler.

        Args:
            base_path: Base directory for log files
            **kwargs: Additional configuration options

        Returns:
            MultiFileOutputHandler instance
        """
        return MultiFileOutputHandler(base_path=base_path, **kwargs)

    @staticmethod
    def create_console_handler(**kwargs) -> ConsoleOutputHandler:
        """
        Create a console output handler.

        Args:
            **kwargs: Configuration options

        Returns:
            ConsoleOutputHandler instance
        """
        return ConsoleOutputHandler(**kwargs)
