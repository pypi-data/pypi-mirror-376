"""
JSON structured output handler.
"""

import json
import re
import threading
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from ..core.exceptions import OutputError
from ..core.interfaces import OutputHandler
from ..core.models import LogEntry


class JSONOutputHandler(OutputHandler):
    """
    JSON structured output handler.

    Converts log entries to structured JSON format with field mapping
    and validation support.
    """

    def __init__(
        self,
        output_handler: OutputHandler | str,
        field_mapping: Optional[Dict[str, str]] = None,
        include_raw_message: bool = True,
        pretty_print: bool = False,
        ensure_ascii: bool = False,
        custom_serializer: Optional[Callable] = None,
    ):
        """
        Initialize JSON output handler.

        Args:
            output_handler: Underlying output handler (file, console, network) or file path
            field_mapping: Custom field name mappings
            include_raw_message: Whether to include original raw message
            pretty_print: Whether to format JSON with indentation
            ensure_ascii: Whether to escape non-ASCII characters
            custom_serializer: Custom JSON serializer function
        """
        # If output_handler is a string, create a FileOutputHandler
        if isinstance(output_handler, str):
            from .file_handler import FileOutputHandler

            output_handler = FileOutputHandler(output_handler)

        self.output_handler = output_handler
        self.field_mapping = field_mapping or {}
        self.include_raw_message = include_raw_message
        self.pretty_print = pretty_print
        self.ensure_ascii = ensure_ascii
        self.custom_serializer = custom_serializer

        self._lock = threading.Lock()
        self._closed = False

        # Default field mappings
        self.default_mapping = {
            "timestamp": "@timestamp",
            "log_type": "type",
            "level": "level",
            "message": "message",
            "source_ip": "source.ip",
            "user_agent": "user_agent",
            "status_code": "http.response.status_code",
            "response_time": "http.response.time",
        }

        # Merge with custom mappings
        self.field_mapping = {**self.default_mapping, **self.field_mapping}

    def _parse_log_entry(self, log_entry: str) -> Dict[str, Any]:
        """
        Parse a raw log entry into structured data.

        Args:
            log_entry: Raw log entry string

        Returns:
            Dict containing parsed log data
        """
        # If it's already a LogEntry object, convert it
        if isinstance(log_entry, LogEntry):
            return self._logentry_to_dict(log_entry)

        # Try to parse common log formats
        parsed_data: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "message": log_entry.strip(),
            "level": "INFO",
            "log_type": "unknown",
        }

        # Extract timestamp (ISO format)
        timestamp_match = re.search(
            r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)",
            log_entry,
        )
        if timestamp_match:
            parsed_data["timestamp"] = timestamp_match.group(1)

        # Extract log level
        level_match = re.search(r"\[(\w+)\]", log_entry)
        if level_match:
            parsed_data["level"] = level_match.group(1).upper()

        # Extract IP address
        ip_match = re.search(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", log_entry)
        if ip_match:
            parsed_data["source_ip"] = ip_match.group(1)

        # Extract HTTP status code (look for 3-digit codes in quotes or after HTTP method)
        status_match = re.search(r'"[A-Z]+ [^"]*" ([1-5]\d{2})', log_entry)
        if not status_match:
            status_match = re.search(
                r"\b([1-5]\d{2})\s+\d+\s*$", log_entry
            )  # Status followed by size at end
        if status_match:
            parsed_data["status_code"] = int(status_match.group(1))

        # Extract response time
        time_match = re.search(r"(\d+(?:\.\d+)?)\s*ms", log_entry)
        if time_match:
            parsed_data["response_time"] = (
                float(time_match.group(1)) / 1000
            )  # Convert to seconds
        else:
            time_match = re.search(r"(\d+(?:\.\d+)?)\s*s", log_entry)
            if time_match:
                parsed_data["response_time"] = float(time_match.group(1))

        # Extract user agent (quoted strings)
        ua_match = re.search(r'"([^"]*Mozilla[^"]*)"', log_entry)
        if ua_match:
            parsed_data["user_agent"] = ua_match.group(1)

        # Detect log type based on content
        log_entry_lower = log_entry.lower()
        if "nginx" in log_entry_lower:
            parsed_data["log_type"] = "nginx"
        elif "apache" in log_entry_lower:
            parsed_data["log_type"] = "apache"
        elif "syslog" in log_entry_lower or "kernel" in log_entry_lower:
            parsed_data["log_type"] = "syslog"
        elif "fastapi" in log_entry_lower:
            parsed_data["log_type"] = "fastapi"
        elif "django" in log_entry_lower:
            parsed_data["log_type"] = "django"
        elif "docker" in log_entry_lower:
            parsed_data["log_type"] = "docker"
        elif "kubernetes" in log_entry_lower or "k8s" in log_entry_lower:
            parsed_data["log_type"] = "kubernetes"

        return parsed_data

    def _logentry_to_dict(self, log_entry: LogEntry) -> Dict[str, Any]:
        """
        Convert LogEntry object to dictionary.

        Args:
            log_entry: LogEntry object

        Returns:
            Dict representation of log entry
        """
        return {
            "timestamp": log_entry.timestamp.isoformat(),
            "log_type": log_entry.log_type,
            "level": log_entry.level,
            "message": log_entry.message,
            "source_ip": log_entry.source_ip,
            "user_agent": log_entry.user_agent,
            "status_code": log_entry.status_code,
            "response_time": log_entry.response_time,
            **log_entry.custom_fields,
        }

    def _apply_field_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply field name mappings to the data.

        Args:
            data: Original data dictionary

        Returns:
            Dict with mapped field names
        """
        mapped_data: Dict[str, Any] = {}

        for original_field, value in data.items():
            if value is None:
                continue

            # Get mapped field name or use original
            mapped_field = self.field_mapping.get(original_field, original_field)

            # Handle nested field names (e.g., "source.ip")
            if "." in mapped_field:
                parts = mapped_field.split(".")
                current = mapped_data

                # Create nested structure
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                current[parts[-1]] = value
            else:
                mapped_data[mapped_field] = value

        return mapped_data

    def _serialize_to_json(
        self, data: Dict[str, Any], raw_message: str | None = None
    ) -> str:
        """
        Serialize data to JSON string.

        Args:
            data: Data to serialize
            raw_message: Original raw message

        Returns:
            JSON string
        """
        # Add raw message if requested
        if self.include_raw_message and raw_message:
            data["raw_message"] = raw_message

        # Add metadata
        data["@version"] = "1"
        # Also include timestamp field for compatibility
        if "@timestamp" in data and "timestamp" not in data:
            data["timestamp"] = data["@timestamp"]
        elif "timestamp" in data and "@timestamp" not in data:
            data["@timestamp"] = data["timestamp"]

        try:
            if self.custom_serializer:
                return self.custom_serializer(data)

            return json.dumps(
                data,
                ensure_ascii=self.ensure_ascii,
                indent=2 if self.pretty_print else None,
                separators=(",", ": ") if self.pretty_print else (",", ":"),
                default=self._json_serializer,
            )
        except Exception as e:
            raise OutputError(f"JSON serialization failed: {e}")

    def _json_serializer(self, obj: Any) -> Any:
        """
        Custom JSON serializer for non-standard types.

        Args:
            obj: Object to serialize

        Returns:
            Serializable representation
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return str(obj)

    def write_log(self, log_entry: str | LogEntry) -> None:
        """
        Write a log entry as JSON.

        Args:
            log_entry: Log entry to write (string or LogEntry object)
        """
        if self._closed:
            raise OutputError("JSON handler is closed")

        with self._lock:
            try:
                # Parse the log entry
                if isinstance(log_entry, LogEntry):
                    parsed_data = self._logentry_to_dict(log_entry)
                    raw_message = log_entry.to_string()
                else:
                    parsed_data = self._parse_log_entry(log_entry)
                    raw_message = log_entry

                # Apply field mappings
                mapped_data = self._apply_field_mapping(parsed_data)

                # Serialize to JSON
                json_output = self._serialize_to_json(mapped_data, raw_message)

                # Write through underlying handler
                # Check if output_handler is a string (incorrect usage) and handle it
                if isinstance(self.output_handler, str):
                    raise OutputError(
                        "Output handler is a string, expected an OutputHandler object"
                    )

                self.output_handler.write_log(json_output)

            except Exception as e:
                raise OutputError(f"Failed to write JSON log entry: {e}")

    def flush(self) -> None:
        """Flush the underlying output handler."""
        if not self._closed:
            self.output_handler.flush()

    def close(self) -> None:
        """Close the JSON handler and underlying output handler."""
        with self._lock:
            if not self._closed:
                self._closed = True
                self.output_handler.close()

    def validate_json_format(self, json_string: str) -> bool:
        """
        Validate JSON format.

        Args:
            json_string: JSON string to validate

        Returns:
            bool: True if valid JSON
        """
        try:
            json.loads(json_string)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    def set_field_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Update field mappings.

        Args:
            mapping: New field mappings to add/update
        """
        self.field_mapping.update(mapping)

    def get_field_mapping(self) -> Dict[str, str]:
        """
        Get current field mappings.

        Returns:
            Dict of current field mappings
        """
        return self.field_mapping.copy()

    def is_closed(self) -> bool:
        """
        Check if handler is closed.

        Returns:
            bool: True if closed
        """
        return self._closed


class ELKJSONOutputHandler(JSONOutputHandler):
    """
    JSON output handler optimized for ELK Stack (Elasticsearch, Logstash, Kibana).

    Uses ELK-compatible field mappings and format.
    """

    def __init__(self, output_handler: OutputHandler, **kwargs):
        # ELK-specific field mappings
        elk_mapping = {
            "timestamp": "@timestamp",
            "log_type": "type",
            "level": "level",
            "message": "message",
            "source_ip": "source.ip",
            "user_agent": "user_agent",
            "status_code": "http.response.status_code",
            "response_time": "http.response.time_ms",
        }

        kwargs["field_mapping"] = {**elk_mapping, **kwargs.get("field_mapping", {})}
        kwargs["include_raw_message"] = kwargs.get("include_raw_message", True)

        super().__init__(output_handler, **kwargs)


class SplunkJSONOutputHandler(JSONOutputHandler):
    """
    JSON output handler optimized for Splunk.

    Uses Splunk-compatible field mappings and format.
    """

    def __init__(self, output_handler: OutputHandler, **kwargs):
        # Splunk-specific field mappings
        splunk_mapping = {
            "timestamp": "_time",
            "log_type": "sourcetype",
            "level": "log_level",
            "message": "_raw",
            "source_ip": "src_ip",
            "user_agent": "http_user_agent",
            "status_code": "status",
            "response_time": "response_time",
        }

        kwargs["field_mapping"] = {**splunk_mapping, **kwargs.get("field_mapping", {})}
        kwargs["include_raw_message"] = kwargs.get("include_raw_message", False)

        super().__init__(output_handler, **kwargs)
