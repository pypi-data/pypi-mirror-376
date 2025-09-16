"""
Comprehensive log validation and quality assurance system.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.models import LogEntry
from ..patterns.validator import PatternValidator


@dataclass
class ValidationResult:
    """Result of log validation with detailed information."""

    is_valid: bool
    log_entry: str
    log_type: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    field_completeness: Dict[str, bool] = field(default_factory=dict)
    pattern_matches: Dict[str, bool] = field(default_factory=dict)
    quality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "log_entry": self.log_entry,
            "log_type": self.log_type,
            "errors": self.errors,
            "warnings": self.warnings,
            "field_completeness": self.field_completeness,
            "pattern_matches": self.pattern_matches,
            "quality_score": self.quality_score,
        }


@dataclass
class ValidationStatistics:
    """Statistics for validation process."""

    total_validated: int = 0
    valid_logs: int = 0
    invalid_logs: int = 0
    validation_by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    common_errors: Dict[str, int] = field(default_factory=dict)
    average_quality_score: float = 0.0
    quality_scores: List[float] = field(default_factory=list)

    def add_result(self, result: ValidationResult) -> None:
        """Add validation result to statistics."""
        self.total_validated += 1

        if result.is_valid:
            self.valid_logs += 1
        else:
            self.invalid_logs += 1

        # Track by log type
        if result.log_type not in self.validation_by_type:
            self.validation_by_type[result.log_type] = {"valid": 0, "invalid": 0}

        if result.is_valid:
            self.validation_by_type[result.log_type]["valid"] += 1
        else:
            self.validation_by_type[result.log_type]["invalid"] += 1

        # Track common errors
        for error in result.errors:
            self.common_errors[error] = self.common_errors.get(error, 0) + 1

        # Track quality scores
        self.quality_scores.append(result.quality_score)
        self.average_quality_score = sum(self.quality_scores) / len(self.quality_scores)

    def get_success_rate(self) -> float:
        """Get overall validation success rate."""
        if self.total_validated == 0:
            return 0.0
        return self.valid_logs / self.total_validated

    def get_type_success_rate(self, log_type: str) -> float:
        """Get success rate for specific log type."""
        if log_type not in self.validation_by_type:
            return 0.0

        type_stats = self.validation_by_type[log_type]
        total = type_stats["valid"] + type_stats["invalid"]

        if total == 0:
            return 0.0

        return type_stats["valid"] / total


class LogValidator:
    """
    Comprehensive log validator for format validation, pattern matching,
    and field completeness checking.
    """

    def __init__(self):
        self.pattern_validator = PatternValidator()
        self.statistics = ValidationStatistics()

        # Common log patterns for different types
        self.log_patterns = {
            "nginx_access": {
                "combined": r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d{3}) (\d+|-) "([^"]*)" "([^"]*)"',
                "common": r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d{3}) (\d+|-)',
            },
            "nginx_error": {
                "standard": r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} \[(\w+)\] \d+#\d+: (.+)"
            },
            "apache_access": {
                "combined": r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d{3}) (\d+|-) "([^"]*)" "([^"]*)"',
                "common": r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d{3}) (\d+|-)',
            },
            "syslog": {
                "rfc3164": r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.*)$",
                "rfc5424": r"^<(\d+)>(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)$",
            },
            "fastapi": {
                "uvicorn": r"^\w+ \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - (.+)",
                "access": r'^(\S+) - - \[([^\]]+)\] "([^"]*)" (\d{3})',
            },
            "django": {
                "request": r'^\[(\d{2}/\w{3}/\d{4} \d{2}:\d{2}:\d{2})\] "([^"]*)" (\d{3}) (\d+)',
                "error": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \[(\w+)\] (.+)",
            },
            "docker": {"standard": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z (.+)"},
            "kubernetes": {
                "pod": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+\d+\s+(.+)"
            },
            "mysql": {
                "error": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+\d+\s+\[(\w+)\]\s+(.+)",
                "slow": r"^# Time: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z",
            },
            "postgresql": {
                "log": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \w{3} \[(\d+)\] (\w+): (.+)"
            },
        }

        # Required fields for each log type
        self.required_fields = {
            "nginx_access": ["ip", "timestamp", "request", "status_code"],
            "nginx_error": ["timestamp", "level", "message"],
            "apache_access": ["ip", "timestamp", "request", "status_code"],
            "syslog": ["timestamp", "hostname", "message"],
            "fastapi": ["timestamp", "level", "message"],
            "django": ["timestamp", "request", "status_code"],
            "docker": ["timestamp", "message"],
            "kubernetes": ["timestamp", "message"],
            "mysql": ["timestamp", "level", "message"],
            "postgresql": ["timestamp", "level", "message"],
        }

    def validate_log_entry(
        self, log_entry: str, log_type: str, expected_pattern: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a single log entry comprehensively.

        Args:
            log_entry: Log entry string to validate
            log_type: Type of log (nginx_access, syslog, etc.)
            expected_pattern: Optional specific pattern to match

        Returns:
            ValidationResult with detailed validation information
        """
        result = ValidationResult(is_valid=True, log_entry=log_entry, log_type=log_type)

        # 1. Basic format validation
        self._validate_basic_format(log_entry, result)

        # 2. Pattern matching validation
        self._validate_pattern_matching(log_entry, log_type, expected_pattern, result)

        # 3. Field completeness check
        self._validate_field_completeness(log_entry, log_type, result)

        # 4. Content validation
        self._validate_content(log_entry, log_type, result)

        # 5. Calculate quality score
        result.quality_score = self._calculate_quality_score(result)

        # Update statistics
        self.statistics.add_result(result)

        return result

    def _validate_basic_format(self, log_entry: str, result: ValidationResult) -> None:
        """Validate basic log format requirements."""
        if not log_entry or not log_entry.strip():
            result.errors.append("Empty log entry")
            result.is_valid = False
            return

        # Check for minimum length
        if len(log_entry.strip()) < 10:
            result.warnings.append("Log entry seems too short")

        # Check for maximum reasonable length
        if len(log_entry) > 10000:
            result.warnings.append("Log entry is very long")

        # Check for non-printable characters (except newlines)
        if any(ord(c) < 32 and c not in "\n\r\t" for c in log_entry):
            result.warnings.append("Contains non-printable characters")

    def _validate_pattern_matching(
        self,
        log_entry: str,
        log_type: str,
        expected_pattern: Optional[str],
        result: ValidationResult,
    ) -> None:
        """Validate log entry against known patterns."""
        patterns_to_check = []

        # Add expected pattern if provided
        if expected_pattern:
            patterns_to_check.append(("expected", expected_pattern))

        # Add known patterns for log type
        if log_type in self.log_patterns:
            for pattern_name, pattern in self.log_patterns[log_type].items():
                patterns_to_check.append((pattern_name, pattern))

        matched_any = False

        for pattern_name, pattern in patterns_to_check:
            try:
                match = re.search(pattern, log_entry)
                result.pattern_matches[pattern_name] = match is not None

                if match:
                    matched_any = True

            except re.error as e:
                result.errors.append(f"Invalid regex pattern '{pattern_name}': {e}")
                result.is_valid = False

        if patterns_to_check and not matched_any:
            result.errors.append(
                f"Log entry doesn't match any known patterns for {log_type}"
            )
            result.is_valid = False

    def _validate_field_completeness(
        self, log_entry: str, log_type: str, result: ValidationResult
    ) -> None:
        """Check if log entry contains required fields."""
        if log_type not in self.required_fields:
            result.warnings.append(f"Unknown log type: {log_type}")
            return

        required = self.required_fields[log_type]

        for field in required:
            has_field = self._check_field_presence(log_entry, field, log_type)
            result.field_completeness[field] = has_field

            if not has_field:
                result.warnings.append(f"Missing or invalid {field} field")

    def _check_field_presence(self, log_entry: str, field: str, log_type: str) -> bool:
        """Check if a specific field is present and valid in log entry."""
        # This is a simplified implementation - in practice, you'd need
        # more sophisticated field extraction based on log type

        field_patterns = {
            "ip": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "timestamp": r"\d{4}[-/]\d{2}[-/]\d{2}|\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|\d{2}/\w{3}/\d{4}",
            "status_code": r"\b[1-5]\d{2}\b",
            "request": r'"[^"]*"',
            "level": r"\b(?:DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b",
            "message": r".+",
            "hostname": r"\b[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9]\b",
        }

        if field in field_patterns:
            return bool(re.search(field_patterns[field], log_entry))

        return True  # Assume present if we don't have a pattern

    def _validate_content(
        self, log_entry: str, log_type: str, result: ValidationResult
    ) -> None:
        """Validate log content for consistency and realism."""
        # Check for timestamp consistency
        timestamps = re.findall(
            r"\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}", log_entry
        )
        if len(timestamps) > 1:
            result.warnings.append("Multiple timestamps found")

        # Check for HTTP status codes - more comprehensive validation
        status_codes = re.findall(r"\b(\d{3})\b", log_entry)
        for code in status_codes:
            code_int = int(code)
            # Valid HTTP status codes are 100-599
            if code_int < 100 or code_int > 599:
                result.warnings.append(f"Invalid HTTP status code: {code}")
            # Check for unrealistic status codes
            elif code_int > 599 or (code_int >= 600):
                result.warnings.append(f"Invalid HTTP status code: {code}")

        # Check for IP addresses
        ips = re.findall(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", log_entry)
        for ip in ips:
            octets = [int(x) for x in ip.split(".")]
            if any(octet > 255 for octet in octets):
                result.warnings.append(f"Invalid IP address: {ip}")

        # Check for reasonable response sizes
        sizes = re.findall(r"\b(\d{4,})\b", log_entry)
        for size in sizes:
            size_int = int(size)
            if size_int > 1000000000:  # 1GB
                result.warnings.append(f"Unusually large response size: {size}")

    def _calculate_quality_score(self, result: ValidationResult) -> float:
        """Calculate quality score based on validation results."""
        score = 100.0

        # Deduct points for errors (major issues)
        score -= len(result.errors) * 30

        # Deduct points for warnings (minor issues)
        score -= len(result.warnings) * 10

        # Deduct points for field incompleteness
        if result.field_completeness:
            missing_fields = sum(
                1 for complete in result.field_completeness.values() if not complete
            )
            score -= missing_fields * 15

        # Deduct points for pattern match failures
        if result.pattern_matches:
            failed_matches = sum(
                1 for matched in result.pattern_matches.values() if not matched
            )
            score -= failed_matches * 20

        return max(0.0, min(100.0, score))

    def validate_log_batch(
        self, log_entries: List[str], log_type: str
    ) -> List[ValidationResult]:
        """
        Validate a batch of log entries.

        Args:
            log_entries: List of log entry strings
            log_type: Type of logs

        Returns:
            List of ValidationResult objects
        """
        results = []

        for log_entry in log_entries:
            result = self.validate_log_entry(log_entry, log_type)
            results.append(result)

        return results

    def validate_log_file(
        self, file_path: str, log_type: str, sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate logs from a file.

        Args:
            file_path: Path to log file
            log_type: Type of logs in file
            sample_size: Optional limit on number of lines to validate

        Returns:
            Dictionary with validation summary
        """
        results = []
        line_count = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        result = self.validate_log_entry(line, log_type)
                        results.append(result)
                        line_count += 1

                        if sample_size and line_count >= sample_size:
                            break

        except Exception as e:
            return {"error": f"Failed to read file: {e}", "results": []}

        # Generate summary
        valid_count = sum(1 for r in results if r.is_valid)

        return {
            "file_path": file_path,
            "total_lines": line_count,
            "valid_logs": valid_count,
            "invalid_logs": line_count - valid_count,
            "success_rate": valid_count / line_count if line_count > 0 else 0,
            "average_quality_score": (
                sum(r.quality_score for r in results) / len(results) if results else 0
            ),
            "results": results,
        }

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics."""
        return {
            "total_validated": self.statistics.total_validated,
            "valid_logs": self.statistics.valid_logs,
            "invalid_logs": self.statistics.invalid_logs,
            "success_rate": self.statistics.get_success_rate(),
            "average_quality_score": self.statistics.average_quality_score,
            "validation_by_type": self.statistics.validation_by_type,
            "common_errors": dict(
                sorted(
                    self.statistics.common_errors.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            ),
            "quality_distribution": self._get_quality_distribution(),
        }

    def _get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of quality scores."""
        if not self.statistics.quality_scores:
            return {}

        distribution = {
            "excellent (90-100)": 0,
            "good (70-89)": 0,
            "fair (50-69)": 0,
            "poor (0-49)": 0,
        }

        for score in self.statistics.quality_scores:
            if score >= 90:
                distribution["excellent (90-100)"] += 1
            elif score >= 70:
                distribution["good (70-89)"] += 1
            elif score >= 50:
                distribution["fair (50-69)"] += 1
            else:
                distribution["poor (0-49)"] += 1

        return distribution

    def reset_statistics(self) -> None:
        """Reset validation statistics."""
        self.statistics = ValidationStatistics()

    def add_custom_pattern(
        self, log_type: str, pattern_name: str, pattern: str
    ) -> None:
        """
        Add a custom validation pattern.

        Args:
            log_type: Log type identifier
            pattern_name: Name for the pattern
            pattern: Regular expression pattern
        """
        if log_type not in self.log_patterns:
            self.log_patterns[log_type] = {}

        self.log_patterns[log_type][pattern_name] = pattern

    def add_required_fields(self, log_type: str, fields: List[str]) -> None:
        """
        Add required fields for a log type.

        Args:
            log_type: Log type identifier
            fields: List of required field names
        """
        self.required_fields[log_type] = fields
