"""
Pattern manager for storing and managing custom log patterns.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .template_parser import TemplateParser


@dataclass
class LogPattern:
    """Represents a custom log pattern"""

    name: str
    template: str
    description: str
    category: str
    fields: Dict[str, Any]
    sample_output: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PatternManager:
    """
    Manages custom log patterns including storage, validation, and retrieval.
    """

    def __init__(self, patterns_dir: str = "patterns"):
        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(exist_ok=True)
        self.patterns: Dict[str, LogPattern] = {}
        self.parser = TemplateParser()
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load patterns from storage directory"""
        pattern_files = list(self.patterns_dir.glob("*.json")) + list(
            self.patterns_dir.glob("*.yaml")
        )

        for pattern_file in pattern_files:
            try:
                if pattern_file.suffix == ".json":
                    with open(pattern_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:  # .yaml
                    with open(pattern_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                if isinstance(data, dict) and "patterns" in data:
                    # Multiple patterns in one file
                    for pattern_data in data["patterns"]:
                        pattern = LogPattern(**pattern_data)
                        self.patterns[pattern.name] = pattern
                elif isinstance(data, dict):
                    # Single pattern
                    pattern = LogPattern(**data)
                    self.patterns[pattern.name] = pattern

            except Exception as e:
                print(f"Warning: Failed to load pattern from {pattern_file}: {e}")

    def add_pattern(self, pattern: LogPattern) -> bool:
        """
        Add a new pattern.

        Args:
            pattern: LogPattern to add

        Returns:
            True if pattern was added successfully
        """
        # Validate pattern template
        validation = self.parser.validate_template(pattern.template)
        if not validation["valid"]:
            raise ValueError(f"Invalid pattern template: {validation['errors']}")

        # Generate sample output
        pattern.sample_output = self.parser.generate_log(pattern.template)

        # Add timestamp
        from datetime import datetime

        now = datetime.now().isoformat()
        if not pattern.created_at:
            pattern.created_at = now
        pattern.updated_at = now

        # Store pattern
        self.patterns[pattern.name] = pattern
        return self._save_pattern(pattern)

    def update_pattern(self, name: str, **kwargs) -> bool:
        """
        Update an existing pattern.

        Args:
            name: Pattern name to update
            **kwargs: Fields to update

        Returns:
            True if pattern was updated successfully
        """
        if name not in self.patterns:
            raise KeyError(f"Pattern '{name}' not found")

        pattern = self.patterns[name]

        # Update fields
        for key, value in kwargs.items():
            if hasattr(pattern, key):
                setattr(pattern, key, value)

        # Re-validate if template was changed
        if "template" in kwargs:
            validation = self.parser.validate_template(pattern.template)
            if not validation["valid"]:
                raise ValueError(f"Invalid pattern template: {validation['errors']}")
            pattern.sample_output = self.parser.generate_log(pattern.template)

        # Update timestamp
        from datetime import datetime

        pattern.updated_at = datetime.now().isoformat()

        return self._save_pattern(pattern)

    def remove_pattern(self, name: str) -> bool:
        """
        Remove a pattern.

        Args:
            name: Pattern name to remove

        Returns:
            True if pattern was removed successfully
        """
        if name not in self.patterns:
            return False

        del self.patterns[name]

        # Remove file
        pattern_file = self.patterns_dir / f"{name}.json"
        if pattern_file.exists():
            pattern_file.unlink()
            return True

        return False

    def get_pattern(self, name: str) -> Optional[LogPattern]:
        """Get a pattern by name"""
        return self.patterns.get(name)

    def list_patterns(self, category: Optional[str] = None) -> List[LogPattern]:
        """
        List all patterns, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of patterns
        """
        patterns = list(self.patterns.values())

        if category:
            patterns = [p for p in patterns if p.category == category]

        return sorted(patterns, key=lambda p: p.name)

    def get_categories(self) -> List[str]:
        """Get list of all pattern categories"""
        categories = set(pattern.category for pattern in self.patterns.values())
        return sorted(list(categories))

    def generate_log_from_pattern(
        self, pattern_name: str, custom_values: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate a log entry from a named pattern.

        Args:
            pattern_name: Name of the pattern to use
            custom_values: Optional custom field values

        Returns:
            Generated log string
        """
        pattern = self.get_pattern(pattern_name)
        if not pattern:
            raise KeyError(f"Pattern '{pattern_name}' not found")

        return self.parser.generate_log(pattern.template, custom_values)

    def validate_pattern(self, pattern: LogPattern) -> Dict[str, Any]:
        """
        Validate a pattern.

        Args:
            pattern: Pattern to validate

        Returns:
            Validation results
        """
        return self.parser.validate_template(pattern.template)

    def _save_pattern(self, pattern: LogPattern) -> bool:
        """Save pattern to file"""
        try:
            pattern_file = self.patterns_dir / f"{pattern.name}.json"
            with open(pattern_file, "w", encoding="utf-8") as f:
                json.dump(asdict(pattern), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def export_patterns(self, file_path: str, format_type: str = "json") -> bool:
        """
        Export all patterns to a file.

        Args:
            file_path: Output file path
            format_type: Export format ('json' or 'yaml')

        Returns:
            True if export was successful
        """
        try:
            data = {"patterns": [asdict(pattern) for pattern in self.patterns.values()]}

            with open(file_path, "w", encoding="utf-8") as f:
                if format_type.lower() == "yaml":
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def import_patterns(self, file_path: str) -> int:
        """
        Import patterns from a file.

        Args:
            file_path: Input file path

        Returns:
            Number of patterns imported
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            imported_count = 0

            if isinstance(data, dict) and "patterns" in data:
                for pattern_data in data["patterns"]:
                    try:
                        pattern = LogPattern(**pattern_data)
                        self.add_pattern(pattern)
                        imported_count += 1
                    except Exception as e:
                        print(
                            f"Warning: Failed to import pattern {pattern_data.get('name', 'unknown')}: {e}"
                        )

            return imported_count
        except Exception:
            return 0

    def create_sample_patterns(self) -> None:
        """Create some sample patterns for demonstration"""
        sample_patterns = [
            LogPattern(
                name="nginx_custom",
                template="{timestamp} [{level}] {pid}#{tid}: *{connection_id} {message}, client: {ip_address}, server: {server_name}",
                description="Custom nginx error log pattern",
                category="web_server",
                fields={
                    "level": {"type": "choice", "options": ["error", "warn", "info"]},
                    "pid": {
                        "type": "random_int",
                        "options": {"min_val": 1000, "max_val": 9999},
                    },
                    "tid": {
                        "type": "random_int",
                        "options": {"min_val": 0, "max_val": 99},
                    },
                    "connection_id": {"type": "counter"},
                    "message": {
                        "type": "choice",
                        "options": ["connection refused", "timeout", "file not found"],
                    },
                    "ip_address": {
                        "type": "choice",
                        "options": ["192.168.1.100", "10.0.0.50", "172.16.0.10"],
                    },
                    "server_name": {
                        "type": "choice",
                        "options": [
                            "example.com",
                            "api.example.com",
                            "www.example.com",
                        ],
                    },
                },
            ),
            LogPattern(
                name="api_request",
                template="{iso_timestamp} [INFO] API Request: {method} {endpoint} - Status: {status_code} - Response Time: {response_time}ms - User: {user_id}",
                description="API request log pattern",
                category="application",
                fields={
                    "method": {
                        "type": "choice",
                        "options": ["GET", "POST", "PUT", "DELETE"],
                    },
                    "endpoint": {
                        "type": "choice",
                        "options": [
                            "/api/users",
                            "/api/orders",
                            "/api/products",
                            "/health",
                        ],
                    },
                    "status_code": {
                        "type": "choice",
                        "options": ["200", "201", "400", "404", "500"],
                    },
                    "response_time": {
                        "type": "random_float",
                        "options": {"min_val": 10, "max_val": 2000},
                    },
                    "user_id": {"type": "uuid"},
                },
            ),
            LogPattern(
                name="database_query",
                template="{timestamp} [SQL] Duration: {duration}ms Query: {query} Rows: {rows_affected}",
                description="Database query log pattern",
                category="database",
                fields={
                    "duration": {
                        "type": "random_float",
                        "options": {"min_val": 0.1, "max_val": 500},
                    },
                    "query": {
                        "type": "choice",
                        "options": [
                            "SELECT * FROM users",
                            "INSERT INTO orders",
                            "UPDATE products",
                            "DELETE FROM cache",
                        ],
                    },
                    "rows_affected": {
                        "type": "random_int",
                        "options": {"min_val": 0, "max_val": 1000},
                    },
                },
            ),
        ]

        for pattern in sample_patterns:
            try:
                self.add_pattern(pattern)
            except Exception as e:
                print(f"Warning: Failed to create sample pattern {pattern.name}: {e}")
