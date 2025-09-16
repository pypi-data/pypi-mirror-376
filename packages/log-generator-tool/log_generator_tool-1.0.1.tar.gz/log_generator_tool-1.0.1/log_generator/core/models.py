"""
Data models for the log generator system.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class LogEntry:
    """
    Represents a single log entry with all its metadata.

    This model provides a structured way to handle log data before
    formatting it for output.
    """

    timestamp: datetime
    log_type: str
    level: str
    message: str
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def to_string(self, format_type: str = "default") -> str:
        """
        Convert log entry to formatted string.

        Args:
            format_type (str): Format type for output

        Returns:
            str: Formatted log string
        """
        if format_type == "json":
            return self.to_json()

        # Default format
        base_format = f"{self.timestamp.isoformat()} [{self.level}] {self.message}"

        if self.source_ip:
            base_format = f"{self.source_ip} - {base_format}"

        if self.status_code:
            base_format += f" - Status: {self.status_code}"

        if self.response_time:
            base_format += f" - Time: {self.response_time:.3f}s"

        return base_format

    def to_json(self) -> str:
        """
        Convert log entry to JSON format.

        Returns:
            str: JSON formatted log entry
        """
        data = {
            "timestamp": self.timestamp.isoformat(),
            "log_type": self.log_type,
            "level": self.level,
            "message": self.message,
        }

        if self.source_ip:
            data["source_ip"] = self.source_ip
        if self.user_agent:
            data["user_agent"] = self.user_agent
        if self.status_code:
            data["status_code"] = self.status_code
        if self.response_time:
            data["response_time"] = self.response_time

        # Add custom fields
        data.update(self.custom_fields)

        return json.dumps(data, ensure_ascii=False)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert log entry to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of log entry
        """
        data = {
            "timestamp": self.timestamp,
            "log_type": self.log_type,
            "level": self.level,
            "message": self.message,
            "source_ip": self.source_ip,
            "user_agent": self.user_agent,
            "status_code": self.status_code,
            "response_time": self.response_time,
        }

        # Add custom fields
        data.update(self.custom_fields)

        return data


@dataclass
class GenerationStatistics:
    """
    Statistics for log generation process.
    """

    total_logs_generated: int = 0
    logs_by_type: Dict[str, int] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors_count: int = 0
    generation_rate: float = 0.0  # logs per second

    def add_log(self, log_type: str) -> None:
        """
        Record a generated log.

        Args:
            log_type (str): Type of log that was generated
        """
        self.total_logs_generated += 1
        self.logs_by_type[log_type] = self.logs_by_type.get(log_type, 0) + 1

    def add_error(self) -> None:
        """Record an error during generation."""
        self.errors_count += 1

    def calculate_rate(self) -> float:
        """
        Calculate generation rate in logs per second.

        Returns:
            float: Logs per second
        """
        if not self.start_time or not self.end_time:
            return 0.0

        duration = (self.end_time - self.start_time).total_seconds()
        if duration > 0:
            self.generation_rate = self.total_logs_generated / duration

        return self.generation_rate

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert statistics to dictionary.

        Returns:
            Dict[str, Any]: Statistics as dictionary
        """
        return {
            "total_logs_generated": self.total_logs_generated,
            "logs_by_type": self.logs_by_type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "errors_count": self.errors_count,
            "generation_rate": self.generation_rate,
        }
