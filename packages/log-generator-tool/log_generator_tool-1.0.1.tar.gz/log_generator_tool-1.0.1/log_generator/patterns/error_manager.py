"""
Advanced error pattern management system with custom pattern support,
frequency control, and realistic error scenario generation.
"""

import json
import random
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .error_patterns import ErrorPattern, ErrorPatternLibrary


@dataclass
class ErrorScenario:
    """Represents a realistic error scenario with multiple related errors"""

    name: str
    description: str
    category: str
    patterns: List[str]  # List of pattern IDs
    sequence_rules: Dict[str, Any]  # Rules for error sequence generation
    duration_minutes: int = 30  # How long the scenario typically lasts
    escalation_probability: float = 0.3  # Probability of errors escalating


@dataclass
class ErrorFrequencyConfig:
    """Configuration for error frequency and timing"""

    base_frequency: float = 1.0  # Base errors per minute
    peak_hours: List[int] = None  # Hours when errors are more frequent (0-23)
    peak_multiplier: float = 2.0  # Frequency multiplier during peak hours
    burst_probability: float = 0.1  # Probability of error bursts
    burst_multiplier: float = 5.0  # Frequency multiplier during bursts
    burst_duration_minutes: int = 5  # Duration of error bursts

    def __post_init__(self):
        if self.peak_hours is None:
            self.peak_hours = [9, 10, 11, 14, 15, 16]  # Typical business hours


class ErrorPatternManager:
    """
    Advanced error pattern management system that provides:
    - Custom error pattern creation and management
    - Realistic error frequency and timing control
    - Error scenario generation with escalation
    - Pattern weight adjustment based on real-world data
    - Integration with existing log generators
    """

    def __init__(
        self,
        patterns_dir: str = "error_patterns",
        scenarios_dir: str = "error_scenarios",
    ):
        self.library = ErrorPatternLibrary(patterns_dir)
        self.scenarios_dir = Path(scenarios_dir)
        self.scenarios_dir.mkdir(exist_ok=True)

        # Error frequency and timing
        self.frequency_config = ErrorFrequencyConfig()
        self.current_burst_end = None
        self.error_history = deque(maxlen=1000)  # Recent error history

        # Scenarios and escalation
        self.scenarios: Dict[str, ErrorScenario] = {}
        self.active_scenarios: Dict[str, datetime] = {}  # scenario_name -> start_time

        # Pattern usage statistics
        self.pattern_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "usage_count": 0,
                "last_used": None,
                "avg_response_time": 0.0,
                "escalation_count": 0,
            }
        )

        self._load_scenarios()
        self._initialize_default_scenarios()

    def _load_scenarios(self) -> None:
        """Load error scenarios from files"""
        scenario_files = list(self.scenarios_dir.glob("*.json"))

        for scenario_file in scenario_files:
            try:
                with open(scenario_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    for scenario_data in data:
                        scenario = ErrorScenario(**scenario_data)
                        self.scenarios[scenario.name] = scenario
                elif isinstance(data, dict):
                    scenario = ErrorScenario(**data)
                    self.scenarios[scenario.name] = scenario

            except Exception as e:
                print(
                    f"Warning: Failed to load error scenario from {scenario_file}: {e}"
                )

    def _initialize_default_scenarios(self) -> None:
        """Initialize default error scenarios"""
        default_scenarios = [
            ErrorScenario(
                name="database_overload",
                description="Database becomes overloaded leading to cascading failures",
                category="database",
                patterns=[
                    "mysql_connection_lost",
                    "postgresql_deadlock",
                    "database_slow_query",
                ],
                sequence_rules={
                    "start_pattern": "database_slow_query",
                    "escalation_chain": [
                        "database_slow_query",
                        "mysql_connection_lost",
                        "postgresql_deadlock",
                    ],
                    "escalation_delay_minutes": [2, 5, 10],
                },
                duration_minutes=45,
                escalation_probability=0.7,
            ),
            ErrorScenario(
                name="web_server_cascade",
                description="Web server errors cascading from upstream issues",
                category="web_server",
                patterns=[
                    "nginx_timeout",
                    "nginx_connection_refused",
                    "apache_file_not_found",
                ],
                sequence_rules={
                    "start_pattern": "nginx_timeout",
                    "escalation_chain": [
                        "nginx_timeout",
                        "nginx_connection_refused",
                        "apache_file_not_found",
                    ],
                    "escalation_delay_minutes": [1, 3, 8],
                },
                duration_minutes=30,
                escalation_probability=0.5,
            ),
            ErrorScenario(
                name="system_resource_exhaustion",
                description="System resources become exhausted causing multiple failures",
                category="system",
                patterns=[
                    "disk_space_full",
                    "memory_allocation_failed",
                    "service_failed_to_start",
                ],
                sequence_rules={
                    "start_pattern": "memory_allocation_failed",
                    "escalation_chain": [
                        "memory_allocation_failed",
                        "disk_space_full",
                        "service_failed_to_start",
                    ],
                    "escalation_delay_minutes": [5, 10, 15],
                },
                duration_minutes=60,
                escalation_probability=0.8,
            ),
            ErrorScenario(
                name="application_validation_storm",
                description="High volume of validation errors indicating potential attack or bug",
                category="application",
                patterns=[
                    "fastapi_validation_error",
                    "api_rate_limit_exceeded",
                    "django_database_error",
                ],
                sequence_rules={
                    "start_pattern": "fastapi_validation_error",
                    "escalation_chain": [
                        "fastapi_validation_error",
                        "api_rate_limit_exceeded",
                        "django_database_error",
                    ],
                    "escalation_delay_minutes": [1, 2, 5],
                },
                duration_minutes=20,
                escalation_probability=0.4,
            ),
        ]

        for scenario in default_scenarios:
            if scenario.name not in self.scenarios:
                self.scenarios[scenario.name] = scenario

    def add_custom_pattern(self, pattern: ErrorPattern) -> bool:
        """
        Add a custom error pattern with automatic weight adjustment.

        Args:
            pattern: ErrorPattern to add

        Returns:
            True if pattern was added successfully
        """
        success = self.library.add_custom_pattern(pattern)

        if success:
            # Initialize statistics for new pattern
            self.pattern_stats[pattern.id] = {
                "usage_count": 0,
                "last_used": None,
                "avg_response_time": 0.0,
                "escalation_count": 0,
                "created_at": datetime.now().isoformat(),
            }

        return success

    def update_pattern_frequency(
        self, pattern_id: str, new_weight: float, reason: str = ""
    ) -> bool:
        """
        Update pattern frequency weight with reasoning.

        Args:
            pattern_id: ID of pattern to update
            new_weight: New frequency weight
            reason: Reason for the change

        Returns:
            True if update was successful
        """
        success = self.library.update_pattern_weight(pattern_id, new_weight)

        if success:
            # Log the change
            self.pattern_stats[pattern_id]["weight_changes"] = self.pattern_stats[
                pattern_id
            ].get("weight_changes", [])
            self.pattern_stats[pattern_id]["weight_changes"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "old_weight": (
                        self.library.get_pattern(pattern_id).frequency_weight
                        if pattern_id in self.library.patterns
                        else 0
                    ),
                    "new_weight": new_weight,
                    "reason": reason,
                }
            )

        return success

    def create_error_scenario(self, scenario: ErrorScenario) -> bool:
        """
        Create a new error scenario.

        Args:
            scenario: ErrorScenario to create

        Returns:
            True if scenario was created successfully
        """
        # Validate that all patterns exist
        for pattern_id in scenario.patterns:
            if not self.library.get_pattern(pattern_id):
                raise ValueError(f"Pattern '{pattern_id}' not found in library")

        self.scenarios[scenario.name] = scenario
        return self._save_scenario(scenario)

    def start_error_scenario(self, scenario_name: str) -> bool:
        """
        Start an error scenario.

        Args:
            scenario_name: Name of scenario to start

        Returns:
            True if scenario was started successfully
        """
        if scenario_name not in self.scenarios:
            return False

        self.active_scenarios[scenario_name] = datetime.now()
        return True

    def stop_error_scenario(self, scenario_name: str) -> bool:
        """
        Stop an active error scenario.

        Args:
            scenario_name: Name of scenario to stop

        Returns:
            True if scenario was stopped successfully
        """
        if scenario_name in self.active_scenarios:
            del self.active_scenarios[scenario_name]
            return True
        return False

    def generate_realistic_error(
        self,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        consider_scenarios: bool = True,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Generate a realistic error considering current scenarios, frequency, and timing.

        Args:
            category: Optional category filter
            severity: Optional severity filter
            consider_scenarios: Whether to consider active scenarios

        Returns:
            Tuple of (pattern_id, error_message, metadata)
        """
        current_time = datetime.now()

        # Determine if we should generate an error based on frequency
        if not self._should_generate_error(current_time):
            return None, None, {}

        # Check for active scenarios first
        if consider_scenarios and self.active_scenarios:
            scenario_error = self._generate_scenario_error(current_time)
            if scenario_error:
                return scenario_error

        # Generate regular error based on current conditions
        adjusted_weights = self._calculate_adjusted_weights(
            current_time, category, severity
        )

        if not adjusted_weights:
            return None, None, {}

        # Select pattern based on adjusted weights
        pattern_ids, weights = zip(*adjusted_weights.items())
        selected_pattern_id = random.choices(
            list(pattern_ids), weights=list(weights), k=1
        )[0]
        selected_pattern = self.library.get_pattern(selected_pattern_id)

        # Generate error message
        error_message = self.library.generate_error_message(selected_pattern.id)

        # Update statistics
        self._update_pattern_stats(selected_pattern.id, current_time)

        # Create metadata
        metadata = {
            "timestamp": current_time.isoformat(),
            "pattern_id": selected_pattern.id,
            "category": selected_pattern.category,
            "severity": selected_pattern.severity,
            "frequency_weight": selected_pattern.frequency_weight,
            "is_scenario_error": False,
        }

        return selected_pattern.id, error_message, metadata

    def _should_generate_error(self, current_time: datetime) -> bool:
        """Determine if an error should be generated based on frequency settings"""
        # Calculate current frequency based on time and conditions
        base_freq = self.frequency_config.base_frequency

        # Apply peak hour multiplier
        current_hour = current_time.hour
        if current_hour in self.frequency_config.peak_hours:
            base_freq *= self.frequency_config.peak_multiplier

        # Check for burst conditions
        if self.current_burst_end and current_time < self.current_burst_end:
            base_freq *= self.frequency_config.burst_multiplier
        elif random.random() < self.frequency_config.burst_probability:
            # Start new burst
            self.current_burst_end = current_time + timedelta(
                minutes=self.frequency_config.burst_duration_minutes
            )
            base_freq *= self.frequency_config.burst_multiplier

        # Convert frequency to probability (assuming this is called once per minute)
        probability = min(
            base_freq / 60.0, 1.0
        )  # Convert per-minute to per-second probability

        return random.random() < probability

    def _generate_scenario_error(
        self, current_time: datetime
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """Generate an error from active scenarios"""
        for scenario_name, start_time in list(self.active_scenarios.items()):
            scenario = self.scenarios[scenario_name]

            # Check if scenario should still be active
            elapsed_minutes = (current_time - start_time).total_seconds() / 60
            if elapsed_minutes > scenario.duration_minutes:
                self.stop_error_scenario(scenario_name)
                continue

            # Determine which pattern to use based on scenario rules
            pattern_id = self._select_scenario_pattern(scenario, elapsed_minutes)
            if not pattern_id:
                continue

            # Generate error message
            error_message = self.library.generate_error_message(pattern_id)

            # Update statistics
            self._update_pattern_stats(pattern_id, current_time, is_scenario=True)

            # Create metadata
            metadata = {
                "timestamp": current_time.isoformat(),
                "pattern_id": pattern_id,
                "scenario_name": scenario_name,
                "scenario_elapsed_minutes": elapsed_minutes,
                "is_scenario_error": True,
            }

            return pattern_id, error_message, metadata

        return None

    def _select_scenario_pattern(
        self, scenario: ErrorScenario, elapsed_minutes: float
    ) -> Optional[str]:
        """Select appropriate pattern for scenario based on elapsed time"""
        rules = scenario.sequence_rules

        if "escalation_chain" in rules and "escalation_delay_minutes" in rules:
            # Use escalation chain
            chain = rules["escalation_chain"]
            delays = rules["escalation_delay_minutes"]

            # Find current escalation level
            current_level = 0
            for i, delay in enumerate(delays):
                if elapsed_minutes >= delay:
                    current_level = i + 1
                else:
                    break

            # Select pattern from current level
            if current_level < len(chain):
                return chain[current_level]
            else:
                # Use last pattern in chain
                return chain[-1]

        # Fallback to random selection from scenario patterns
        return random.choice(scenario.patterns)

    def _calculate_adjusted_weights(
        self,
        current_time: datetime,
        category: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> Dict[str, float]:
        """Calculate adjusted weights based on current conditions"""
        patterns = list(self.library.patterns.values())

        # Apply filters
        if category:
            patterns = [p for p in patterns if p.category == category]
        if severity:
            patterns = [p for p in patterns if p.severity == severity]

        adjusted_weights = {}

        for pattern in patterns:
            weight = pattern.frequency_weight

            # Adjust based on recent usage (reduce weight for recently used patterns)
            stats = self.pattern_stats.get(pattern.id, {})
            if stats.get("last_used"):
                last_used = datetime.fromisoformat(stats["last_used"])
                minutes_since_use = (current_time - last_used).total_seconds() / 60

                # Reduce weight if used recently (within last 10 minutes)
                if minutes_since_use < 10:
                    weight *= minutes_since_use / 10

            # Adjust based on severity and time of day
            if pattern.severity == "critical":
                # Critical errors are less common during business hours
                if current_time.hour in self.frequency_config.peak_hours:
                    weight *= 0.5

            adjusted_weights[pattern.id] = weight

        return adjusted_weights

    def _update_pattern_stats(
        self, pattern_id: str, timestamp: datetime, is_scenario: bool = False
    ) -> None:
        """Update pattern usage statistics"""
        stats = self.pattern_stats[pattern_id]
        stats["usage_count"] += 1
        stats["last_used"] = timestamp.isoformat()

        if is_scenario:
            stats["escalation_count"] += 1

        # Add to error history
        self.error_history.append(
            {
                "pattern_id": pattern_id,
                "timestamp": timestamp.isoformat(),
                "is_scenario": is_scenario,
            }
        )

    def get_pattern_analytics(self, pattern_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a specific pattern"""
        if pattern_id not in self.library.patterns:
            return {}

        pattern = self.library.get_pattern(pattern_id)
        stats = self.pattern_stats.get(pattern_id, {})

        # Calculate recent usage
        recent_usage = sum(
            1 for entry in self.error_history if entry["pattern_id"] == pattern_id
        )

        return {
            "pattern_info": {
                "id": pattern.id,
                "category": pattern.category,
                "severity": pattern.severity,
                "frequency_weight": pattern.frequency_weight,
                "description": pattern.description,
            },
            "usage_stats": {
                "total_usage": stats.get("usage_count", 0),
                "recent_usage": recent_usage,
                "last_used": stats.get("last_used"),
                "escalation_count": stats.get("escalation_count", 0),
            },
            "effectiveness": {
                "avg_response_time": stats.get("avg_response_time", 0.0),
                "weight_changes": stats.get("weight_changes", []),
            },
        }

    def get_system_health_indicators(self) -> Dict[str, Any]:
        """Get system health indicators based on error patterns"""
        current_time = datetime.now()

        # Analyze recent error history
        recent_errors = [
            entry
            for entry in self.error_history
            if (
                current_time - datetime.fromisoformat(entry["timestamp"])
            ).total_seconds()
            < 3600
        ]

        # Calculate error rates by category
        category_counts = defaultdict(int)
        severity_counts = defaultdict(int)

        for entry in recent_errors:
            pattern = self.library.get_pattern(entry["pattern_id"])
            if pattern:
                category_counts[pattern.category] += 1
                severity_counts[pattern.severity] += 1

        # Determine health status
        critical_count = severity_counts.get("critical", 0)
        error_count = severity_counts.get("error", 0)
        total_errors = len(recent_errors)

        if critical_count > 5 or total_errors > 50:
            health_status = "critical"
        elif critical_count > 2 or error_count > 20:
            health_status = "warning"
        elif total_errors > 10:
            health_status = "degraded"
        else:
            health_status = "healthy"

        return {
            "health_status": health_status,
            "total_errors_last_hour": total_errors,
            "error_rate_per_minute": total_errors / 60,
            "category_breakdown": dict(category_counts),
            "severity_breakdown": dict(severity_counts),
            "active_scenarios": list(self.active_scenarios.keys()),
            "recommendations": self._generate_health_recommendations(
                health_status, category_counts, severity_counts
            ),
        }

    def _generate_health_recommendations(
        self,
        health_status: str,
        category_counts: Dict[str, int],
        severity_counts: Dict[str, int],
    ) -> List[str]:
        """Generate health recommendations based on error patterns"""
        recommendations = []

        if health_status == "critical":
            recommendations.append(
                "Immediate attention required - multiple critical errors detected"
            )

        if severity_counts.get("critical", 0) > 3:
            recommendations.append("Investigate critical system issues immediately")

        # Category-specific recommendations
        if category_counts.get("database", 0) > 10:
            recommendations.append(
                "Database performance issues detected - check connections and queries"
            )

        if category_counts.get("web_server", 0) > 15:
            recommendations.append(
                "Web server issues detected - check upstream services and load"
            )

        if category_counts.get("system", 0) > 8:
            recommendations.append(
                "System resource issues detected - check disk space and memory"
            )

        if not recommendations:
            recommendations.append("System appears healthy - continue monitoring")

        return recommendations

    def export_configuration(self, file_path: str) -> bool:
        """Export complete error management configuration"""
        try:
            config = {
                "frequency_config": asdict(self.frequency_config),
                "scenarios": {
                    name: asdict(scenario) for name, scenario in self.scenarios.items()
                },
                "pattern_stats": dict(self.pattern_stats),
                "exported_at": datetime.now().isoformat(),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def _save_scenario(self, scenario: ErrorScenario) -> bool:
        """Save scenario to file"""
        try:
            scenario_file = self.scenarios_dir / f"{scenario.name}.json"
            with open(scenario_file, "w", encoding="utf-8") as f:
                json.dump(asdict(scenario), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
