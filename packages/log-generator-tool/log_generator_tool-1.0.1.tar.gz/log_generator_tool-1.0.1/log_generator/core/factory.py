"""
Factory pattern implementation for log generators.

This module provides the LogFactory class that implements the factory pattern
for creating and managing log generator instances dynamically.
"""

import importlib
import inspect
import logging
from typing import Any, Dict, List, Optional, Type

from .exceptions import ConfigurationError, FactoryError
from .interfaces import LogFactory as LogFactoryInterface
from .interfaces import LogGenerator


class LogFactory(LogFactoryInterface):
    """
    Factory class for creating and managing log generator instances.

    This class implements the factory pattern to provide dynamic creation
    of log generators, plugin-style registration system, and lifecycle
    management of generator instances.
    """

    def __init__(self):
        """Initialize the log factory."""
        self._generators: Dict[str, Type[LogGenerator]] = {}
        self._instances: Dict[str, LogGenerator] = {}
        self._logger = logging.getLogger(__name__)

        # Register built-in generators
        self._register_builtin_generators()

    def create_generator(self, log_type: str, config: Dict[str, Any]) -> LogGenerator:
        """
        Create a log generator instance for the specified type.

        Args:
            log_type: Type of log generator to create
            config: Configuration for the generator

        Returns:
            Instance of the requested log generator

        Raises:
            FactoryError: If generator type is not registered or creation fails
        """
        if log_type not in self._generators:
            raise FactoryError(
                f"Unknown log generator type: {log_type}. "
                f"Available types: {', '.join(self.get_available_types())}",
                error_code="UNKNOWN_GENERATOR_TYPE",
            )

        generator_class = self._generators[log_type]

        try:
            # Check if generator class accepts config in constructor
            sig = inspect.signature(generator_class.__init__)
            if "config" in sig.parameters:
                instance = generator_class(config=config)
            else:
                instance = generator_class()
                # Try to set config if the instance has a method for it
                if hasattr(instance, "set_config"):
                    instance.set_config(config)

            # Set custom fields if provided in config
            custom_fields = config.get("custom_fields", {})
            if custom_fields and hasattr(instance, "set_custom_fields"):
                instance.set_custom_fields(custom_fields)

            # Store instance for lifecycle management
            instance_key = f"{log_type}_{id(instance)}"
            self._instances[instance_key] = instance

            self._logger.info(f"Created generator instance for type: {log_type}")
            return instance

        except Exception as e:
            self._logger.error(f"Failed to create generator for type {log_type}: {e}")
            raise FactoryError(
                f"Failed to create generator for type {log_type}: {e}",
                error_code="GENERATOR_CREATION_FAILED",
            )

    def register_generator(
        self, log_type: str, generator_class: Type[LogGenerator]
    ) -> None:
        """
        Register a new log generator type.

        Args:
            log_type: Identifier for the log type
            generator_class: Class that implements LogGenerator interface

        Raises:
            FactoryError: If generator class is invalid
        """
        # Validate that the class implements LogGenerator interface
        if not issubclass(generator_class, LogGenerator):
            raise FactoryError(
                f"Generator class {generator_class.__name__} must implement LogGenerator interface",
                error_code="INVALID_GENERATOR_CLASS",
            )

        # Check if required methods are implemented
        required_methods = ["generate_log", "get_log_pattern", "validate_log"]
        for method_name in required_methods:
            if not hasattr(generator_class, method_name):
                raise FactoryError(
                    f"Generator class {generator_class.__name__} missing required method: {method_name}",
                    error_code="MISSING_REQUIRED_METHOD",
                )

        # Register the generator
        self._generators[log_type] = generator_class
        self._logger.info(f"Registered generator for type: {log_type}")

    def unregister_generator(self, log_type: str) -> None:
        """
        Unregister a log generator type.

        Args:
            log_type: Identifier for the log type to unregister
        """
        if log_type in self._generators:
            del self._generators[log_type]
            self._logger.info(f"Unregistered generator for type: {log_type}")
        else:
            self._logger.warning(
                f"Attempted to unregister unknown generator type: {log_type}"
            )

    def get_available_types(self) -> List[str]:
        """
        Get list of available log generator types.

        Returns:
            List of registered log type identifiers
        """
        return list(self._generators.keys())

    def is_type_registered(self, log_type: str) -> bool:
        """
        Check if a log type is registered.

        Args:
            log_type: Log type identifier to check

        Returns:
            True if type is registered, False otherwise
        """
        return log_type in self._generators

    def get_generator_class(self, log_type: str) -> Optional[Type[LogGenerator]]:
        """
        Get the generator class for a specific log type.

        Args:
            log_type: Log type identifier

        Returns:
            Generator class or None if not registered
        """
        return self._generators.get(log_type)

    def register_from_module(
        self, module_path: str, log_type: str | None = None
    ) -> None:
        """
        Register generator(s) from a Python module.

        This method supports plugin-style loading of generators from external modules.

        Args:
            module_path: Python module path (e.g., 'my_package.generators.custom')
            log_type: Optional log type name. If not provided, will try to auto-detect

        Raises:
            FactoryError: If module cannot be loaded or generator not found
        """
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise FactoryError(
                f"Failed to import module {module_path}: {e}",
                error_code="MODULE_IMPORT_FAILED",
            )

        # If log_type is specified, look for a specific class
        if log_type:
            generator_class = self._find_generator_in_module(module, log_type)
            if generator_class:
                self.register_generator(log_type, generator_class)
            else:
                raise FactoryError(
                    f"No suitable generator class found in module {module_path}",
                    error_code="GENERATOR_NOT_FOUND",
                )
        else:
            # Auto-discover generators in the module
            discovered = self._discover_generators_in_module(module)
            if not discovered:
                raise FactoryError(
                    f"No generator classes found in module {module_path}",
                    error_code="NO_GENERATORS_FOUND",
                )

            for name, cls in discovered.items():
                self.register_generator(name, cls)

    def cleanup_instances(self) -> None:
        """
        Clean up all managed generator instances.

        This method should be called when shutting down to properly
        clean up resources used by generator instances.
        """
        for instance_key, instance in self._instances.items():
            try:
                # Call cleanup method if available
                if hasattr(instance, "cleanup"):
                    instance.cleanup()
            except Exception as e:
                self._logger.error(
                    f"Error cleaning up generator instance {instance_key}: {e}"
                )

        self._instances.clear()
        self._logger.info("Cleaned up all generator instances")

    def get_instance_count(self) -> int:
        """
        Get the number of active generator instances.

        Returns:
            Number of active instances
        """
        return len(self._instances)

    def _register_builtin_generators(self) -> None:
        """
        Register built-in log generators.

        This method automatically registers the standard generators
        that come with the system.
        """
        builtin_generators = {
            "nginx_access": "log_generator.generators.nginx.NginxAccessLogGenerator",
            "nginx_error": "log_generator.generators.nginx.NginxErrorLogGenerator",
            "apache_access": "log_generator.generators.apache.ApacheAccessLogGenerator",
            "apache_error": "log_generator.generators.apache.ApacheErrorLogGenerator",
            "django_request": "log_generator.generators.django.DjangoRequestLogGenerator",
            "django_sql": "log_generator.generators.django.DjangoSQLLogGenerator",
            "docker": "log_generator.generators.docker.DockerLogGenerator",
            "kubernetes_pod": "log_generator.generators.kubernetes.KubernetesPodLogGenerator",
            "kubernetes_event": "log_generator.generators.kubernetes.KubernetesEventLogGenerator",
            "mysql_query": "log_generator.generators.mysql.MySQLQueryLogGenerator",
            "mysql_error": "log_generator.generators.mysql.MySQLErrorLogGenerator",
            "mysql_slow": "log_generator.generators.mysql.MySQLSlowQueryLogGenerator",
            "postgresql": "log_generator.generators.postgresql.PostgreSQLLogGenerator",
            "postgresql_slow": "log_generator.generators.postgresql.PostgreSQLSlowQueryLogGenerator",
            "syslog": "log_generator.generators.syslog.SyslogGenerator",
            "fastapi": "log_generator.generators.fastapi.FastAPILogGenerator",
        }

        for log_type, class_path in builtin_generators.items():
            try:
                module_path, class_name = class_path.rsplit(".", 1)
                module = importlib.import_module(module_path)
                generator_class = getattr(module, class_name)
                self.register_generator(log_type, generator_class)
            except (ImportError, AttributeError) as e:
                self._logger.warning(
                    f"Failed to register builtin generator {log_type}: {e}"
                )

    def _find_generator_in_module(
        self, module, log_type: str
    ) -> Optional[Type[LogGenerator]]:
        """
        Find a specific generator class in a module.

        Args:
            module: Python module object
            log_type: Log type to look for

        Returns:
            Generator class if found, None otherwise
        """
        # Try common naming patterns
        possible_names = [
            f"{log_type.title()}Generator",
            f"{log_type.title()}LogGenerator",
            f"{log_type.upper()}Generator",
            f"{log_type.capitalize()}Generator",
        ]

        for name in possible_names:
            if hasattr(module, name):
                cls = getattr(module, name)
                if inspect.isclass(cls) and issubclass(cls, LogGenerator):
                    return cls

        # Fallback: search all classes in module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, LogGenerator) and obj != LogGenerator:
                return obj

        return None

    def _discover_generators_in_module(self, module) -> Dict[str, Type[LogGenerator]]:
        """
        Discover all generator classes in a module.

        Args:
            module: Python module object

        Returns:
            Dictionary mapping generator names to classes
        """
        generators = {}

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, LogGenerator) and obj != LogGenerator:
                # Try to derive log type from class name
                log_type = self._derive_log_type_from_class_name(name)
                generators[log_type] = obj

        return generators

    def _derive_log_type_from_class_name(self, class_name: str) -> str:
        """
        Derive log type identifier from class name.

        Args:
            class_name: Name of the generator class

        Returns:
            Derived log type identifier
        """
        # Remove common suffixes in order of preference
        name = class_name
        if name.endswith("LogGenerator"):
            name = name[: -len("LogGenerator")]
        elif name.endswith("Generator"):
            name = name[: -len("Generator")]

        # Convert to snake_case
        import re

        name = re.sub("([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        name = re.sub("([a-z\\d])([A-Z])", r"\1_\2", name)

        return name.lower()

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup_instances()
        except Exception:
            pass  # Ignore errors during destruction
