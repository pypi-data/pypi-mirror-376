"""
Error pattern library for realistic error log generation.
"""

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ErrorPattern:
    """Represents an error pattern with metadata"""

    id: str
    category: str  # web_server, application, system, database
    severity: str  # critical, error, warning, info
    message_template: str
    description: str
    frequency_weight: float = (
        1.0  # Relative frequency (1.0 = normal, 0.1 = rare, 5.0 = common)
    )
    context_fields: Dict[str, Any] = None
    real_world_examples: List[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.context_fields is None:
            self.context_fields = {}
        if self.real_world_examples is None:
            self.real_world_examples = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class ErrorPatternLibrary:
    """
    Manages error patterns for realistic error log generation.
    Provides categorized error patterns based on real-world scenarios.
    """

    def __init__(self, patterns_dir: str = "error_patterns"):
        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(exist_ok=True)
        self.patterns: Dict[str, ErrorPattern] = {}
        self.categories: Dict[str, List[str]] = {}
        self._initialize_builtin_patterns()
        self._load_custom_patterns()

    def _initialize_builtin_patterns(self) -> None:
        """Initialize built-in error patterns based on real-world scenarios"""

        # Web Server Error Patterns (Nginx, Apache)
        web_server_patterns = [
            ErrorPattern(
                id="nginx_connection_refused",
                category="web_server",
                severity="error",
                message_template='connect() failed (111: Connection refused) while connecting to upstream, client: {client_ip}, server: {server_name}, request: "{method} {uri} HTTP/1.1", upstream: "{upstream}"',
                description="Nginx upstream connection refused error",
                frequency_weight=2.5,
                context_fields={
                    "client_ip": [
                        "192.168.1.100",
                        "10.0.0.50",
                        "172.16.0.10",
                        "203.0.113.45",
                    ],
                    "server_name": [
                        "api.example.com",
                        "www.example.com",
                        "backend.example.com",
                    ],
                    "method": ["GET", "POST", "PUT", "DELETE"],
                    "uri": [
                        "/api/users",
                        "/api/orders",
                        "/health",
                        "/metrics",
                        "/login",
                    ],
                    "upstream": [
                        "http://127.0.0.1:8000",
                        "http://127.0.0.1:3000",
                        "http://backend:8080",
                    ],
                },
                real_world_examples=[
                    'connect() failed (111: Connection refused) while connecting to upstream, client: 192.168.1.100, server: api.example.com, request: "GET /api/users HTTP/1.1", upstream: "http://127.0.0.1:8000"',
                    'connect() failed (111: Connection refused) while connecting to upstream, client: 10.0.0.50, server: www.example.com, request: "POST /login HTTP/1.1", upstream: "http://backend:8080"',
                ],
            ),
            ErrorPattern(
                id="nginx_timeout",
                category="web_server",
                severity="error",
                message_template='upstream timed out (110: Connection timed out) while reading response header from upstream, client: {client_ip}, server: {server_name}, request: "{method} {uri} HTTP/1.1", upstream: "{upstream}"',
                description="Nginx upstream timeout error",
                frequency_weight=1.8,
                context_fields={
                    "client_ip": ["192.168.1.100", "10.0.0.50", "172.16.0.10"],
                    "server_name": ["api.example.com", "www.example.com"],
                    "method": ["GET", "POST"],
                    "uri": ["/api/slow-endpoint", "/api/reports", "/api/analytics"],
                    "upstream": ["http://127.0.0.1:8000", "http://slow-service:8080"],
                },
            ),
            ErrorPattern(
                id="apache_file_not_found",
                category="web_server",
                severity="error",
                message_template="File does not exist: {document_root}{requested_file}",
                description="Apache file not found error",
                frequency_weight=3.2,
                context_fields={
                    "document_root": [
                        "/var/www/html/",
                        "/usr/share/nginx/html/",
                        "/opt/app/public/",
                    ],
                    "requested_file": [
                        "favicon.ico",
                        "robots.txt",
                        "sitemap.xml",
                        "old-page.html",
                        "missing-image.jpg",
                    ],
                },
            ),
            ErrorPattern(
                id="apache_permission_denied",
                category="web_server",
                severity="error",
                message_template="Permission denied: {user} cannot access {file_path}",
                description="Apache permission denied error",
                frequency_weight=1.2,
                context_fields={
                    "user": ["www-data", "apache", "nginx", "nobody"],
                    "file_path": [
                        "/var/log/app.log",
                        "/etc/ssl/private/cert.key",
                        "/var/www/.htaccess",
                    ],
                },
            ),
        ]

        # Application Error Patterns
        application_patterns = [
            ErrorPattern(
                id="fastapi_validation_error",
                category="application",
                severity="error",
                message_template="Validation error in {endpoint}: {field} field is {error_type}",
                description="FastAPI request validation error",
                frequency_weight=4.1,
                context_fields={
                    "endpoint": [
                        "/api/users",
                        "/api/orders",
                        "/api/products",
                        "/api/auth/login",
                    ],
                    "field": [
                        "email",
                        "password",
                        "user_id",
                        "amount",
                        "date",
                        "phone",
                    ],
                    "error_type": [
                        "required",
                        "invalid format",
                        "too short",
                        "too long",
                        "out of range",
                    ],
                },
            ),
            ErrorPattern(
                id="django_database_error",
                category="application",
                severity="error",
                message_template="Database error in {view}: {error_detail}",
                description="Django database connection error",
                frequency_weight=2.3,
                context_fields={
                    "view": [
                        "UserListView",
                        "OrderCreateView",
                        "ProductDetailView",
                        "AuthLoginView",
                    ],
                    "error_detail": [
                        "connection to database lost",
                        "table 'users' doesn't exist",
                        "duplicate key value violates unique constraint",
                        "column 'email' cannot be null",
                    ],
                },
            ),
            ErrorPattern(
                id="application_memory_error",
                category="application",
                severity="critical",
                message_template="OutOfMemoryError: Java heap space in {component} while processing {operation}",
                description="Application out of memory error",
                frequency_weight=0.8,
                context_fields={
                    "component": [
                        "UserService",
                        "OrderProcessor",
                        "ReportGenerator",
                        "DataImporter",
                    ],
                    "operation": [
                        "user data export",
                        "large report generation",
                        "bulk data import",
                        "image processing",
                    ],
                },
            ),
            ErrorPattern(
                id="api_rate_limit_exceeded",
                category="application",
                severity="warning",
                message_template="Rate limit exceeded for client {client_id}: {current_rate} requests/minute exceeds limit of {rate_limit}",
                description="API rate limiting error",
                frequency_weight=2.7,
                context_fields={
                    "client_id": [
                        "client_123",
                        "mobile_app",
                        "web_dashboard",
                        "api_user_456",
                    ],
                    "current_rate": ["150", "200", "350", "500"],
                    "rate_limit": ["100", "200", "300"],
                },
            ),
        ]

        # System Level Error Patterns
        system_patterns = [
            ErrorPattern(
                id="disk_space_full",
                category="system",
                severity="critical",
                message_template="No space left on device: {device} ({mount_point}) - {usage}% full",
                description="Disk space exhaustion error",
                frequency_weight=1.5,
                context_fields={
                    "device": ["/dev/sda1", "/dev/nvme0n1p1", "/dev/xvda1"],
                    "mount_point": ["/", "/var", "/tmp", "/home", "/var/log"],
                    "usage": ["98", "99", "100"],
                },
            ),
            ErrorPattern(
                id="memory_allocation_failed",
                category="system",
                severity="critical",
                message_template="Cannot allocate memory: {process} (PID {pid}) failed to allocate {size}MB",
                description="System memory allocation failure",
                frequency_weight=0.9,
                context_fields={
                    "process": ["java", "python", "node", "postgres", "redis"],
                    "pid": ["1234", "5678", "9012", "3456"],
                    "size": ["512", "1024", "2048", "4096"],
                },
            ),
            ErrorPattern(
                id="network_unreachable",
                category="system",
                severity="error",
                message_template="Network is unreachable: {destination} via {interface}",
                description="Network connectivity error",
                frequency_weight=1.7,
                context_fields={
                    "destination": [
                        "8.8.8.8",
                        "api.external-service.com",
                        "database.internal",
                        "cache.redis",
                    ],
                    "interface": ["eth0", "wlan0", "docker0", "br-123456"],
                },
            ),
            ErrorPattern(
                id="service_failed_to_start",
                category="system",
                severity="error",
                message_template="Failed to start {service}: {error_reason}",
                description="System service startup failure",
                frequency_weight=1.4,
                context_fields={
                    "service": ["nginx", "postgresql", "redis", "docker", "ssh"],
                    "error_reason": [
                        "port already in use",
                        "configuration file not found",
                        "insufficient permissions",
                        "dependency service not running",
                    ],
                },
            ),
        ]

        # Database Error Patterns
        database_patterns = [
            ErrorPattern(
                id="mysql_connection_lost",
                category="database",
                severity="error",
                message_template="MySQL server has gone away during query: {query_type} on table {table_name}",
                description="MySQL connection lost error",
                frequency_weight=2.1,
                context_fields={
                    "query_type": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                    "table_name": ["users", "orders", "products", "sessions", "logs"],
                },
            ),
            ErrorPattern(
                id="postgresql_deadlock",
                category="database",
                severity="error",
                message_template="Deadlock detected: Process {pid1} waits for {lock_type} on {resource}; blocked by process {pid2}",
                description="PostgreSQL deadlock error",
                frequency_weight=1.3,
                context_fields={
                    "pid1": ["12345", "23456", "34567"],
                    "pid2": ["54321", "65432", "76543"],
                    "lock_type": ["ShareLock", "ExclusiveLock", "RowExclusiveLock"],
                    "resource": [
                        "relation users",
                        "relation orders",
                        "tuple (1,5) of relation products",
                    ],
                },
            ),
            ErrorPattern(
                id="database_slow_query",
                category="database",
                severity="warning",
                message_template="Slow query detected: {duration}s - {query}",
                description="Database slow query warning",
                frequency_weight=3.5,
                context_fields={
                    "duration": ["5.234", "12.567", "25.891", "45.123"],
                    "query": [
                        "SELECT * FROM users WHERE created_at > '2023-01-01'",
                        "SELECT COUNT(*) FROM orders JOIN products ON orders.product_id = products.id",
                        "UPDATE users SET last_login = NOW() WHERE id IN (SELECT ...)",
                        "DELETE FROM logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)",
                    ],
                },
            ),
        ]

        # Add all patterns to the library
        all_patterns = (
            web_server_patterns
            + application_patterns
            + system_patterns
            + database_patterns
        )

        for pattern in all_patterns:
            self.patterns[pattern.id] = pattern

            # Organize by category
            if pattern.category not in self.categories:
                self.categories[pattern.category] = []
            self.categories[pattern.category].append(pattern.id)

    def _load_custom_patterns(self) -> None:
        """Load custom error patterns from files"""
        pattern_files = list(self.patterns_dir.glob("*.json"))

        for pattern_file in pattern_files:
            try:
                with open(pattern_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    # Multiple patterns in array
                    for pattern_data in data:
                        pattern = ErrorPattern(**pattern_data)
                        self.add_custom_pattern(pattern)
                elif isinstance(data, dict):
                    # Single pattern
                    pattern = ErrorPattern(**data)
                    self.add_custom_pattern(pattern)

            except Exception as e:
                print(
                    f"Warning: Failed to load custom error pattern from {pattern_file}: {e}"
                )

    def add_custom_pattern(self, pattern: ErrorPattern) -> bool:
        """
        Add a custom error pattern.

        Args:
            pattern: ErrorPattern to add

        Returns:
            True if pattern was added successfully
        """
        try:
            self.patterns[pattern.id] = pattern

            # Update category index
            if pattern.category not in self.categories:
                self.categories[pattern.category] = []
            if pattern.id not in self.categories[pattern.category]:
                self.categories[pattern.category].append(pattern.id)

            # Save to file
            return self._save_custom_pattern(pattern)
        except Exception:
            return False

    def update_pattern_weight(self, pattern_id: str, new_weight: float) -> bool:
        """
        Update the frequency weight of a pattern.

        Args:
            pattern_id: ID of the pattern to update
            new_weight: New frequency weight

        Returns:
            True if update was successful
        """
        if pattern_id not in self.patterns:
            return False

        self.patterns[pattern_id].frequency_weight = new_weight

        # Save if it's a custom pattern
        if self._is_custom_pattern(pattern_id):
            return self._save_custom_pattern(self.patterns[pattern_id])

        return True

    def get_pattern(self, pattern_id: str) -> Optional[ErrorPattern]:
        """Get an error pattern by ID"""
        return self.patterns.get(pattern_id)

    def get_patterns_by_category(self, category: str) -> List[ErrorPattern]:
        """Get all patterns in a specific category"""
        if category not in self.categories:
            return []

        return [self.patterns[pattern_id] for pattern_id in self.categories[category]]

    def get_patterns_by_severity(self, severity: str) -> List[ErrorPattern]:
        """Get all patterns with specific severity level"""
        return [
            pattern
            for pattern in self.patterns.values()
            if pattern.severity == severity
        ]

    def get_weighted_random_pattern(
        self, category: Optional[str] = None, severity: Optional[str] = None
    ) -> ErrorPattern:
        """
        Get a random error pattern based on frequency weights.

        Args:
            category: Optional category filter
            severity: Optional severity filter

        Returns:
            Randomly selected ErrorPattern based on weights
        """
        # Filter patterns
        candidates = list(self.patterns.values())

        if category:
            candidates = [p for p in candidates if p.category == category]

        if severity:
            candidates = [p for p in candidates if p.severity == severity]

        if not candidates:
            raise ValueError("No patterns match the specified criteria")

        # Create weighted selection
        weights = [pattern.frequency_weight for pattern in candidates]
        return random.choices(candidates, weights=weights, k=1)[0]

    def generate_error_message(
        self, pattern_id: str, custom_context: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate an error message from a pattern.

        Args:
            pattern_id: ID of the pattern to use
            custom_context: Optional custom context values

        Returns:
            Generated error message
        """
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            raise KeyError(f"Pattern '{pattern_id}' not found")

        # Prepare context values
        context = {}

        # Use pattern's context fields
        for field, options in pattern.context_fields.items():
            if isinstance(options, list):
                context[field] = random.choice(options)
            elif isinstance(options, dict):
                # Handle range-based generation
                if "min_val" in options and "max_val" in options:
                    context[field] = str(
                        random.randint(options["min_val"], options["max_val"])
                    )
                else:
                    context[field] = str(options.get("default", "unknown"))
            else:
                context[field] = str(options)

        # Override with custom context if provided
        if custom_context:
            context.update(custom_context)

        # Generate message
        try:
            return pattern.message_template.format(**context)
        except KeyError as e:
            # Handle missing context fields gracefully
            return (
                f"Error generating message for pattern {pattern_id}: missing field {e}"
            )

    def get_error_scenario(
        self, category: str, count: int = 5
    ) -> List[Tuple[str, str]]:
        """
        Generate a realistic error scenario with multiple related errors.

        Args:
            category: Error category to focus on
            count: Number of error messages to generate

        Returns:
            List of (pattern_id, error_message) tuples
        """
        patterns = self.get_patterns_by_category(category)
        if not patterns:
            return []

        scenario = []
        for _ in range(count):
            # Weight selection towards more common errors, but include some rare ones
            pattern = random.choices(
                patterns, weights=[p.frequency_weight for p in patterns], k=1
            )[0]

            message = self.generate_error_message(pattern.id)
            scenario.append((pattern.id, message))

        return scenario

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the error pattern library"""
        stats = {
            "total_patterns": len(self.patterns),
            "categories": {},
            "severity_distribution": {},
            "average_weight": 0.0,
        }

        # Category breakdown
        for category, pattern_ids in self.categories.items():
            stats["categories"][category] = len(pattern_ids)

        # Severity distribution
        for pattern in self.patterns.values():
            if pattern.severity not in stats["severity_distribution"]:
                stats["severity_distribution"][pattern.severity] = 0
            stats["severity_distribution"][pattern.severity] += 1

        # Average weight
        if self.patterns:
            stats["average_weight"] = sum(
                p.frequency_weight for p in self.patterns.values()
            ) / len(self.patterns)

        return stats

    def export_patterns(self, file_path: str) -> bool:
        """Export all patterns to a JSON file"""
        try:
            data = [asdict(pattern) for pattern in self.patterns.values()]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def _save_custom_pattern(self, pattern: ErrorPattern) -> bool:
        """Save a custom pattern to file"""
        try:
            pattern_file = self.patterns_dir / f"{pattern.id}.json"
            with open(pattern_file, "w", encoding="utf-8") as f:
                json.dump(asdict(pattern), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def _is_custom_pattern(self, pattern_id: str) -> bool:
        """Check if a pattern is custom (saved to file)"""
        pattern_file = self.patterns_dir / f"{pattern_id}.json"
        return pattern_file.exists()

    def list_categories(self) -> List[str]:
        """Get list of all available categories"""
        return sorted(list(self.categories.keys()))

    def list_severities(self) -> List[str]:
        """Get list of all available severity levels"""
        severities = set(pattern.severity for pattern in self.patterns.values())
        return sorted(list(severities))
