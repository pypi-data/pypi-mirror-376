"""
Console output handler with color support.
"""

import io
import sys
import threading
from datetime import datetime
from typing import Dict, Optional

from ..core.exceptions import OutputError
from ..core.interfaces import OutputHandler


class ConsoleOutputHandler(OutputHandler):
    """
    Console output handler with colored output support.

    Provides real-time log output to console with optional color coding
    based on log levels and types.
    """

    # ANSI color codes
    COLORS = {
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
        "DIM": "\033[2m",
        "RED": "\033[31m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "BLUE": "\033[34m",
        "MAGENTA": "\033[35m",
        "CYAN": "\033[36m",
        "WHITE": "\033[37m",
        "BRIGHT_RED": "\033[91m",
        "BRIGHT_GREEN": "\033[92m",
        "BRIGHT_YELLOW": "\033[93m",
        "BRIGHT_BLUE": "\033[94m",
        "BRIGHT_MAGENTA": "\033[95m",
        "BRIGHT_CYAN": "\033[96m",
        "BRIGHT_WHITE": "\033[97m",
    }

    # Default color mapping for log levels
    LEVEL_COLORS = {
        "DEBUG": "CYAN",
        "INFO": "GREEN",
        "WARNING": "YELLOW",
        "WARN": "YELLOW",
        "ERROR": "RED",
        "CRITICAL": "BRIGHT_RED",
        "CRIT": "BRIGHT_RED",
    }

    # Default color mapping for log types
    TYPE_COLORS = {
        "nginx": "BLUE",
        "apache": "MAGENTA",
        "syslog": "CYAN",
        "fastapi": "GREEN",
        "django": "BRIGHT_GREEN",
        "docker": "BRIGHT_BLUE",
        "kubernetes": "BRIGHT_MAGENTA",
    }

    def __init__(
        self,
        colored: bool = True,
        output_stream=None,
        timestamp_format: str = "%Y-%m-%d %H:%M:%S",
        show_timestamp: bool = True,
        show_log_type: bool = True,
        custom_colors: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize console output handler.

        Args:
            colored: Enable colored output
            output_stream: Output stream (default: sys.stdout)
            timestamp_format: Format for timestamps
            show_timestamp: Whether to show timestamps
            show_log_type: Whether to show log type
            custom_colors: Custom color mappings
        """
        self.colored = colored and self._supports_color()
        self.output_stream = output_stream or sys.stdout
        self.timestamp_format = timestamp_format
        self.show_timestamp = show_timestamp
        self.show_log_type = show_log_type

        self._lock = threading.Lock()
        self._closed = False

        # Merge custom colors with defaults
        if custom_colors:
            self.level_colors = {**self.LEVEL_COLORS, **custom_colors.get("levels", {})}
            self.type_colors = {**self.TYPE_COLORS, **custom_colors.get("types", {})}
        else:
            self.level_colors = self.LEVEL_COLORS.copy()
            self.type_colors = self.TYPE_COLORS.copy()

    def _supports_color(self) -> bool:
        """
        Check if the terminal supports color output.

        Returns:
            bool: True if colors are supported
        """
        # Use the output_stream parameter or default to stdout
        stream = getattr(self, "output_stream", sys.stdout)

        # Check if output is a TTY
        if not hasattr(stream, "isatty") or not stream.isatty():
            return False

        # Check environment variables
        import os

        term = os.environ.get("TERM", "")
        if term in ("dumb", ""):
            return False

        # Check for color support
        if "color" in term or term in ("xterm", "xterm-256color", "screen"):
            return True

        return True

    def _get_color_code(self, color_name: str) -> str:
        """
        Get ANSI color code for color name.

        Args:
            color_name: Name of the color

        Returns:
            str: ANSI color code or empty string if colors disabled
        """
        if not self.colored:
            return ""

        return self.COLORS.get(color_name.upper(), "")

    def _colorize_text(self, text: str, color: str) -> str:
        """
        Apply color to text.

        Args:
            text: Text to colorize
            color: Color name

        Returns:
            str: Colorized text
        """
        if not self.colored:
            return text

        color_code = self._get_color_code(color)
        reset_code = self._get_color_code("RESET")

        return f"{color_code}{text}{reset_code}"

    def _extract_log_info(self, log_entry: str) -> Dict[str, str]:
        """
        Extract log level and type from log entry.

        Args:
            log_entry: Raw log entry

        Returns:
            Dict containing extracted info
        """
        info = {"level": "", "type": "", "message": log_entry}

        # Try to extract log level (look for [LEVEL] pattern)
        import re

        level_match = re.search(r"\[(\w+)\]", log_entry)
        if level_match:
            info["level"] = level_match.group(1).upper()

        # Try to extract log type from common patterns
        if "nginx" in log_entry.lower():
            info["type"] = "nginx"
        elif "apache" in log_entry.lower():
            info["type"] = "apache"
        elif "syslog" in log_entry.lower():
            info["type"] = "syslog"
        elif "fastapi" in log_entry.lower():
            info["type"] = "fastapi"
        elif "django" in log_entry.lower():
            info["type"] = "django"
        elif "docker" in log_entry.lower():
            info["type"] = "docker"
        elif "kubernetes" in log_entry.lower() or "k8s" in log_entry.lower():
            info["type"] = "kubernetes"

        return info

    def _format_log_entry(self, log_entry: str) -> str:
        """
        Format log entry with colors and additional info.

        Args:
            log_entry: Raw log entry

        Returns:
            str: Formatted log entry
        """
        # Extract log information
        log_info = self._extract_log_info(log_entry)

        parts = []

        # Add timestamp if enabled
        if self.show_timestamp:
            timestamp = datetime.now().strftime(self.timestamp_format)
            timestamp_colored = self._colorize_text(timestamp, "DIM")
            parts.append(f"[{timestamp_colored}]")

        # Add log type if enabled and detected
        if self.show_log_type and log_info["type"]:
            type_color = self.type_colors.get(log_info["type"], "WHITE")
            type_colored = self._colorize_text(log_info["type"].upper(), type_color)
            parts.append(f"[{type_colored}]")

        # Colorize the main log entry based on level
        if log_info["level"] and log_info["level"] in self.level_colors:
            level_color = self.level_colors[log_info["level"]]
            log_entry = self._colorize_text(log_entry, level_color)

        # Combine all parts
        if parts:
            return f"{' '.join(parts)} {log_entry}"
        else:
            return log_entry

    def write_log(self, log_entry: str) -> None:
        """
        Write a log entry to console.

        Args:
            log_entry: Log entry to write
        """
        if self._closed:
            raise OutputError("Console handler is closed")

        with self._lock:
            try:
                # Format the log entry
                formatted_entry = self._format_log_entry(log_entry)

                # Ensure entry ends with newline
                if not formatted_entry.endswith("\n"):
                    formatted_entry += "\n"

                # Write to output stream
                self.output_stream.write(formatted_entry)
                self.output_stream.flush()

            except Exception as e:
                raise OutputError(f"Failed to write to console: {e}")

    def flush(self) -> None:
        """Flush the output stream."""
        with self._lock:
            if not self._closed:
                try:
                    self.output_stream.flush()
                except Exception as e:
                    raise OutputError(f"Failed to flush console output: {e}")

    def close(self) -> None:
        """Close the console handler."""
        with self._lock:
            self._closed = True
            # Don't close stdout/stderr as they might be used by other parts
            # Also don't close StringIO objects used in tests
            if self.output_stream not in (sys.stdout, sys.stderr) and not isinstance(
                self.output_stream, (io.StringIO, io.BytesIO)
            ):
                try:
                    self.output_stream.close()
                except Exception:
                    pass  # Ignore errors when closing

    def set_colors_enabled(self, enabled: bool) -> None:
        """
        Enable or disable colored output.

        Args:
            enabled: Whether to enable colors
        """
        self.colored = enabled and self._supports_color()

    def add_level_color(self, level: str, color: str) -> None:
        """
        Add or update color mapping for a log level.

        Args:
            level: Log level name
            color: Color name
        """
        self.level_colors[level.upper()] = color.upper()

    def add_type_color(self, log_type: str, color: str) -> None:
        """
        Add or update color mapping for a log type.

        Args:
            log_type: Log type name
            color: Color name
        """
        self.type_colors[log_type.lower()] = color.upper()

    def is_closed(self) -> bool:
        """
        Check if handler is closed.

        Returns:
            bool: True if closed
        """
        return self._closed
