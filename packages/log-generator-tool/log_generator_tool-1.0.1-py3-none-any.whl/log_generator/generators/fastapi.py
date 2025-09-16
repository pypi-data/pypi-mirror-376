"""
FastAPI application log generator.

This module implements a log generator that produces realistic FastAPI application logs
including request/response logs, error logs, and various log levels with realistic
API endpoint patterns and response times.
"""

import json
import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from faker import Faker

from ..core.interfaces import LogGenerator
from ..core.models import LogEntry


class FastAPILogGenerator(LogGenerator):
    """
    Generates FastAPI application logs with realistic patterns.

    Produces logs that mimic real FastAPI applications including:
    - Request/response logs with timing information
    - Error logs with stack traces
    - Authentication and authorization logs
    - Database query logs
    - Various log levels (INFO, DEBUG, WARNING, ERROR)
    """

    # Log levels with realistic distribution
    LOG_LEVELS = {"INFO": 0.60, "DEBUG": 0.20, "WARNING": 0.15, "ERROR": 0.05}

    # Common FastAPI endpoints with realistic patterns
    API_ENDPOINTS = [
        "/api/v1/users",
        "/api/v1/users/{user_id}",
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/refresh",
        "/api/v1/products",
        "/api/v1/products/{product_id}",
        "/api/v1/orders",
        "/api/v1/orders/{order_id}",
        "/api/v1/health",
        "/api/v1/metrics",
        "/docs",
        "/openapi.json",
        "/api/v1/search",
        "/api/v1/categories",
        "/api/v1/upload",
        "/api/v1/download/{file_id}",
    ]

    # HTTP methods with distribution
    HTTP_METHODS = {
        "GET": 0.60,
        "POST": 0.20,
        "PUT": 0.10,
        "DELETE": 0.05,
        "PATCH": 0.03,
        "OPTIONS": 0.02,
    }

    # HTTP status codes with realistic distribution for APIs
    STATUS_CODES = {
        200: 0.65,  # OK
        201: 0.10,  # Created
        400: 0.08,  # Bad Request
        401: 0.05,  # Unauthorized
        404: 0.05,  # Not Found
        422: 0.03,  # Unprocessable Entity
        500: 0.02,  # Internal Server Error
        403: 0.01,  # Forbidden
        429: 0.01,  # Too Many Requests
    }

    # Common log message patterns by level
    LOG_PATTERNS = {
        "INFO": [
            "Request completed: {method} {endpoint} - {status_code} - {response_time}ms",
            "User {user_id} authenticated successfully",
            "Database query executed: {query_type} - {duration}ms",
            "Cache hit for key: {cache_key}",
            "File uploaded: {filename} ({file_size} bytes)",
            "Email sent to {email}",
            "Background task started: {task_name}",
            "API rate limit check passed for IP {ip}",
            "Health check passed - all services operational",
            "Metrics collected: {metric_count} data points",
        ],
        "DEBUG": [
            "Request headers: {headers}",
            "Request body: {request_body}",
            "Response body: {response_body}",
            "SQL query: {sql_query}",
            "Cache miss for key: {cache_key}",
            "Validation passed for field: {field_name}",
            "JWT token decoded successfully",
            "Database connection acquired from pool",
            "Middleware processing: {middleware_name}",
            "Template rendered: {template_name}",
        ],
        "WARNING": [
            "Slow query detected: {query} took {duration}ms",
            "High memory usage: {memory_usage}MB",
            "Rate limit approaching for IP {ip}: {current_requests}/{limit}",
            "Deprecated endpoint accessed: {endpoint}",
            "Large request body: {size}MB",
            "Cache eviction: {evicted_keys} keys removed",
            "Connection pool near capacity: {active}/{max_connections}",
            "Retry attempt {attempt}/{max_attempts} for {operation}",
            "File size exceeds recommended limit: {file_size}MB",
            "API version {version} will be deprecated on {date}",
        ],
        "ERROR": [
            "Database connection failed: {error}",
            "Authentication failed for user {user_id}: {reason}",
            "Validation error: {field} - {error_message}",
            "External API call failed: {api_url} - {error}",
            "File processing error: {filename} - {error}",
            "Payment processing failed: order {order_id} - {error}",
            "Email delivery failed: {email} - {error}",
            "Background task failed: {task_name} - {error}",
            "Rate limit exceeded for IP {ip}",
            "Internal server error: {error_message}",
        ],
    }

    # Common error messages for different scenarios
    ERROR_MESSAGES = [
        "Connection timeout",
        "Invalid JSON format",
        "Missing required field",
        "Unauthorized access",
        "Resource not found",
        "Duplicate entry",
        "Validation failed",
        "Service unavailable",
        "Rate limit exceeded",
        "Internal processing error",
    ]

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize FastAPI log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Override defaults with custom config
        if "log_levels" in self.custom_config:
            self.LOG_LEVELS = self.custom_config["log_levels"]
        if "endpoints" in self.custom_config:
            self.API_ENDPOINTS = self.custom_config["endpoints"]
        if "status_codes" in self.custom_config:
            self.STATUS_CODES = self.custom_config["status_codes"]

    def generate_log(self) -> str:
        """
        Generate a single FastAPI log entry.

        Returns:
            str: Formatted FastAPI log entry
        """
        return self.generate_log_with_time(datetime.now())

    def generate_log_with_time(self, timestamp: datetime) -> str:
        """
        Generate a FastAPI log entry with a specific timestamp.

        Args:
            timestamp: The timestamp to use for the log entry

        Returns:
            str: Formatted FastAPI log entry with specified timestamp
        """
        level = self._weighted_choice(self.LOG_LEVELS)
        formatted_timestamp = self._format_timestamp(timestamp)

        # Generate request ID for tracing
        request_id = self.faker.uuid4()[:8]

        # Choose log type based on level
        if level == "INFO" and random.random() < 0.7:
            # Request/response log
            log_message = self._generate_request_log()
        else:
            # General application log
            log_message = self._generate_application_log(level)

        # FastAPI log format: timestamp [level] request_id: message
        log_entry = f"{formatted_timestamp} [{level}] {request_id}: {log_message}"

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for FastAPI logs.

        Returns:
            str: Regular expression pattern
        """
        # Pattern for FastAPI log format - flexible to handle various request ID formats
        return (
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) "
            r"\[(\w+)\] ([a-zA-Z0-9]{8}): (.*)$"
        )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches FastAPI log format.

        Args:
            log_entry (str): Log entry to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pattern = self.get_log_pattern()
        return bool(re.match(pattern, log_entry))

    def set_custom_fields(self, fields: Dict[str, Any]) -> None:
        """
        Set custom fields for log generation.

        Args:
            fields (Dict[str, Any]): Custom field definitions
        """
        self.custom_config.update(fields)

        if "log_levels" in fields:
            self.LOG_LEVELS = fields["log_levels"]
        if "endpoints" in fields:
            self.API_ENDPOINTS = fields["endpoints"]
        if "status_codes" in fields:
            self.STATUS_CODES = fields["status_codes"]

    def _generate_timestamp(self) -> str:
        """Generate timestamp in FastAPI log format."""
        now = datetime.now()
        return self._format_timestamp(now)

    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format a specific timestamp in FastAPI log format."""
        return timestamp.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]  # Milliseconds

    def _generate_request_log(self) -> str:
        """Generate request/response log message."""
        method = self._weighted_choice(self.HTTP_METHODS)
        endpoint = self._generate_endpoint()
        status_code = self._weighted_choice(self.STATUS_CODES)
        response_time = self._generate_response_time(status_code)

        return f"Request completed: {method} {endpoint} - {status_code} - {response_time}ms"

    def _generate_application_log(self, level: str) -> str:
        """Generate application-specific log message."""
        patterns = self.LOG_PATTERNS.get(level, ["Generic {level} message"])
        pattern = random.choice(patterns)

        # Fill in template variables
        variables = {
            "method": self._weighted_choice(self.HTTP_METHODS),
            "endpoint": self._generate_endpoint(),
            "status_code": self._weighted_choice(self.STATUS_CODES),
            "response_time": self._generate_response_time(),
            "user_id": random.randint(1000, 99999),
            "query_type": random.choice(["SELECT", "INSERT", "UPDATE", "DELETE"]),
            "duration": random.randint(1, 1000),
            "cache_key": f"user:{random.randint(1000, 99999)}:profile",
            "filename": self.faker.file_name(),
            "file_size": random.randint(1024, 10485760),  # 1KB to 10MB
            "email": self.faker.email(),
            "task_name": random.choice(
                ["send_email", "process_payment", "generate_report", "backup_data"]
            ),
            "ip": self.faker.ipv4(),
            "metric_count": random.randint(100, 10000),
            "headers": json.dumps(
                {"User-Agent": "FastAPI-Client/1.0", "Content-Type": "application/json"}
            ),
            "request_body": json.dumps(
                {"user_id": random.randint(1000, 99999), "action": "update"}
            ),
            "response_body": json.dumps(
                {"status": "success", "data": {"id": random.randint(1, 1000)}}
            ),
            "sql_query": f"SELECT * FROM users WHERE id = {random.randint(1, 1000)}",
            "field_name": random.choice(["email", "password", "username", "phone"]),
            "field": random.choice(["email", "password", "username", "phone"]),
            "middleware_name": random.choice(
                ["AuthMiddleware", "CORSMiddleware", "RateLimitMiddleware"]
            ),
            "template_name": random.choice(
                ["user_profile.html", "dashboard.html", "email_template.html"]
            ),
            "query": f"SELECT * FROM orders WHERE created_at > '{self.faker.date()}'",
            "memory_usage": random.randint(100, 2048),
            "current_requests": random.randint(80, 95),
            "limit": 100,
            "size": round(random.uniform(5.0, 50.0), 2),
            "evicted_keys": random.randint(10, 100),
            "active": random.randint(18, 20),
            "max_connections": 20,
            "attempt": random.randint(1, 3),
            "max_attempts": 3,
            "operation": random.choice(["database_query", "api_call", "file_upload"]),
            "version": f"v{random.randint(1, 3)}",
            "date": self.faker.future_date(),
            "error": random.choice(self.ERROR_MESSAGES),
            "reason": random.choice(
                ["invalid_credentials", "account_locked", "token_expired"]
            ),
            "error_message": random.choice(self.ERROR_MESSAGES),
            "api_url": f"https://{self.faker.domain_name()}/api/v1/data",
            "order_id": f"ORD-{random.randint(100000, 999999)}",
            "level": level.lower(),
        }

        try:
            return pattern.format(**variables)
        except KeyError:
            # If template variable not found, return pattern as-is
            return pattern

    def _generate_endpoint(self) -> str:
        """Generate realistic API endpoint."""
        if random.random() < 0.8:
            endpoint = random.choice(self.API_ENDPOINTS)
            # Replace path parameters with actual values
            if "{user_id}" in endpoint:
                endpoint = endpoint.replace(
                    "{user_id}", str(random.randint(1000, 99999))
                )
            if "{product_id}" in endpoint:
                endpoint = endpoint.replace(
                    "{product_id}", str(random.randint(1, 10000))
                )
            if "{order_id}" in endpoint:
                endpoint = endpoint.replace(
                    "{order_id}", f"ORD-{random.randint(100000, 999999)}"
                )
            if "{file_id}" in endpoint:
                endpoint = endpoint.replace("{file_id}", self.faker.uuid4()[:8])
            return endpoint
        else:
            # Generate dynamic endpoints
            dynamic_endpoints = [
                f"/api/v1/users/{random.randint(1000, 99999)}/orders",
                f"/api/v1/search?q={self.faker.word()}",
                f"/api/v1/categories/{self.faker.slug()}",
                f"/api/v1/reports/{self.faker.date()}",
            ]
            return random.choice(dynamic_endpoints)

    def _generate_response_time(self, status_code: Optional[int] = None) -> int:
        """Generate realistic response time based on status code."""
        if status_code:
            if status_code >= 500:
                # Server errors tend to be slower or timeout
                return random.randint(2000, 30000)
            elif status_code == 404:
                # Not found is usually fast
                return random.randint(10, 100)
            elif status_code in [400, 401, 403, 422]:
                # Client errors are usually fast
                return random.randint(20, 200)
            else:
                # Success responses
                return random.randint(50, 1500)
        else:
            # General response time
            return random.randint(10, 2000)

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]
