"""
Log analysis and sampling functionality for quality assurance.
"""

import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.log_validator import LogValidator, ValidationResult
from ..core.models import LogEntry


@dataclass
class LogSample:
    """Represents a sample of logs with metadata."""

    log_type: str
    sample_size: int
    logs: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert sample to dictionary."""
        return {
            "log_type": self.log_type,
            "sample_size": self.sample_size,
            "logs": self.logs,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class LogStatistics:
    """Comprehensive statistics for log analysis."""

    total_logs: int = 0
    log_types: Dict[str, int] = field(default_factory=dict)
    log_levels: Dict[str, int] = field(default_factory=dict)
    status_codes: Dict[str, int] = field(default_factory=dict)
    ip_addresses: Dict[str, int] = field(default_factory=dict)
    user_agents: Dict[str, int] = field(default_factory=dict)
    time_distribution: Dict[str, int] = field(default_factory=dict)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    field_completeness: Dict[str, float] = field(default_factory=dict)
    average_log_length: float = 0.0
    quality_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "total_logs": self.total_logs,
            "log_types": self.log_types,
            "log_levels": self.log_levels,
            "status_codes": self.status_codes,
            "top_ip_addresses": dict(
                sorted(self.ip_addresses.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "top_user_agents": dict(
                sorted(self.user_agents.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
            "time_distribution": self.time_distribution,
            "error_patterns": dict(
                sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[
                    :10
                ]
            ),
            "field_completeness": self.field_completeness,
            "average_log_length": self.average_log_length,
            "quality_metrics": self.quality_metrics,
        }


@dataclass
class QualityReport:
    """Quality assessment report for logs."""

    overall_score: float
    total_logs_analyzed: int
    validation_results: List[ValidationResult] = field(default_factory=list)
    statistics: Optional[LogStatistics] = None
    recommendations: List[str] = field(default_factory=list)
    issues_found: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "overall_score": self.overall_score,
            "total_logs_analyzed": self.total_logs_analyzed,
            "validation_summary": {
                "valid_logs": sum(1 for r in self.validation_results if r.is_valid),
                "invalid_logs": sum(
                    1 for r in self.validation_results if not r.is_valid
                ),
                "average_quality_score": (
                    sum(r.quality_score for r in self.validation_results)
                    / len(self.validation_results)
                    if self.validation_results
                    else 0
                ),
            },
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "recommendations": self.recommendations,
            "issues_found": self.issues_found,
            "timestamp": self.timestamp.isoformat(),
        }


class LogAnalyzer:
    """
    Comprehensive log analyzer for statistics, sampling, and quality assessment.
    """

    def __init__(self):
        self.validator = LogValidator()

        # Patterns for extracting various log components
        self.extraction_patterns = {
            "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "timestamp_iso": r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}",
            "timestamp_apache": r"\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}",
            "timestamp_syslog": r"\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}",
            "status_code": r"\b([1-5]\d{2})\b",
            "log_level": r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|NOTICE)\b",
            "user_agent": r'"([^"]*Mozilla[^"]*)"',
            "http_method": r"\b(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\b",
            "response_size": r"\b(\d+)\s*$",
            "error_message": r"(?:error|Error|ERROR)[:\s]+([^,\n]+)",
        }

    def generate_samples(
        self,
        log_entries: List[str],
        log_type: str,
        sample_size: int = 10,
        strategy: str = "random",
    ) -> LogSample:
        """
        Generate samples from log entries using different strategies.

        Args:
            log_entries: List of log entries to sample from
            log_type: Type of logs
            sample_size: Number of samples to generate
            strategy: Sampling strategy ("random", "systematic", "stratified", "quality_based")

        Returns:
            LogSample object with selected samples
        """
        if not log_entries:
            return LogSample(log_type=log_type, sample_size=0)

        sample_size = min(sample_size, len(log_entries))

        if strategy == "random":
            samples = random.sample(log_entries, sample_size)
        elif strategy == "systematic":
            samples = self._systematic_sampling(log_entries, sample_size)
        elif strategy == "stratified":
            samples = self._stratified_sampling(log_entries, log_type, sample_size)
        elif strategy == "quality_based":
            samples = self._quality_based_sampling(log_entries, log_type, sample_size)
        else:
            samples = random.sample(log_entries, sample_size)

        metadata = {
            "strategy": strategy,
            "original_count": len(log_entries),
            "sampling_ratio": sample_size / len(log_entries),
        }

        return LogSample(
            log_type=log_type, sample_size=sample_size, logs=samples, metadata=metadata
        )

    def _systematic_sampling(
        self, log_entries: List[str], sample_size: int
    ) -> List[str]:
        """Systematic sampling with fixed intervals."""
        if sample_size >= len(log_entries):
            return log_entries

        interval = len(log_entries) // sample_size
        start = random.randint(0, interval - 1)

        samples = []
        for i in range(sample_size):
            index = (start + i * interval) % len(log_entries)
            samples.append(log_entries[index])

        return samples

    def _stratified_sampling(
        self, log_entries: List[str], log_type: str, sample_size: int
    ) -> List[str]:
        """Stratified sampling based on log characteristics."""
        # Group logs by characteristics (e.g., status codes, log levels)
        strata = defaultdict(list)

        for log_entry in log_entries:
            # Determine stratum based on log characteristics
            stratum = self._determine_stratum(log_entry, log_type)
            strata[stratum].append(log_entry)

        # Sample proportionally from each stratum
        samples = []
        total_strata = len(strata)

        if total_strata == 0:
            return random.sample(log_entries, sample_size)

        samples_per_stratum = sample_size // total_strata
        remaining_samples = sample_size % total_strata

        for i, (stratum, entries) in enumerate(strata.items()):
            stratum_sample_size = samples_per_stratum
            if i < remaining_samples:
                stratum_sample_size += 1

            if stratum_sample_size > 0:
                stratum_samples = random.sample(
                    entries, min(stratum_sample_size, len(entries))
                )
                samples.extend(stratum_samples)

        return samples[:sample_size]

    def _determine_stratum(self, log_entry: str, log_type: str) -> str:
        """Determine stratum for stratified sampling."""
        # Extract status code for HTTP logs - be more specific
        status_match = re.search(r"\s([1-5]\d{2})\s", log_entry)
        if status_match:
            status_code = int(status_match.group(1))
            if status_code < 300:
                return "success"
            elif status_code < 400:
                return "redirect"
            elif status_code < 500:
                return "client_error"
            else:
                return "server_error"

        # Extract log level
        level_match = re.search(self.extraction_patterns["log_level"], log_entry)
        if level_match:
            level = level_match.group(1).upper()
            if level in ["DEBUG", "INFO", "NOTICE"]:
                return "info"
            elif level in ["WARN", "WARNING"]:
                return "warning"
            else:
                return "error"

        return "other"

    def _quality_based_sampling(
        self, log_entries: List[str], log_type: str, sample_size: int
    ) -> List[str]:
        """Quality-based sampling prioritizing diverse quality scores."""
        # Validate a subset to get quality scores
        validation_sample_size = min(100, len(log_entries))
        validation_sample = random.sample(log_entries, validation_sample_size)

        quality_scores = []
        for log_entry in validation_sample:
            result = self.validator.validate_log_entry(log_entry, log_type)
            quality_scores.append((log_entry, result.quality_score))

        # Sort by quality score and select diverse samples
        quality_scores.sort(key=lambda x: x[1])

        # Select samples from different quality ranges
        samples = []
        ranges = [
            (0, 0.25),  # Low quality
            (0.25, 0.5),  # Medium-low quality
            (0.5, 0.75),  # Medium-high quality
            (0.75, 1.0),  # High quality
        ]

        samples_per_range = sample_size // len(ranges)

        for start, end in ranges:
            range_entries = [
                entry for entry, score in quality_scores if start <= score / 100 < end
            ]
            if range_entries:
                range_sample_size = min(samples_per_range, len(range_entries))
                samples.extend(random.sample(range_entries, range_sample_size))

        # Fill remaining slots randomly
        while len(samples) < sample_size and len(samples) < len(log_entries):
            remaining_entries = [entry for entry in log_entries if entry not in samples]
            if remaining_entries:
                samples.append(random.choice(remaining_entries))
            else:
                break

        return samples[:sample_size]

    def analyze_logs(self, log_entries: List[str], log_type: str) -> LogStatistics:
        """
        Perform comprehensive statistical analysis of log entries.

        Args:
            log_entries: List of log entries to analyze
            log_type: Type of logs being analyzed

        Returns:
            LogStatistics object with comprehensive analysis
        """
        stats = LogStatistics()
        stats.total_logs = len(log_entries)
        stats.log_types[log_type] = len(log_entries)

        # Track various metrics
        log_lengths = []
        timestamps = []
        field_presence = defaultdict(int)

        for log_entry in log_entries:
            log_lengths.append(len(log_entry))

            # Extract and count various components
            self._extract_and_count(log_entry, stats)

            # Track field presence for completeness analysis
            self._analyze_field_presence(log_entry, log_type, field_presence)

            # Extract timestamps for time distribution
            timestamp = self._extract_timestamp(log_entry)
            if timestamp:
                timestamps.append(timestamp)

        # Calculate averages and distributions
        stats.average_log_length = (
            sum(log_lengths) / len(log_lengths) if log_lengths else 0
        )

        # Calculate field completeness
        total_logs = len(log_entries)
        for field, count in field_presence.items():
            stats.field_completeness[field] = count / total_logs

        # Analyze time distribution
        stats.time_distribution = self._analyze_time_distribution(timestamps)

        # Calculate quality metrics
        stats.quality_metrics = self._calculate_quality_metrics(log_entries, log_type)

        return stats

    def _extract_and_count(self, log_entry: str, stats: LogStatistics) -> None:
        """Extract and count various log components."""
        # Extract IP addresses
        ips = re.findall(self.extraction_patterns["ip_address"], log_entry)
        for ip in ips:
            stats.ip_addresses[ip] = stats.ip_addresses.get(ip, 0) + 1

        # Extract status codes - be more specific to avoid matching IP addresses
        status_codes = re.findall(r"\s([1-5]\d{2})\s", log_entry)
        for code in status_codes:
            stats.status_codes[code] = stats.status_codes.get(code, 0) + 1

        # Extract log levels
        levels = re.findall(self.extraction_patterns["log_level"], log_entry)
        for level in levels:
            stats.log_levels[level.upper()] = stats.log_levels.get(level.upper(), 0) + 1

        # Extract user agents - look for quoted strings that might be user agents
        user_agents = re.findall(
            r'"([^"]*(?:Mozilla|curl|wget|Python|Chrome|Firefox|Safari|Edge)[^"]*)"',
            log_entry,
        )
        for ua in user_agents:
            # Simplify user agent for counting
            simplified_ua = self._simplify_user_agent(ua)
            stats.user_agents[simplified_ua] = (
                stats.user_agents.get(simplified_ua, 0) + 1
            )

        # Extract error patterns
        errors = re.findall(self.extraction_patterns["error_message"], log_entry)
        for error in errors:
            # Normalize error message
            normalized_error = self._normalize_error_message(error)
            stats.error_patterns[normalized_error] = (
                stats.error_patterns.get(normalized_error, 0) + 1
            )

    def _analyze_field_presence(
        self, log_entry: str, log_type: str, field_presence: Dict[str, int]
    ) -> None:
        """Analyze presence of required fields."""
        required_fields = self.validator.required_fields.get(log_type, [])

        for field in required_fields:
            if self.validator._check_field_presence(log_entry, field, log_type):
                field_presence[field] += 1

    def _extract_timestamp(self, log_entry: str) -> Optional[datetime]:
        """Extract timestamp from log entry."""
        # Try different timestamp formats
        patterns = [
            (self.extraction_patterns["timestamp_iso"], "%Y-%m-%d %H:%M:%S"),
            (self.extraction_patterns["timestamp_apache"], "%d/%b/%Y:%H:%M:%S"),
        ]

        for pattern, date_format in patterns:
            match = re.search(pattern, log_entry)
            if match:
                try:
                    timestamp_str = match.group(0)
                    if "T" in timestamp_str:
                        timestamp_str = timestamp_str.replace("T", " ")
                    return datetime.strptime(timestamp_str, date_format)
                except ValueError:
                    continue

        return None

    def _analyze_time_distribution(self, timestamps: List[datetime]) -> Dict[str, int]:
        """Analyze time distribution of logs."""
        distribution = defaultdict(int)

        for timestamp in timestamps:
            # Hour distribution
            hour_key = f"hour_{timestamp.hour:02d}"
            distribution[hour_key] += 1

            # Day of week distribution
            day_key = f"day_{timestamp.strftime('%A')}"
            distribution[day_key] += 1

        return dict(distribution)

    def _simplify_user_agent(self, user_agent: str) -> str:
        """Simplify user agent string for counting."""
        if "Chrome" in user_agent:
            return "Chrome"
        elif "Firefox" in user_agent:
            return "Firefox"
        elif "Safari" in user_agent and "Chrome" not in user_agent:
            return "Safari"
        elif "Edge" in user_agent:
            return "Edge"
        elif "curl" in user_agent:
            return "curl"
        elif "wget" in user_agent:
            return "wget"
        else:
            return "Other"

    def _normalize_error_message(self, error_message: str) -> str:
        """Normalize error message for pattern recognition."""
        # Remove specific details like IDs, timestamps, etc.
        normalized = re.sub(r"\d+", "N", error_message)
        normalized = re.sub(r"[0-9a-fA-F]{8,}", "ID", normalized)
        normalized = normalized.strip()[:100]  # Limit length
        return normalized

    def _calculate_quality_metrics(
        self, log_entries: List[str], log_type: str
    ) -> Dict[str, float]:
        """Calculate quality metrics for the log set."""
        if not log_entries:
            return {}

        # Sample for quality assessment
        sample_size = min(50, len(log_entries))
        sample_entries = random.sample(log_entries, sample_size)

        validation_results = []
        for entry in sample_entries:
            result = self.validator.validate_log_entry(entry, log_type)
            validation_results.append(result)

        # Calculate metrics
        valid_count = sum(1 for r in validation_results if r.is_valid)
        avg_quality = sum(r.quality_score for r in validation_results) / len(
            validation_results
        )

        return {
            "validation_rate": valid_count / len(validation_results),
            "average_quality_score": avg_quality,
            "error_rate": (len(validation_results) - valid_count)
            / len(validation_results),
            "completeness_score": (
                sum(
                    sum(r.field_completeness.values()) / len(r.field_completeness)
                    for r in validation_results
                    if r.field_completeness
                )
                / len(validation_results)
                if validation_results
                else 0
            ),
        }

    def generate_quality_report(
        self, log_entries: List[str], log_type: str
    ) -> QualityReport:
        """
        Generate comprehensive quality report for log entries.

        Args:
            log_entries: List of log entries to analyze
            log_type: Type of logs being analyzed

        Returns:
            QualityReport with comprehensive assessment
        """
        # Validate all logs
        validation_results = []
        for log_entry in log_entries:
            result = self.validator.validate_log_entry(log_entry, log_type)
            validation_results.append(result)

        # Generate statistics
        statistics = self.analyze_logs(log_entries, log_type)

        # Calculate overall score
        valid_count = sum(1 for r in validation_results if r.is_valid)
        validation_rate = (
            valid_count / len(validation_results) if validation_results else 0
        )
        avg_quality = (
            sum(r.quality_score for r in validation_results) / len(validation_results)
            if validation_results
            else 0
        )

        overall_score = (validation_rate * 0.6 + avg_quality / 100 * 0.4) * 100

        # Generate recommendations and identify issues
        recommendations = self._generate_recommendations(statistics, validation_results)
        issues = self._identify_issues(statistics, validation_results)

        return QualityReport(
            overall_score=overall_score,
            total_logs_analyzed=len(log_entries),
            validation_results=validation_results,
            statistics=statistics,
            recommendations=recommendations,
            issues_found=issues,
        )

    def _generate_recommendations(
        self, statistics: LogStatistics, validation_results: List[ValidationResult]
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Check validation rate
        valid_count = sum(1 for r in validation_results if r.is_valid)
        validation_rate = (
            valid_count / len(validation_results) if validation_results else 0
        )

        if validation_rate < 0.8:
            recommendations.append(
                "Improve log format consistency - validation rate is below 80%"
            )

        # Check field completeness
        avg_completeness = (
            sum(statistics.field_completeness.values())
            / len(statistics.field_completeness)
            if statistics.field_completeness
            else 0
        )
        if avg_completeness < 0.9:
            recommendations.append(
                "Ensure all required fields are present in log entries"
            )

        # Check error distribution
        error_count = sum(
            count
            for level, count in statistics.log_levels.items()
            if level in ["ERROR", "CRITICAL", "FATAL"]
        )
        total_logs = statistics.total_logs

        if total_logs > 0 and error_count / total_logs > 0.1:
            recommendations.append(
                "High error rate detected - investigate error patterns"
            )

        # Check IP diversity
        if len(statistics.ip_addresses) < 5 and statistics.total_logs > 100:
            recommendations.append(
                "Low IP address diversity - consider adding more varied source IPs"
            )

        # Check status code distribution
        if statistics.status_codes:
            success_codes = sum(
                count
                for code, count in statistics.status_codes.items()
                if code.startswith(("2", "3"))
            )
            if success_codes / sum(statistics.status_codes.values()) < 0.7:
                recommendations.append(
                    "Consider increasing success rate in HTTP status codes"
                )

        return recommendations

    def _identify_issues(
        self, statistics: LogStatistics, validation_results: List[ValidationResult]
    ) -> List[str]:
        """Identify issues in the log data."""
        issues = []

        # Common validation errors
        error_counter = Counter()
        for result in validation_results:
            for error in result.errors:
                error_counter[error] += 1

        for error, count in error_counter.most_common(5):
            if count > len(validation_results) * 0.1:  # More than 10% of logs
                issues.append(
                    f"Common validation error: {error} (affects {count} logs)"
                )

        # Check for suspicious patterns
        if statistics.ip_addresses:
            top_ip_count = max(statistics.ip_addresses.values())
            if top_ip_count > statistics.total_logs * 0.5:
                issues.append(
                    "Single IP address dominates traffic (possible bot or test data)"
                )

        # Check timestamp distribution
        if statistics.time_distribution:
            hour_counts = [
                count
                for key, count in statistics.time_distribution.items()
                if key.startswith("hour_")
            ]
            if hour_counts and max(hour_counts) > sum(hour_counts) * 0.8:
                issues.append(
                    "Logs concentrated in single hour (possible batch generation)"
                )

        return issues

    def compare_log_sets(
        self, log_set1: List[str], log_set2: List[str], log_type: str
    ) -> Dict[str, Any]:
        """
        Compare two sets of logs and provide analysis.

        Args:
            log_set1: First set of log entries
            log_set2: Second set of log entries
            log_type: Type of logs being compared

        Returns:
            Dictionary with comparison results
        """
        stats1 = self.analyze_logs(log_set1, log_type)
        stats2 = self.analyze_logs(log_set2, log_type)

        comparison = {
            "set1_stats": stats1.to_dict(),
            "set2_stats": stats2.to_dict(),
            "differences": {},
            "similarities": {},
            "recommendations": [],
        }

        # Compare key metrics
        if stats1.total_logs > 0 and stats2.total_logs > 0:
            # Compare status code distributions
            if stats1.status_codes and stats2.status_codes:
                comparison["differences"]["status_codes"] = self._compare_distributions(
                    stats1.status_codes, stats2.status_codes
                )

            # Compare log level distributions
            if stats1.log_levels and stats2.log_levels:
                comparison["differences"]["log_levels"] = self._compare_distributions(
                    stats1.log_levels, stats2.log_levels
                )

            # Compare quality metrics
            comparison["differences"]["quality_metrics"] = {
                "set1": stats1.quality_metrics,
                "set2": stats2.quality_metrics,
            }

        return comparison

    def _compare_distributions(
        self, dist1: Dict[str, int], dist2: Dict[str, int]
    ) -> Dict[str, Any]:
        """Compare two distributions."""
        total1 = sum(dist1.values())
        total2 = sum(dist2.values())

        if total1 == 0 or total2 == 0:
            return {"error": "Empty distribution"}

        # Calculate proportions
        prop1 = {k: v / total1 for k, v in dist1.items()}
        prop2 = {k: v / total2 for k, v in dist2.items()}

        # Find differences
        all_keys = set(prop1.keys()) | set(prop2.keys())
        differences = {}

        for key in all_keys:
            p1 = prop1.get(key, 0)
            p2 = prop2.get(key, 0)
            diff = abs(p1 - p2)
            if diff > 0.05:  # 5% threshold
                differences[key] = {
                    "set1_proportion": p1,
                    "set2_proportion": p2,
                    "difference": diff,
                }

        return {
            "significant_differences": differences,
            "total_keys": len(all_keys),
            "common_keys": len(set(prop1.keys()) & set(prop2.keys())),
        }
