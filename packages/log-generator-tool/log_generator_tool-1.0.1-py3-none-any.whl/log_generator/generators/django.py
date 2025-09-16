"""
Django log generators for application and database logs.

This module implements log generators that produce realistic Django application logs
including request logs, SQL query logs, and error logs following Django's standard
logging format.
"""

import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from faker import Faker

from ..core.interfaces import LogGenerator
from ..core.models import LogEntry


class DjangoRequestLogGenerator(LogGenerator):
    """
    Generates Django request logs with realistic patterns.

    Produces logs similar to Django's default request logging including
    HTTP methods, URLs, status codes, and response times.
    """

    # HTTP methods with realistic distribution for Django apps
    HTTP_METHODS = {
        "GET": 0.65,
        "POST": 0.25,
        "PUT": 0.04,
        "DELETE": 0.03,
        "PATCH": 0.02,
        "HEAD": 0.01,
    }

    # HTTP status codes with realistic distribution
    STATUS_CODES = {
        200: 0.70,
        404: 0.12,
        302: 0.08,
        500: 0.03,
        403: 0.02,
        400: 0.02,
        401: 0.02,
        301: 0.01,
    }

    # Common Django URL patterns
    URL_PATTERNS = [
        "/",
        "/admin/",
        "/admin/login/",
        "/admin/logout/",
        "/api/users/",
        "/api/auth/login/",
        "/api/auth/logout/",
        "/accounts/login/",
        "/accounts/logout/",
        "/accounts/profile/",
        "/static/admin/css/base.css",
        "/static/admin/js/admin.js",
        "/media/uploads/image.jpg",
        "/favicon.ico",
        "/robots.txt",
    ]

    # Django log levels
    LOG_LEVELS = {
        "INFO": 0.60,
        "WARNING": 0.25,
        "ERROR": 0.10,
        "DEBUG": 0.04,
        "CRITICAL": 0.01,
    }

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Django request log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Override defaults with custom config
        if "status_codes" in self.custom_config:
            self.STATUS_CODES = self.custom_config["status_codes"]
        if "url_patterns" in self.custom_config:
            self.URL_PATTERNS = self.custom_config["url_patterns"]
        if "log_levels" in self.custom_config:
            self.LOG_LEVELS = self.custom_config["log_levels"]

    def generate_log(self) -> str:
        """
        Generate a single Django request log entry.

        Returns:
            str: Formatted Django request log entry
        """
        timestamp = self._generate_timestamp()
        level = self._weighted_choice(self.LOG_LEVELS)
        logger_name = "django.request"

        method = self._weighted_choice(self.HTTP_METHODS)
        url = self._generate_url()
        status_code = self._weighted_choice(self.STATUS_CODES)
        response_time = self._generate_response_time()
        user = self._generate_user()
        ip_address = self._generate_ip_address()

        # Django request log format
        if level == "ERROR":
            log_entry = (
                f"{timestamp} {level} {logger_name}: Internal Server Error: {url}\n"
                f"Traceback (most recent call last):\n"
                f'  File "/app/views.py", line {random.randint(10, 200)}, in {self.faker.word()}\n'
                f"    {self._generate_error_line()}\n"
                f"{self._generate_exception()}"
            )
        else:
            log_entry = (
                f"{timestamp} {level} {logger_name}: "
                f'"{method} {url}" {status_code} [{response_time}ms] '
                f"(user: {user}, ip: {ip_address})"
            )

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for Django request logs.

        Returns:
            str: Regular expression pattern
        """
        return (
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) "
            r"(\w+) ([\w\.]+): "
            r'"([A-Z]+) ([^"]+)" (\d+) \[(\d+)ms\] '
            r"\(user: ([^,]+), ip: ([\d\.]+)\)$"
        )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches Django request log format.

        Args:
            log_entry (str): Log entry to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pattern = self.get_log_pattern()
        return bool(re.match(pattern, log_entry.split("\n")[0]))

    def set_custom_fields(self, fields: Dict[str, Any]) -> None:
        """
        Set custom fields for log generation.

        Args:
            fields (Dict[str, Any]): Custom field definitions
        """
        self.custom_config.update(fields)

        if "status_codes" in fields:
            self.STATUS_CODES = fields["status_codes"]
        if "url_patterns" in fields:
            self.URL_PATTERNS = fields["url_patterns"]
        if "log_levels" in fields:
            self.LOG_LEVELS = fields["log_levels"]

    def _generate_timestamp(self) -> str:
        """Generate timestamp in Django format."""
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S,%f")[
            :-3
        ]  # Remove last 3 digits from microseconds

    def _generate_url(self) -> str:
        """Generate realistic Django URL."""
        if random.random() < 0.8:
            return random.choice(self.URL_PATTERNS)
        else:
            # Generate dynamic URLs
            dynamic_patterns = [
                f"/api/users/{self.faker.random_int(1, 10000)}/",
                f"/blog/{self.faker.slug()}/",
                f"/products/{self.faker.random_int(1, 1000)}/",
                f"/admin/{self.faker.word()}/{self.faker.random_int(1, 100)}/change/",
                f"/search/?q={self.faker.word()}",
                f"/category/{self.faker.word()}/",
            ]
            return random.choice(dynamic_patterns)

    def _generate_response_time(self) -> int:
        """Generate realistic response time in milliseconds."""
        # Most requests are fast, some are slower
        if random.random() < 0.8:
            return random.randint(10, 200)
        elif random.random() < 0.95:
            return random.randint(200, 1000)
        else:
            return random.randint(1000, 5000)

    def _generate_user(self) -> str:
        """Generate user information."""
        if random.random() < 0.7:
            return "AnonymousUser"
        else:
            return self.faker.user_name()

    def _generate_ip_address(self) -> str:
        """Generate realistic IP address."""
        if random.random() < 0.6:
            return self.faker.ipv4_private()
        else:
            return self.faker.ipv4_public()

    def _generate_error_line(self) -> str:
        """Generate realistic Python error line."""
        error_lines = [
            "return self.get_object().name",
            "user = User.objects.get(id=user_id)",
            "result = some_function(param)",
            "data = json.loads(request.body)",
            "return render(request, template_name, context)",
        ]
        return random.choice(error_lines)

    def _generate_exception(self) -> str:
        """Generate realistic Django exception."""
        exceptions = [
            "DoesNotExist: User matching query does not exist.",
            "ValueError: invalid literal for int() with base 10: 'abc'",
            "KeyError: 'required_field'",
            "AttributeError: 'NoneType' object has no attribute 'name'",
            "ValidationError: This field is required.",
            "PermissionDenied: You do not have permission to perform this action.",
        ]
        return random.choice(exceptions)

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]


class DjangoSQLLogGenerator(LogGenerator):
    """
    Generates Django SQL query logs with realistic database operations.

    Produces logs similar to Django's SQL query logging including
    query types, execution times, and SQL statements.
    """

    # SQL query types with distribution
    QUERY_TYPES = {"SELECT": 0.70, "INSERT": 0.15, "UPDATE": 0.10, "DELETE": 0.05}

    # Common Django model operations
    DJANGO_MODELS = [
        "User",
        "Group",
        "Permission",
        "Session",
        "ContentType",
        "LogEntry",
        "Product",
        "Order",
        "Category",
        "Article",
        "Comment",
    ]

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Django SQL log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        if "models" in self.custom_config:
            self.DJANGO_MODELS = self.custom_config["models"]

    def generate_log(self) -> str:
        """
        Generate a single Django SQL log entry.

        Returns:
            str: Formatted Django SQL log entry
        """
        timestamp = self._generate_timestamp()
        level = "DEBUG"
        logger_name = "django.db.backends"

        query_type = self._weighted_choice(self.QUERY_TYPES)
        sql_query = self._generate_sql_query(query_type)
        execution_time = self._generate_execution_time()

        # Django SQL log format
        log_entry = (
            f"{timestamp} {level} {logger_name}: "
            f"({execution_time}) {sql_query}; args={self._generate_sql_args(query_type)}"
        )

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for Django SQL logs.

        Returns:
            str: Regular expression pattern
        """
        return (
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) "
            r"(\w+) ([\w\.]+): "
            r"\(([0-9.]+)\) (.+); args=(.+)$"
        )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches Django SQL log format.

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

        if "models" in fields:
            self.DJANGO_MODELS = fields["models"]

    def _generate_timestamp(self) -> str:
        """Generate timestamp in Django format."""
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

    def _generate_sql_query(self, query_type: str) -> str:
        """Generate realistic SQL query based on type."""
        model = random.choice(self.DJANGO_MODELS)
        table_name = f"app_{model.lower()}"

        if query_type == "SELECT":
            if random.random() < 0.3:
                # Simple select
                return f'SELECT * FROM "{table_name}" WHERE "id" = %s'
            elif random.random() < 0.6:
                # Select with conditions
                return f'SELECT "id", "name", "created_at" FROM "{table_name}" WHERE "active" = %s ORDER BY "created_at" DESC'
            else:
                # Join query
                return f'SELECT * FROM "{table_name}" INNER JOIN "app_category" ON ("{table_name}"."category_id" = "app_category"."id") WHERE "app_category"."name" = %s'

        elif query_type == "INSERT":
            return f'INSERT INTO "{table_name}" ("name", "email", "created_at") VALUES (%s, %s, %s)'

        elif query_type == "UPDATE":
            return f'UPDATE "{table_name}" SET "name" = %s, "updated_at" = %s WHERE "id" = %s'

        elif query_type == "DELETE":
            return f'DELETE FROM "{table_name}" WHERE "id" = %s'

        return f'SELECT * FROM "{table_name}"'

    def _generate_sql_args(self, query_type: str) -> str:
        """Generate realistic SQL arguments."""
        if query_type == "SELECT":
            if random.random() < 0.5:
                return f"({self.faker.random_int(1, 10000)},)"
            else:
                return f"(True,)"

        elif query_type == "INSERT":
            return f"('{self.faker.name()}', '{self.faker.email()}', '{datetime.now().isoformat()}')"

        elif query_type == "UPDATE":
            return f"('{self.faker.name()}', '{datetime.now().isoformat()}', {self.faker.random_int(1, 10000)})"

        elif query_type == "DELETE":
            return f"({self.faker.random_int(1, 10000)},)"

        return "()"

    def _generate_execution_time(self) -> str:
        """Generate realistic SQL execution time."""
        # Most queries are fast, some are slower
        if random.random() < 0.8:
            return f"{random.uniform(0.001, 0.050):.3f}"
        elif random.random() < 0.95:
            return f"{random.uniform(0.050, 0.500):.3f}"
        else:
            return f"{random.uniform(0.500, 2.000):.3f}"

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]
