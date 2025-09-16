"""
File output handler with rotation support.
"""

import os
import shutil
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union

from ..core.exceptions import OutputError
from ..core.interfaces import OutputHandler


class FileOutputHandler(OutputHandler):
    """
    File output handler with log rotation support.

    Supports both size-based and time-based log rotation with
    file permission and disk space checking.
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        rotation_size: Optional[int] = None,  # bytes
        rotation_time: Optional[int] = None,  # seconds
        max_files: int = 10,
        buffer_size: int = 8192,
        encoding: str = "utf-8",
    ):
        """
        Initialize file output handler.

        Args:
            file_path: Path to the log file
            rotation_size: Maximum file size in bytes before rotation
            rotation_time: Maximum time in seconds before rotation
            max_files: Maximum number of rotated files to keep
            buffer_size: Buffer size for file writing
            encoding: File encoding
        """
        self.file_path = Path(file_path)
        self.rotation_size = rotation_size
        self.rotation_time = rotation_time
        self.max_files = max_files
        self.buffer_size = buffer_size
        self.encoding = encoding

        self._file_handle = None
        self._lock = threading.Lock()
        self._creation_time = None
        self._bytes_written = 0

        # Create directory if it doesn't exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check permissions and disk space
        self._check_permissions()
        self._check_disk_space()

        # Open initial file
        self._open_file()

    def _check_permissions(self) -> None:
        """Check if we have write permissions to the target directory."""
        try:
            # Check if directory is writable
            if not os.access(self.file_path.parent, os.W_OK):
                raise OutputError(
                    f"No write permission to directory: {self.file_path.parent}"
                )

            # If file exists, check if it's writable
            if self.file_path.exists() and not os.access(self.file_path, os.W_OK):
                raise OutputError(f"No write permission to file: {self.file_path}")

        except Exception as e:
            raise OutputError(f"Permission check failed: {e}")

    def _check_disk_space(self, min_space_mb: int = 100) -> None:
        """
        Check available disk space.

        Args:
            min_space_mb: Minimum required space in MB
        """
        try:
            stat = shutil.disk_usage(self.file_path.parent)
            available_mb = stat.free / (1024 * 1024)

            if available_mb < min_space_mb:
                raise OutputError(
                    f"Insufficient disk space: {available_mb:.1f}MB available, "
                    f"{min_space_mb}MB required"
                )
        except Exception as e:
            raise OutputError(f"Disk space check failed: {e}")

    def _open_file(self) -> None:
        """Open the log file for writing."""
        try:
            self._file_handle = open(
                self.file_path, "a", buffering=self.buffer_size, encoding=self.encoding
            )
            self._creation_time = datetime.now()

            # Get current file size
            if self.file_path.exists():
                self._bytes_written = self.file_path.stat().st_size
            else:
                self._bytes_written = 0

        except Exception as e:
            raise OutputError(f"Failed to open log file {self.file_path}: {e}")

    def _should_rotate(self) -> bool:
        """Check if log rotation is needed."""
        # Size-based rotation
        if self.rotation_size and self._bytes_written >= self.rotation_size:
            return True

        # Time-based rotation
        if (
            self.rotation_time
            and self._creation_time
            and (datetime.now() - self._creation_time).total_seconds()
            >= self.rotation_time
        ):
            return True

        return False

    def _rotate_file(self) -> None:
        """Rotate the current log file."""
        if not self._file_handle:
            return

        try:
            # Close current file
            self._file_handle.close()

            # Generate timestamp for rotated file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_path = self.file_path.with_suffix(
                f".{timestamp}{self.file_path.suffix}"
            )

            # Move current file to rotated name
            if self.file_path.exists():
                self.file_path.rename(rotated_path)

            # Clean up old rotated files
            self._cleanup_old_files()

            # Open new file
            self._open_file()

        except Exception as e:
            raise OutputError(f"Log rotation failed: {e}")

    def _cleanup_old_files(self) -> None:
        """Remove old rotated log files beyond max_files limit."""
        try:
            # Find all rotated files
            pattern = f"{self.file_path.stem}.*{self.file_path.suffix}"
            rotated_files = list(self.file_path.parent.glob(pattern))

            # Sort by modification time (newest first)
            rotated_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove files beyond the limit
            for old_file in rotated_files[self.max_files :]:
                try:
                    old_file.unlink()
                except Exception as e:
                    # Log the error but don't fail the rotation
                    print(f"Warning: Failed to remove old log file {old_file}: {e}")

        except Exception as e:
            # Don't fail rotation for cleanup errors
            print(f"Warning: Log cleanup failed: {e}")

    def write_log(self, log_entry: str, log_type: str | None = None) -> None:
        """
        Write a log entry to the file.

        Args:
            log_entry: Log entry to write
            log_type: Optional log type (for compatibility with multi-file handler)
        """
        with self._lock:
            try:
                # Check if rotation is needed
                if self._should_rotate():
                    self._rotate_file()

                # Check disk space periodically
                if self._bytes_written % (1024 * 1024) == 0:  # Check every MB
                    self._check_disk_space()

                # Write log entry
                if not self._file_handle:
                    raise OutputError("File handle is not available")

                # Ensure log entry ends with newline
                if not log_entry.endswith("\n"):
                    log_entry += "\n"

                self._file_handle.write(log_entry)
                self._bytes_written += len(log_entry.encode(self.encoding))

            except Exception as e:
                raise OutputError(f"Failed to write log entry: {e}")

    def flush(self) -> None:
        """Flush buffered output to disk."""
        with self._lock:
            if self._file_handle:
                try:
                    self._file_handle.flush()
                    os.fsync(self._file_handle.fileno())
                except Exception as e:
                    raise OutputError(f"Failed to flush file: {e}")

    def close(self) -> None:
        """Close the file handler and clean up resources."""
        with self._lock:
            if self._file_handle:
                try:
                    self._file_handle.flush()
                    self._file_handle.close()
                    self._file_handle = None
                except Exception as e:
                    raise OutputError(f"Failed to close file: {e}")

    def get_current_size(self) -> int:
        """
        Get current file size in bytes.

        Returns:
            int: Current file size
        """
        return self._bytes_written

    def get_file_path(self) -> Path:
        """
        Get the current log file path.

        Returns:
            Path: Current log file path
        """
        return self.file_path

    def force_rotation(self) -> None:
        """Force log rotation regardless of size or time limits."""
        with self._lock:
            self._rotate_file()
