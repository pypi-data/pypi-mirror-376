"""
Core engine for the log generator system.

This module provides the LogGeneratorCore class that orchestrates the entire
log generation process, including starting/stopping generation, collecting
statistics, and handling errors.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .config import ConfigurationManager
from .exceptions import ConfigurationError, GenerationError
from .interfaces import LogFactory, LogGenerator, OutputHandler
from .models import GenerationStatistics, LogEntry
from .output_factory import OutputHandlerFactory


class LogGeneratorCore:
    """
    Core engine that orchestrates the log generation process.

    This class manages the lifecycle of log generation, coordinates between
    different generators and output handlers, collects statistics, and
    provides error handling and recovery mechanisms.
    """

    def __init__(self, config_path: str | None = None):
        """
        Initialize the log generator core.

        Args:
            config_path: Path to configuration file (optional)
        """
        self._config_manager = ConfigurationManager()
        self._config: Dict[str, Any] = {}
        self._log_factory: Optional[LogFactory] = None
        self._generators: Dict[str, LogGenerator] = {}
        self._output_handlers: List[OutputHandler] = []
        self._statistics = GenerationStatistics()

        # Generation control
        self._is_running = False
        self._generation_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Error handling
        self._error_handlers: List[Callable[[Exception], None]] = []
        self._max_retries = 3
        self._retry_delay = 1.0

        # Logging
        self._logger = logging.getLogger(__name__)

        # Load configuration if provided
        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str) -> None:
        """
        Load configuration from file.

        Args:
            config_path: Path to configuration file

        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
        try:
            self._config = self._config_manager.load_config(config_path)
            self._logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            self._logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def set_log_factory(self, factory: LogFactory) -> None:
        """
        Set the log factory for creating generators.

        Args:
            factory: LogFactory instance
        """
        self._log_factory = factory
        self._logger.info("Log factory set")

    def add_output_handler(self, handler: OutputHandler) -> None:
        """
        Add an output handler for generated logs.

        Args:
            handler: OutputHandler instance
        """
        self._output_handlers.append(handler)
        self._logger.info(f"Output handler added: {type(handler).__name__}")

    def add_error_handler(self, handler: Callable[[Exception], None]) -> None:
        """
        Add an error handler callback.

        Args:
            handler: Function to call when errors occur
        """
        self._error_handlers.append(handler)

    def start_generation(self) -> None:
        """
        Start the log generation process.

        This method initializes generators based on configuration and starts
        the generation thread.

        Raises:
            GenerationError: If generation cannot be started
        """
        if self._is_running:
            self._logger.warning("Log generation is already running")
            return

        # Check if configuration is loaded
        if not self._config:
            raise GenerationError("No configuration loaded")

        # Check if log factory is set
        if not self._log_factory:
            raise GenerationError("No log factory set")

        # Check if output handlers are configured
        if not self._output_handlers:
            raise GenerationError("No output handlers configured")

        try:
            self._initialize_generators()
            self._reset_statistics()

            # Start generation thread
            self._stop_event.clear()
            self._generation_thread = threading.Thread(
                target=self._generation_loop, name="LogGenerationThread"
            )
            self._generation_thread.daemon = True
            self._generation_thread.start()

            self._is_running = True
            self._statistics.start_time = datetime.now()

            self._logger.info("Log generation started")

        except Exception as e:
            self._logger.error(f"Failed to start log generation: {e}")
            self._handle_error(GenerationError(f"Failed to start generation: {e}"))
            raise

    def stop_generation(self) -> None:
        """
        Stop the log generation process.

        This method gracefully stops the generation thread and cleans up
        resources.
        """
        if not self._is_running:
            self._logger.warning("Log generation is not running")
            return

        try:
            # Signal stop
            self._stop_event.set()

            # Wait for thread to finish
            if self._generation_thread and self._generation_thread.is_alive():
                self._generation_thread.join(timeout=5.0)

                if self._generation_thread.is_alive():
                    self._logger.warning("Generation thread did not stop gracefully")

            self._is_running = False
            self._statistics.end_time = datetime.now()
            self._statistics.calculate_rate()

            # Flush and close output handlers
            for handler in self._output_handlers:
                try:
                    if hasattr(handler, "flush"):
                        handler.flush()
                    handler.close()
                except Exception as e:
                    self._logger.error(f"Error closing output handler: {e}")

            self._logger.info("Log generation stopped")

        except Exception as e:
            self._logger.error(f"Error stopping log generation: {e}")
            self._handle_error(GenerationError(f"Error stopping generation: {e}"))

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current generation statistics.

        Returns:
            Dictionary containing generation statistics
        """
        # Update rate calculation if still running
        if self._is_running and self._statistics.start_time:
            current_time = datetime.now()
            duration = (current_time - self._statistics.start_time).total_seconds()
            if duration > 0:
                self._statistics.generation_rate = (
                    self._statistics.total_logs_generated / duration
                )

        stats_dict = self._statistics.to_dict()

        # Add compatibility fields for tests
        stats_dict["log_type_counts"] = stats_dict.get("logs_by_type", {})
        stats_dict["error_count"] = stats_dict.get("errors_count", 0)

        return stats_dict

    def is_running(self) -> bool:
        """
        Check if log generation is currently running.

        Returns:
            True if generation is running, False otherwise
        """
        return self._is_running

    def add_log_type(self, log_type: str, generator: LogGenerator) -> None:
        """
        Add a log generator for a specific type.

        Args:
            log_type: Identifier for the log type
            generator: LogGenerator instance
        """
        self._generators[log_type] = generator
        self._logger.info(f"Log generator added for type: {log_type}")

    def _initialize_generators(self) -> None:
        """
        Initialize log generators based on configuration.

        Raises:
            GenerationError: If generators cannot be initialized
        """
        if not self._config:
            raise GenerationError("No configuration loaded")

        if not self._log_factory:
            raise GenerationError("No log factory set")

        log_types_config = self._config.get("log_generator", {}).get("log_types", {})

        # Clear existing generators
        self._generators.clear()

        # Initialize enabled generators
        for log_type, config in log_types_config.items():
            if config.get("enabled", False):
                try:
                    generator = self._log_factory.create_generator(log_type, config)
                    self._generators[log_type] = generator
                    self._logger.info(f"Initialized generator for {log_type}")
                except Exception as e:
                    self._logger.error(
                        f"Failed to initialize generator for {log_type}: {e}"
                    )
                    self._statistics.add_error()
                    raise GenerationError(
                        f"Failed to initialize generator for {log_type}: {e}"
                    )

        if not self._generators:
            raise GenerationError("No generators initialized")

        # Initialize output handlers if none are configured
        if not self._output_handlers:
            try:
                self._output_handlers = OutputHandlerFactory.create_handlers(
                    self._config
                )
                self._logger.info(
                    f"Initialized {len(self._output_handlers)} output handlers"
                )
            except Exception as e:
                self._logger.error(f"Failed to initialize output handlers: {e}")
                # Don't raise an error here, as output handlers can be added later
                # raise GenerationError(f"Failed to initialize output handlers: {e}")

    def _generation_loop(self) -> None:
        """
        High-performance generation loop using virtual time.

        This method generates logs continuously without sleep, using virtual
        timestamps to simulate realistic log timing.
        """
        global_config = self._config.get("log_generator", {}).get("global", {})
        generation_interval = global_config.get("generation_interval", 0.1)
        random_interval = global_config.get("random_interval", False)
        total_logs = global_config.get("total_logs", 0)

        # Virtual time management
        virtual_time_enabled = global_config.get("virtual_time", True)
        logs_per_second = 1.0 / generation_interval if generation_interval > 0 else 1000

        self._logger.info(
            f"Generation loop started (target rate: {logs_per_second:.0f} logs/sec, total: {total_logs})"
        )

        # Initialize virtual time
        from datetime import datetime, timedelta

        # Check if custom start time is provided
        start_time_str = global_config.get("start_time")
        if start_time_str:
            try:
                if len(start_time_str) == 10:  # YYYY-MM-DD format
                    virtual_start_time = datetime.strptime(start_time_str, "%Y-%m-%d")
                elif len(start_time_str) == 19:  # YYYY-MM-DD HH:MM:SS format
                    virtual_start_time = datetime.strptime(
                        start_time_str, "%Y-%m-%d %H:%M:%S"
                    )
                else:
                    self._logger.warning(
                        f"Invalid start time format: {start_time_str}, using current time"
                    )
                    virtual_start_time = datetime.now()

                self._logger.info(f"Using custom start time: {virtual_start_time}")
            except ValueError as e:
                self._logger.warning(
                    f"Failed to parse start time: {e}, using current time"
                )
                virtual_start_time = datetime.now()
        else:
            virtual_start_time = datetime.now()

        virtual_current_time = virtual_start_time

        try:
            batch_size = min(
                1000, max(10, int(logs_per_second / 10))
            )  # Adaptive batch size
            logs_generated_in_batch = 0

            while not self._stop_event.is_set():
                # Check if we've reached the total log limit
                if (
                    total_logs > 0
                    and self._statistics.total_logs_generated >= total_logs
                ):
                    self._logger.info(f"Reached total log limit: {total_logs}")
                    break

                # Generate logs in batches for maximum performance
                for _ in range(batch_size):
                    if self._stop_event.is_set():
                        break

                    # Check limit before generating each log
                    if (
                        total_logs > 0
                        and self._statistics.total_logs_generated >= total_logs
                    ):
                        break

                    # Select a random log type based on frequency weights
                    selected_log_type = self._select_log_type_by_frequency()
                    if not selected_log_type:
                        continue

                    try:
                        generator = self._generators[selected_log_type]

                        # Generate log with virtual timestamp if supported
                        if virtual_time_enabled and hasattr(
                            generator, "generate_log_with_time"
                        ):
                            log_entry = generator.generate_log_with_time(
                                virtual_current_time
                            )
                            self._logger.debug(
                                f"Generated log with virtual time {virtual_current_time} for {selected_log_type}"
                            )
                        else:
                            log_entry = generator.generate_log()
                            self._logger.debug(
                                f"Generated log with current time for {selected_log_type} (virtual_time_enabled={virtual_time_enabled}, has_method={hasattr(generator, 'generate_log_with_time')})"
                            )

                        self._output_log(log_entry, selected_log_type)
                        self._statistics.add_log(selected_log_type)
                        logs_generated_in_batch += 1

                        # Advance virtual time
                        if virtual_time_enabled:
                            # Use random interval if enabled, otherwise use fixed interval
                            if random_interval:
                                import random

                                actual_interval = random.uniform(0, generation_interval)
                            else:
                                actual_interval = generation_interval
                            virtual_current_time += timedelta(seconds=actual_interval)
                    except Exception as e:
                        self._logger.error(
                            f"Error generating log for {selected_log_type}: {e}"
                        )
                        self._statistics.add_error()
                        self._handle_error(
                            GenerationError(
                                f"Error generating {selected_log_type} log: {e}"
                            )
                        )

                # Minimal sleep only for CPU breathing room (not for timing)
                if logs_generated_in_batch > 0:
                    # Very short sleep to prevent 100% CPU usage
                    import time

                    time.sleep(0.001)  # 1ms - just for CPU relief
                    logs_generated_in_batch = 0
                else:
                    # If no logs generated, sleep a bit longer to avoid busy waiting
                    import time

                    time.sleep(0.01)  # 10ms

        finally:
            self._logger.info("Generation loop ended")
            # Mark as not running when loop ends
            self._is_running = False
            # Set end time if not already set
            if self._statistics.end_time is None:
                self._statistics.end_time = datetime.now()
                self._statistics.calculate_rate()

    def _output_log(self, log_entry: str, log_type: str) -> None:
        """
        Output a log entry to all configured handlers.

        Args:
            log_entry: Generated log entry string
            log_type: Type of log that was generated
        """
        for handler in self._output_handlers:
            try:
                # Check if handler supports log_type parameter (multi-file handler)
                if hasattr(handler, "write_log"):
                    import inspect

                    sig = inspect.signature(handler.write_log)
                    if "log_type" in sig.parameters:
                        handler.write_log(log_entry, log_type=log_type)
                    else:
                        handler.write_log(log_entry)
                else:
                    handler.write_log(log_entry)

                # Flush less frequently for better performance
                if self._statistics.total_logs_generated % 100 == 0:
                    if hasattr(handler, "flush"):
                        handler.flush()
            except Exception as e:
                self._logger.error(
                    f"Error writing log to handler {type(handler).__name__}: {e}"
                )
                self._statistics.add_error()
                self._handle_error(GenerationError(f"Output error: {e}"))

    def _select_log_type_by_frequency(self) -> Optional[str]:
        """
        Select a log type based on frequency weights.

        Returns:
            Selected log type or None if no generators available
        """
        if not self._generators:
            return None

        import random

        # Build weighted list based on frequency
        weighted_types = []
        for log_type in self._generators.keys():
            log_config = (
                self._config.get("log_generator", {})
                .get("log_types", {})
                .get(log_type, {})
            )
            frequency = log_config.get("frequency", 1.0)
            # Convert frequency to weight (multiply by 100 for better distribution)
            weight = max(1, int(frequency * 100))
            weighted_types.extend([log_type] * weight)

        if not weighted_types:
            return None

        return random.choice(weighted_types)

    def _reset_statistics(self) -> None:
        """Reset generation statistics."""
        self._statistics = GenerationStatistics()

    def _handle_error(self, error: Exception) -> None:
        """
        Handle errors with registered error handlers.

        Args:
            error: Exception that occurred
        """
        # Call registered error handlers
        for handler in self._error_handlers:
            try:
                handler(error)
            except Exception as e:
                self._logger.error(f"Error in error handler: {e}")

        # Log the error
        self._logger.error(f"Error handled: {error}")

    def _retry_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Retry an operation with exponential backoff.

        Args:
            operation: Function to retry
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the operation

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(self._max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2**attempt)
                    self._logger.warning(
                        f"Operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    self._logger.error(
                        f"Operation failed after {self._max_retries} attempts: {e}"
                    )

        raise last_exception

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure generation is stopped."""
        if self._is_running:
            self.stop_generation()
