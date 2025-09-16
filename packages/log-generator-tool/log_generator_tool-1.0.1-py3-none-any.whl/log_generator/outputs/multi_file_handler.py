"""
Multi-file output handler that creates separate files for each log type.
"""

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..core.exceptions import OutputError
from ..core.interfaces import OutputHandler
from .file_handler import FileOutputHandler


class MultiFileOutputHandler(OutputHandler):
    """
    Output handler that creates separate files for each log type.

    This handler automatically creates and manages separate log files
    for different log types, organizing them by type and optionally
    by date/time patterns.
    """

    def __init__(
        self,
        base_path: Union[str, Path],
        file_pattern: str = "{log_type}_{date}.log",
        date_format: str = "%Y%m%d",
        rotation_size: Optional[int] = None,
        rotation_time: Optional[int] = None,
        max_files: int = 10,
        buffer_size: int = 8192,
        encoding: str = "utf-8",
    ):
        """
        Initialize multi-file output handler.

        Args:
            base_path: Base directory for log files
            file_pattern: Pattern for generating file names. Available variables:
                         {log_type}, {date}, {time}, {datetime}
            date_format: Format string for date/time in file names
            rotation_size: Maximum file size in bytes before rotation
            rotation_time: Maximum time in seconds before rotation
            max_files: Maximum number of rotated files to keep per log type
            buffer_size: Buffer size for file writing
            encoding: File encoding
        """
        self.base_path = Path(base_path)
        self.file_pattern = file_pattern
        self.date_format = date_format
        self.rotation_size = rotation_size
        self.rotation_time = rotation_time
        self.max_files = max_files
        self.buffer_size = buffer_size
        self.encoding = encoding

        # Dictionary to store file handlers for each log type
        self._handlers: Dict[str, FileOutputHandler] = {}
        self._lock = threading.Lock()

        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Check permissions
        self._check_permissions()

    def _check_permissions(self) -> None:
        """Check if we have write permissions to the base directory."""
        try:
            if not os.access(self.base_path, os.W_OK):
                raise OutputError(f"No write permission to directory: {self.base_path}")
        except Exception as e:
            raise OutputError(f"Permission check failed: {e}")

    def _get_file_path(self, log_type: str) -> Path:
        """
        Generate file path for a specific log type.

        Args:
            log_type: Type of log (e.g., 'nginx_access', 'syslog')

        Returns:
            Path object for the log file
        """
        now = datetime.now()

        # Replace pattern variables
        filename = self.file_pattern.format(
            log_type=log_type,
            date=now.strftime(self.date_format),
            time=now.strftime("%H%M%S"),
            datetime=now.strftime(f"{self.date_format}_%H%M%S"),
        )

        return self.base_path / filename

    def _get_handler(self, log_type: str) -> FileOutputHandler:
        """
        Get or create a file handler for the specified log type.

        Args:
            log_type: Type of log

        Returns:
            FileOutputHandler instance for the log type
        """
        with self._lock:
            if log_type not in self._handlers:
                file_path = self._get_file_path(log_type)

                # Create handler for this log type
                handler = FileOutputHandler(
                    file_path=file_path,
                    rotation_size=self.rotation_size,
                    rotation_time=self.rotation_time,
                    max_files=self.max_files,
                    buffer_size=self.buffer_size,
                    encoding=self.encoding,
                )

                self._handlers[log_type] = handler

            return self._handlers[log_type]

    def write_log(self, log_entry: str, log_type: str = "default") -> None:
        """
        Write a log entry to the appropriate file based on log type.

        Args:
            log_entry: Log entry to write
            log_type: Type of log (determines which file to write to)
        """
        try:
            handler = self._get_handler(log_type)
            handler.write_log(log_entry)
        except Exception as e:
            raise OutputError(f"Failed to write log entry for type {log_type}: {e}")

    def flush(self) -> None:
        """Flush all file handlers."""
        with self._lock:
            for handler in self._handlers.values():
                try:
                    handler.flush()
                except Exception as e:
                    # Log error but continue flushing other handlers
                    print(f"Warning: Failed to flush handler: {e}")

    def close(self) -> None:
        """Close all file handlers and clean up resources."""
        with self._lock:
            for log_type, handler in self._handlers.items():
                try:
                    handler.close()
                except Exception as e:
                    print(f"Warning: Failed to close handler for {log_type}: {e}")

            self._handlers.clear()

    def get_active_log_types(self) -> list:
        """
        Get list of currently active log types.

        Returns:
            List of log type names that have active handlers
        """
        with self._lock:
            return list(self._handlers.keys())

    def get_file_path_for_type(self, log_type: str) -> Path:
        """
        Get the current file path for a specific log type.

        Args:
            log_type: Type of log

        Returns:
            Path to the log file for this type
        """
        if log_type in self._handlers:
            return self._handlers[log_type].get_file_path()
        else:
            return self._get_file_path(log_type)

    def get_file_size_for_type(self, log_type: str) -> int:
        """
        Get current file size for a specific log type.

        Args:
            log_type: Type of log

        Returns:
            Current file size in bytes, or 0 if handler doesn't exist
        """
        if log_type in self._handlers:
            return self._handlers[log_type].get_current_size()
        return 0

    def force_rotation_for_type(self, log_type: str) -> None:
        """
        Force log rotation for a specific log type.

        Args:
            log_type: Type of log to rotate
        """
        if log_type in self._handlers:
            self._handlers[log_type].force_rotation()

    def force_rotation_all(self) -> None:
        """Force log rotation for all active log types."""
        with self._lock:
            for handler in self._handlers.values():
                try:
                    handler.force_rotation()
                except Exception as e:
                    print(f"Warning: Failed to rotate handler: {e}")

    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all log types.

        Returns:
            Dictionary with statistics for each log type
        """
        stats = {}
        with self._lock:
            for log_type, handler in self._handlers.items():
                file_path = handler.get_file_path()
                stats[log_type] = {
                    "file_path": str(file_path),
                    "file_size": handler.get_current_size(),
                    "line_count": self._get_line_count(file_path),
                    "recent_logs": self._get_recent_logs(file_path),
                    "active": True,
                }
        return stats

    def _get_line_count(self, file_path: Path) -> int:
        """
        Get the number of lines in a file.

        Args:
            file_path: Path to the file

        Returns:
            Number of lines in the file
        """
        try:
            if file_path.exists():
                with open(file_path, "r", encoding=self.encoding) as f:
                    return sum(1 for _ in f)
        except Exception:
            pass
        return 0

    def _get_recent_logs(self, file_path: Path, num_lines: int = 3) -> list:
        """
        Get the most recent log entries from a file.

        Args:
            file_path: Path to the file
            num_lines: Number of recent lines to retrieve

        Returns:
            List of recent log entries
        """
        try:
            if file_path.exists() and file_path.stat().st_size > 0:
                with open(file_path, "r", encoding=self.encoding) as f:
                    lines = f.readlines()
                    # Return last num_lines, stripped of whitespace
                    return [line.strip() for line in lines[-num_lines:] if line.strip()]
        except Exception:
            pass
        return []
