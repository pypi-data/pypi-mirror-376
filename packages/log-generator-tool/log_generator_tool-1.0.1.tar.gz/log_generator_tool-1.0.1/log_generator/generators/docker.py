"""
Docker log generators for container logs.

This module implements log generators that produce realistic Docker container logs
including application logs, system logs, and container lifecycle events with
proper metadata and labels.
"""

import json
import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from faker import Faker

from ..core.interfaces import LogGenerator
from ..core.models import LogEntry


class DockerLogGenerator(LogGenerator):
    """
    Generates Docker container logs with realistic patterns.

    Produces logs similar to Docker container output including application logs,
    system messages, and container lifecycle events with proper JSON formatting
    and metadata.
    """

    # Log levels with distribution
    LOG_LEVELS = {
        "info": 0.50,
        "warn": 0.25,
        "error": 0.15,
        "debug": 0.08,
        "fatal": 0.02,
    }

    # Common Docker log sources
    LOG_SOURCES = {"stdout": 0.70, "stderr": 0.30}

    # Common container names and images
    CONTAINER_IMAGES = [
        "nginx:latest",
        "redis:alpine",
        "postgres:13",
        "node:16-alpine",
        "python:3.9-slim",
        "mysql:8.0",
        "ubuntu:20.04",
        "alpine:latest",
        "mongo:4.4",
        "elasticsearch:7.15.0",
    ]

    CONTAINER_NAMES = [
        "web-server",
        "api-backend",
        "database",
        "cache-redis",
        "worker-queue",
        "nginx-proxy",
        "app-frontend",
        "monitoring",
        "logging-agent",
        "load-balancer",
    ]

    # Common application log patterns
    APP_LOG_PATTERNS = [
        "Starting application server on port {port}",
        "Database connection established to {host}:{port}",
        "Processing request {request_id} from {ip}",
        "User {user} authenticated successfully",
        "Cache miss for key: {key}",
        "Background job {job_id} completed in {duration}ms",
        "Health check passed for service {service}",
        "Configuration loaded from {config_file}",
        "Metrics exported to {endpoint}",
        "Connection pool size: {pool_size}",
    ]

    # Error patterns
    ERROR_PATTERNS = [
        "Connection refused to database at {host}:{port}",
        "Failed to authenticate user {user}: invalid credentials",
        "Timeout waiting for response from {service}",
        "Out of memory: cannot allocate {size} bytes",
        "Permission denied accessing file {file}",
        "Invalid configuration in {config_file}: {error}",
        "Network unreachable: {host}",
        "Disk space low: {available} remaining",
        "Rate limit exceeded for {endpoint}",
        "SSL certificate expired for {domain}",
    ]

    def __init__(
        self, format_type: str = "json", custom_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Docker log generator.

        Args:
            format_type (str): Log format type ("json" or "text")
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.format_type = format_type.lower()
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Container metadata
        self.container_id = self._generate_container_id()
        self.container_name = self._get_container_name()
        self.image_name = self._get_image_name()

        # Override defaults with custom config
        if "log_levels" in self.custom_config:
            self.LOG_LEVELS = self.custom_config["log_levels"]
        if "container_names" in self.custom_config:
            self.CONTAINER_NAMES = self.custom_config["container_names"]
        if "images" in self.custom_config:
            self.CONTAINER_IMAGES = self.custom_config["images"]

    def generate_log(self) -> str:
        """
        Generate a single Docker container log entry.

        Returns:
            str: Formatted Docker log entry
        """
        timestamp = self._generate_timestamp()
        level = self._weighted_choice(self.LOG_LEVELS)
        source = self._weighted_choice(self.LOG_SOURCES)

        # Generate log message based on level
        if level in ["error", "fatal"]:
            message = self._generate_error_message()
        else:
            message = self._generate_app_message()

        if self.format_type == "json":
            # Docker JSON log format
            log_entry = {"log": message + "\\n", "stream": source, "time": timestamp}
            return json.dumps(log_entry, separators=(",", ":"))
        else:
            # Simple text format with metadata
            return f"{timestamp} [{level.upper()}] {self.container_name}: {message}"

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for Docker logs.

        Returns:
            str: Regular expression pattern
        """
        if self.format_type == "json":
            # JSON format pattern
            return r'^{"log":".*","stream":"(stdout|stderr)","time":"[^"]+"}$'
        else:
            # Text format pattern
            return (
                r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) \[(\w+)\] ([^:]+): (.+)$"
            )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches Docker log format.

        Args:
            log_entry (str): Log entry to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pattern = self.get_log_pattern()

        if self.format_type == "json":
            try:
                # Try to parse as JSON first
                parsed = json.loads(log_entry)
                required_fields = ["log", "stream", "time"]
                return all(field in parsed for field in required_fields)
            except json.JSONDecodeError:
                return False
        else:
            return bool(re.match(pattern, log_entry))

    def set_custom_fields(self, fields: Dict[str, Any]) -> None:
        """
        Set custom fields for log generation.

        Args:
            fields (Dict[str, Any]): Custom field definitions
        """
        self.custom_config.update(fields)

        if "log_levels" in fields:
            self.LOG_LEVELS = fields["log_levels"]
        if "container_names" in fields:
            self.CONTAINER_NAMES = fields["container_names"]
        if "images" in fields:
            self.CONTAINER_IMAGES = fields["images"]
        if "container_id" in fields:
            self.container_id = fields["container_id"]
        if "container_name" in fields:
            self.container_name = fields["container_name"]

    def get_container_metadata(self) -> Dict[str, str]:
        """
        Get container metadata.

        Returns:
            Dict containing container metadata
        """
        return {
            "container_id": self.container_id,
            "container_name": self.container_name,
            "image_name": self.image_name,
        }

    def _generate_timestamp(self) -> str:
        """Generate timestamp in Docker format."""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def _generate_container_id(self) -> str:
        """Generate realistic container ID."""
        if "container_id" in self.custom_config:
            return self.custom_config["container_id"]

        # Generate 64-character hex string (like Docker)
        return "".join(random.choices("0123456789abcdef", k=64))

    def _get_container_name(self) -> str:
        """Get container name."""
        if "container_name" in self.custom_config:
            return self.custom_config["container_name"]

        return random.choice(self.CONTAINER_NAMES)

    def _get_image_name(self) -> str:
        """Get image name."""
        if "image_name" in self.custom_config:
            return self.custom_config["image_name"]

        return random.choice(self.CONTAINER_IMAGES)

    def _generate_app_message(self) -> str:
        """Generate application log message."""
        pattern = random.choice(self.APP_LOG_PATTERNS)

        # Fill in placeholders with realistic data
        replacements = {
            "port": str(random.randint(3000, 9000)),
            "host": self.faker.ipv4(),
            "request_id": self.faker.uuid4()[:8],
            "ip": self.faker.ipv4(),
            "user": self.faker.user_name(),
            "key": f"cache:{self.faker.word()}:{random.randint(1, 1000)}",
            "job_id": self.faker.uuid4()[:8],
            "duration": str(random.randint(10, 5000)),
            "service": random.choice(["database", "cache", "api", "auth"]),
            "config_file": f"/app/config/{self.faker.word()}.yml",
            "endpoint": f"http://{self.faker.domain_name()}/metrics",
            "pool_size": str(random.randint(5, 50)),
        }

        for key, value in replacements.items():
            pattern = pattern.replace(f"{{{key}}}", value)

        return pattern

    def _generate_error_message(self) -> str:
        """Generate error log message."""
        pattern = random.choice(self.ERROR_PATTERNS)

        # Fill in placeholders with realistic data
        replacements = {
            "host": self.faker.ipv4(),
            "port": str(random.randint(3000, 9000)),
            "user": self.faker.user_name(),
            "service": random.choice(["database", "cache", "api", "auth"]),
            "size": f"{random.randint(1, 100)}MB",
            "file": f"/app/{self.faker.file_path()}",
            "config_file": f"/app/config/{self.faker.word()}.yml",
            "error": random.choice(
                ["missing required field", "invalid format", "parse error"]
            ),
            "available": f"{random.randint(1, 10)}GB",
            "endpoint": f"/api/{self.faker.word()}",
            "domain": self.faker.domain_name(),
        }

        for key, value in replacements.items():
            pattern = pattern.replace(f"{{{key}}}", value)

        return pattern

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]
