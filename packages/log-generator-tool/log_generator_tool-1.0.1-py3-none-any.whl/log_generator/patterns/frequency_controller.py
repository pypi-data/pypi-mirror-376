"""
Frequency control system for realistic data generation patterns.
"""

import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple


class FrequencyController:
    """
    Controls the frequency and distribution of generated data to create realistic patterns.
    """

    def __init__(self) -> None:
        self.frequency_maps: Dict[str, Dict[Any, float]] = {}
        self.time_based_patterns: Dict[str, Dict[str, Any]] = {}
        self.correlation_rules: List[Dict[str, Any]] = []
        self.burst_patterns: Dict[str, Dict[str, Any]] = {}

    def set_frequency_distribution(
        self, field_type: str, distribution: Dict[Any, float]
    ) -> None:
        """
        Set frequency distribution for a field type.

        Args:
            field_type: Field type to control
            distribution: Map of values to their probabilities (should sum to 1.0)
        """
        # Normalize distribution to ensure it sums to 1.0
        total = sum(distribution.values())
        if total > 0:
            self.frequency_maps[field_type] = {
                key: value / total for key, value in distribution.items()
            }
        else:
            self.frequency_maps[field_type] = distribution

    def set_time_based_pattern(
        self, field_type: str, pattern_config: Dict[str, Any]
    ) -> None:
        """
        Set time-based patterns for field generation.

        Args:
            field_type: Field type to control
            pattern_config: Configuration for time-based patterns
                - 'peak_hours': List of hours (0-23) when values should be more frequent
                - 'peak_multiplier': Multiplier for peak hours (default: 2.0)
                - 'weekend_factor': Factor for weekend generation (default: 0.5)
                - 'business_hours_only': Only generate during business hours (9-17)
        """
        self.time_based_patterns[field_type] = pattern_config

    def add_correlation_rule(self, rule: Dict[str, Any]) -> None:
        """
        Add correlation rule between fields.

        Args:
            rule: Correlation rule configuration
                - 'condition_field': Field that triggers the rule
                - 'condition_value': Value that triggers the rule
                - 'target_field': Field to modify
                - 'target_distribution': New distribution for target field
                - 'probability': Probability of applying the rule (0.0-1.0)
        """
        self.correlation_rules.append(rule)

    def set_burst_pattern(self, field_type: str, burst_config: Dict[str, Any]) -> None:
        """
        Set burst patterns for field generation.

        Args:
            field_type: Field type to control
            burst_config: Burst pattern configuration
                - 'burst_probability': Probability of burst occurring (0.0-1.0)
                - 'burst_duration': Duration of burst in seconds
                - 'burst_multiplier': Multiplier for generation rate during burst
                - 'burst_values': Specific values to generate during burst
        """
        self.burst_patterns[field_type] = burst_config

    def should_generate_field(
        self, field_type: str, current_time: Optional[datetime] = None
    ) -> bool:
        """
        Determine if a field should be generated based on time patterns.

        Args:
            field_type: Field type to check
            current_time: Current time (defaults to now)

        Returns:
            True if field should be generated
        """
        if field_type not in self.time_based_patterns:
            return True

        if current_time is None:
            current_time = datetime.now()

        pattern = self.time_based_patterns[field_type]

        # Check business hours only
        if pattern.get("business_hours_only", False):
            if current_time.hour < 9 or current_time.hour > 17:
                return False
            if current_time.weekday() >= 5:  # Weekend
                return False

        # Check weekend factor
        weekend_factor = pattern.get("weekend_factor", 1.0)
        if current_time.weekday() >= 5:  # Weekend
            if random.random() > weekend_factor:
                return False

        # Check peak hours
        peak_hours = pattern.get("peak_hours", [])
        peak_multiplier = pattern.get("peak_multiplier", 1.0)

        if peak_hours and current_time.hour in peak_hours:
            # More likely to generate during peak hours
            if random.random() < (1.0 / peak_multiplier):
                return True
        elif peak_hours:
            # Less likely to generate outside peak hours
            if random.random() > (1.0 / peak_multiplier):
                return False

        return True

    def get_controlled_value(
        self,
        field_type: str,
        generator_func: Callable,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Get a value using frequency control and correlation rules.

        Args:
            field_type: Field type to generate
            generator_func: Original generator function
            context: Context with other field values for correlation

        Returns:
            Generated value
        """
        context = context or {}

        # Check burst patterns
        if self._is_in_burst(field_type):
            return self._generate_burst_value(field_type, generator_func)

        # Apply correlation rules
        for rule in self.correlation_rules:
            if (
                rule["condition_field"] in context
                and context[rule["condition_field"]] == rule["condition_value"]
                and rule["target_field"] == field_type
                and random.random() < rule.get("probability", 1.0)
            ):

                # Use correlated distribution
                distribution = rule["target_distribution"]
                values = list(distribution.keys())
                weights = list(distribution.values())
                return random.choices(values, weights=weights)[0]

        # Use frequency distribution if available
        if field_type in self.frequency_maps:
            distribution = self.frequency_maps[field_type]
            values = list(distribution.keys())
            weights = list(distribution.values())
            return random.choices(values, weights=weights)[0]

        # Use original generator
        return generator_func()

    def _is_in_burst(self, field_type: str) -> bool:
        """Check if field type is currently in a burst pattern"""
        if field_type not in self.burst_patterns:
            return False

        burst_config = self.burst_patterns[field_type]
        burst_probability = burst_config.get("burst_probability", 0.0)

        return random.random() < burst_probability

    def _generate_burst_value(self, field_type: str, generator_func: Callable) -> Any:
        """Generate value during burst pattern"""
        burst_config = self.burst_patterns[field_type]
        burst_values = burst_config.get("burst_values", [])

        if burst_values:
            return random.choice(burst_values)
        else:
            # Use original generator with burst multiplier
            return generator_func()

    def create_realistic_web_patterns(self) -> None:
        """Create realistic patterns for web server logs"""
        # HTTP status code distribution
        self.set_frequency_distribution(
            "http_status_code",
            {
                "200": 0.70,
                "404": 0.10,
                "500": 0.05,
                "301": 0.03,
                "302": 0.03,
                "400": 0.02,
                "401": 0.02,
                "403": 0.02,
                "503": 0.02,
                "502": 0.01,
            },
        )

        # HTTP method distribution
        self.set_frequency_distribution(
            "http_method",
            {
                "GET": 0.65,
                "POST": 0.25,
                "PUT": 0.04,
                "DELETE": 0.02,
                "PATCH": 0.02,
                "HEAD": 0.01,
                "OPTIONS": 0.01,
            },
        )

        # Log level distribution
        self.set_frequency_distribution(
            "log_level",
            {"INFO": 0.50, "WARN": 0.25, "ERROR": 0.15, "DEBUG": 0.08, "FATAL": 0.02},
        )

        # Peak hours for web traffic (9 AM - 6 PM)
        self.set_time_based_pattern(
            "http_status_code",
            {
                "peak_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
                "peak_multiplier": 2.0,
                "weekend_factor": 0.6,
            },
        )

        # Correlation: 5xx errors often come with higher response times
        self.add_correlation_rule(
            {
                "condition_field": "http_status_code",
                "condition_value": "500",
                "target_field": "response_time",
                "target_distribution": {
                    "1000": 0.3,
                    "2000": 0.3,
                    "3000": 0.2,
                    "5000": 0.2,
                },
                "probability": 0.8,
            }
        )

        # Burst pattern for error codes during incidents
        self.set_burst_pattern(
            "http_status_code",
            {
                "burst_probability": 0.01,  # 1% chance of burst
                "burst_duration": 300,  # 5 minutes
                "burst_multiplier": 5.0,
                "burst_values": ["500", "502", "503"],
            },
        )

    def create_realistic_database_patterns(self) -> None:
        """Create realistic patterns for database logs"""
        # Query type distribution
        self.set_frequency_distribution(
            "query_type",
            {"SELECT": 0.70, "INSERT": 0.15, "UPDATE": 0.10, "DELETE": 0.05},
        )

        # Database operation during business hours
        self.set_time_based_pattern(
            "query_type",
            {
                "business_hours_only": False,
                "peak_hours": [9, 10, 11, 14, 15, 16],
                "peak_multiplier": 3.0,
                "weekend_factor": 0.3,
            },
        )

        # Correlation: Large result sets take longer
        self.add_correlation_rule(
            {
                "condition_field": "rows_affected",
                "condition_value": lambda x: int(x) > 1000,
                "target_field": "query_duration",
                "target_distribution": {
                    "100": 0.2,
                    "500": 0.3,
                    "1000": 0.3,
                    "2000": 0.2,
                },
                "probability": 0.9,
            }
        )

    def create_realistic_security_patterns(self) -> None:
        """Create realistic patterns for security logs"""
        # Security event distribution
        self.set_frequency_distribution(
            "security_event",
            {
                "login_success": 0.85,
                "login_failure": 0.10,
                "permission_denied": 0.03,
                "suspicious_activity": 0.02,
            },
        )

        # Security events more common during business hours
        self.set_time_based_pattern(
            "security_event",
            {
                "peak_hours": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
                "peak_multiplier": 4.0,
                "weekend_factor": 0.2,
            },
        )

        # Burst pattern for security incidents
        self.set_burst_pattern(
            "security_event",
            {
                "burst_probability": 0.005,  # 0.5% chance
                "burst_duration": 600,  # 10 minutes
                "burst_multiplier": 10.0,
                "burst_values": [
                    "login_failure",
                    "permission_denied",
                    "suspicious_activity",
                ],
            },
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about configured patterns"""
        return {
            "frequency_maps_count": len(self.frequency_maps),
            "time_patterns_count": len(self.time_based_patterns),
            "correlation_rules_count": len(self.correlation_rules),
            "burst_patterns_count": len(self.burst_patterns),
            "configured_fields": list(
                set(
                    list(self.frequency_maps.keys())
                    + list(self.time_based_patterns.keys())
                    + list(self.burst_patterns.keys())
                )
            ),
        }
