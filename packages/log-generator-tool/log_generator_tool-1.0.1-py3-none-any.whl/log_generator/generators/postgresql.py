"""
PostgreSQL log generators for database logs.

This module implements log generators that produce realistic PostgreSQL database logs
including query logs, error logs, and connection logs following PostgreSQL's
standard logging formats.
"""

import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from faker import Faker

from ..core.interfaces import LogGenerator
from ..core.models import LogEntry


class PostgreSQLLogGenerator(LogGenerator):
    """
    Generates PostgreSQL logs with realistic patterns.

    Produces logs similar to PostgreSQL's standard log format including
    connections, queries, errors, and administrative messages.
    """

    # Log levels with distribution
    LOG_LEVELS = {
        "LOG": 0.40,
        "INFO": 0.25,
        "WARNING": 0.20,
        "ERROR": 0.10,
        "FATAL": 0.03,
        "PANIC": 0.02,
    }

    # Query types with distribution
    QUERY_TYPES = {
        "SELECT": 0.55,
        "INSERT": 0.18,
        "UPDATE": 0.15,
        "DELETE": 0.07,
        "CREATE": 0.02,
        "DROP": 0.01,
        "ALTER": 0.02,
    }

    # Common PostgreSQL error codes
    ERROR_CODES = {
        "42P01": "relation does not exist",
        "42703": "column does not exist",
        "23505": "duplicate key value violates unique constraint",
        "23503": "foreign key constraint violation",
        "23502": "null value in column violates not-null constraint",
        "08006": "connection failure",
        "08003": "connection does not exist",
        "25P02": "current transaction is aborted",
        "40001": "serialization failure",
        "53300": "too many connections",
    }

    # Common table names
    TABLE_NAMES = [
        "users",
        "orders",
        "products",
        "categories",
        "sessions",
        "audit_log",
        "settings",
        "permissions",
        "roles",
        "articles",
    ]

    # Common column names
    COLUMN_NAMES = [
        "id",
        "name",
        "email",
        "password_hash",
        "created_at",
        "updated_at",
        "status",
        "type",
        "value",
        "description",
    ]

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize PostgreSQL log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Override defaults with custom config
        if "log_levels" in self.custom_config:
            self.LOG_LEVELS = self.custom_config["log_levels"]
        if "query_types" in self.custom_config:
            self.QUERY_TYPES = self.custom_config["query_types"]
        if "table_names" in self.custom_config:
            self.TABLE_NAMES = self.custom_config["table_names"]

    def generate_log(self) -> str:
        """
        Generate a single PostgreSQL log entry.

        Returns:
            str: Formatted PostgreSQL log entry
        """
        timestamp = self._generate_timestamp()
        level = self._weighted_choice(self.LOG_LEVELS)
        pid = random.randint(1000, 99999)

        # Generate different types of log messages
        if level in ["ERROR", "FATAL", "PANIC"]:
            message = self._generate_error_message(level)
        elif random.random() < 0.6:
            # SQL statement
            message = self._generate_sql_statement()
        else:
            # Connection or administrative message
            message = self._generate_admin_message(level)

        # PostgreSQL log format
        log_entry = f"{timestamp} UTC [{pid}]: [{level}] {message}"

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for PostgreSQL logs.

        Returns:
            str: Regular expression pattern
        """
        return (
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) UTC "
            r"\[(\d+)\]: \[(\w+)\] (.+)$"
        )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches PostgreSQL log format.

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
        if "query_types" in fields:
            self.QUERY_TYPES = fields["query_types"]
        if "table_names" in fields:
            self.TABLE_NAMES = fields["table_names"]

    def _generate_timestamp(self) -> str:
        """Generate timestamp in PostgreSQL format."""
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S.%f")[
            :-3
        ]  # Remove last 3 digits from microseconds

    def _generate_sql_statement(self) -> str:
        """Generate SQL statement."""
        query_type = self._weighted_choice(self.QUERY_TYPES)

        if query_type == "SELECT":
            return self._generate_select_query()
        elif query_type == "INSERT":
            return self._generate_insert_query()
        elif query_type == "UPDATE":
            return self._generate_update_query()
        elif query_type == "DELETE":
            return self._generate_delete_query()
        elif query_type == "CREATE":
            return self._generate_create_statement()
        elif query_type == "DROP":
            return self._generate_drop_statement()
        elif query_type == "ALTER":
            return self._generate_alter_statement()

        return "SELECT 1"

    def _generate_select_query(self) -> str:
        """Generate SELECT query."""
        table = random.choice(self.TABLE_NAMES)

        if random.random() < 0.3:
            # Simple select
            columns = random.sample(self.COLUMN_NAMES, random.randint(1, 3))
            return f"SELECT {', '.join(columns)} FROM {table}"
        elif random.random() < 0.6:
            # Select with WHERE
            condition_col = random.choice(self.COLUMN_NAMES)
            return f"SELECT * FROM {table} WHERE {condition_col} = $1"
        else:
            # Select with JOIN
            join_table = random.choice([t for t in self.TABLE_NAMES if t != table])
            return (
                f"SELECT t1.*, t2.name FROM {table} t1 "
                f"JOIN {join_table} t2 ON t1.{join_table[:-1]}_id = t2.id"
            )

    def _generate_insert_query(self) -> str:
        """Generate INSERT query."""
        table = random.choice(self.TABLE_NAMES)
        columns = random.sample(
            self.COLUMN_NAMES[1:], random.randint(2, 4)
        )  # Skip 'id'
        placeholders = ", ".join([f"${i+1}" for i in range(len(columns))])
        return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

    def _generate_update_query(self) -> str:
        """Generate UPDATE query."""
        table = random.choice(self.TABLE_NAMES)
        set_col = random.choice(self.COLUMN_NAMES[1:])  # Skip 'id'
        condition_col = random.choice(self.COLUMN_NAMES)
        return f"UPDATE {table} SET {set_col} = $1 WHERE {condition_col} = $2"

    def _generate_delete_query(self) -> str:
        """Generate DELETE query."""
        table = random.choice(self.TABLE_NAMES)
        condition_col = random.choice(self.COLUMN_NAMES)
        return f"DELETE FROM {table} WHERE {condition_col} = $1"

    def _generate_create_statement(self) -> str:
        """Generate CREATE statement."""
        if random.random() < 0.7:
            # Create table
            table = self.faker.word() + "s"
            return f"CREATE TABLE {table} (id SERIAL PRIMARY KEY, name VARCHAR(255), created_at TIMESTAMP DEFAULT NOW())"
        else:
            # Create index
            table = random.choice(self.TABLE_NAMES)
            column = random.choice(self.COLUMN_NAMES)
            return f"CREATE INDEX idx_{table}_{column} ON {table} ({column})"

    def _generate_drop_statement(self) -> str:
        """Generate DROP statement."""
        if random.random() < 0.8:
            # Drop table
            table = random.choice(self.TABLE_NAMES)
            return f"DROP TABLE IF EXISTS {table}"
        else:
            # Drop index
            return f"DROP INDEX IF EXISTS idx_{self.faker.word()}"

    def _generate_alter_statement(self) -> str:
        """Generate ALTER statement."""
        table = random.choice(self.TABLE_NAMES)
        if random.random() < 0.5:
            # Add column
            column = self.faker.word()
            return f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR(255)"
        else:
            # Drop column
            column = random.choice(self.COLUMN_NAMES)
            return f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column}"

    def _generate_error_message(self, level: str) -> str:
        """Generate error message based on level."""
        if level == "PANIC":
            panic_messages = [
                "PANIC: could not write to file: No space left on device",
                "PANIC: corrupted page pointers: lower = 0, upper = 0, special = 8192",
                "PANIC: WAL contains references to invalid pages",
            ]
            return random.choice(panic_messages)

        elif level == "FATAL":
            fatal_messages = [
                f"FATAL: database \"{random.choice(['test', 'production'])}\" does not exist",
                f'FATAL: role "{self.faker.user_name()}" does not exist',
                'FATAL: too many connections for role "user"',
                'FATAL: password authentication failed for user "postgres"',
                'FATAL: no pg_hba.conf entry for host "192.168.1.100", user "app", database "production"',
            ]
            return random.choice(fatal_messages)

        else:  # ERROR
            error_code = random.choice(list(self.ERROR_CODES.keys()))
            error_desc = self.ERROR_CODES[error_code]

            if error_code == "42P01":
                table = random.choice(self.TABLE_NAMES)
                return f'ERROR: relation "{table}" does not exist at character {random.randint(10, 100)}'
            elif error_code == "42703":
                column = random.choice(self.COLUMN_NAMES)
                return f'ERROR: column "{column}" does not exist'
            elif error_code == "23505":
                constraint = f"{random.choice(self.TABLE_NAMES)}_pkey"
                return f'ERROR: duplicate key value violates unique constraint "{constraint}"'
            else:
                return f"ERROR: {error_desc}"

    def _generate_admin_message(self, level: str) -> str:
        """Generate administrative message."""
        admin_messages = {
            "LOG": [
                f"connection received: host={self.faker.ipv4()} port={random.randint(30000, 60000)}",
                f"connection authorized: user={self.faker.user_name()} database={random.choice(['test', 'production'])}",
                f"disconnection: session time: {random.randint(1, 3600)} seconds",
                f"checkpoint starting: time",
                f"checkpoint complete: wrote {random.randint(100, 10000)} buffers",
                f'automatic vacuum of table "{random.choice(self.TABLE_NAMES)}": index scans: {random.randint(0, 5)}',
                f'automatic analyze of table "{random.choice(self.TABLE_NAMES)}" system usage: CPU {random.uniform(0.1, 5.0):.2f}s',
            ],
            "INFO": [
                f"database system is ready to accept connections",
                f"autovacuum launcher started",
                f"logical replication launcher started",
                f"background writer process started",
            ],
            "WARNING": [
                f"could not receive data from client: Connection reset by peer",
                f"terminating connection due to administrator command",
                f"canceling statement due to user request",
                f"there is no transaction in progress",
            ],
        }

        messages = admin_messages.get(level, admin_messages["LOG"])
        return random.choice(messages)

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]


class PostgreSQLSlowQueryLogGenerator(LogGenerator):
    """
    Generates PostgreSQL slow query logs with realistic patterns.

    Produces logs similar to PostgreSQL's log_min_duration_statement output
    including query execution time and SQL statements.
    """

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize PostgreSQL slow query log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Reuse table and column names
        self.TABLE_NAMES = ["users", "orders", "products", "categories", "audit_log"]
        self.COLUMN_NAMES = ["id", "name", "email", "created_at", "status"]

    def generate_log(self) -> str:
        """
        Generate a single PostgreSQL slow query log entry.

        Returns:
            str: Formatted PostgreSQL slow query log entry
        """
        timestamp = self._generate_timestamp()
        pid = random.randint(1000, 99999)
        duration = self._generate_duration()
        sql_query = self._generate_slow_query()

        # PostgreSQL slow query log format
        log_entry = (
            f"{timestamp} UTC [{pid}]: [LOG] duration: {duration} ms "
            f"statement: {sql_query}"
        )

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for PostgreSQL slow query logs.

        Returns:
            str: Regular expression pattern
        """
        return (
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) UTC "
            r"\[(\d+)\]: \[LOG\] duration: ([\d.]+) ms "
            r"statement: (.+)$"
        )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches PostgreSQL slow query log format.

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

    def _generate_timestamp(self) -> str:
        """Generate timestamp in PostgreSQL format."""
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def _generate_duration(self) -> str:
        """Generate realistic slow query duration."""
        # Slow queries typically take more than the log_min_duration_statement threshold
        if random.random() < 0.6:
            # Moderately slow (1-10 seconds)
            return f"{random.uniform(1000.0, 10000.0):.3f}"
        elif random.random() < 0.9:
            # Very slow (10-60 seconds)
            return f"{random.uniform(10000.0, 60000.0):.3f}"
        else:
            # Extremely slow (1+ minutes)
            return f"{random.uniform(60000.0, 300000.0):.3f}"

    def _generate_slow_query(self) -> str:
        """Generate slow SQL query."""
        table = random.choice(self.TABLE_NAMES)

        slow_queries = [
            # Full table scan
            f"SELECT * FROM {table}",
            # Complex JOIN without proper indexes
            f"SELECT t1.*, t2.* FROM {table} t1 JOIN {random.choice(self.TABLE_NAMES)} t2 ON t1.name ILIKE '%' || t2.name || '%'",
            # Subquery with large dataset
            f"SELECT * FROM {table} WHERE id IN (SELECT {table[:-1]}_id FROM {random.choice(self.TABLE_NAMES)} WHERE created_at > NOW() - INTERVAL '1 year')",
            # Aggregation on large dataset
            f"SELECT COUNT(*), AVG(id), MAX(created_at) FROM {table} GROUP BY EXTRACT(month FROM created_at)",
            # Update without proper WHERE clause
            f"UPDATE {table} SET status = 'processed' WHERE created_at < NOW() - INTERVAL '30 days'",
            # Delete with complex condition
            f"DELETE FROM {table} WHERE id NOT IN (SELECT DISTINCT {table[:-1]}_id FROM {random.choice(self.TABLE_NAMES)} WHERE status = 'active')",
            # Window function on large dataset
            f"SELECT *, ROW_NUMBER() OVER (PARTITION BY status ORDER BY created_at DESC) FROM {table}",
            # Recursive CTE
            f"WITH RECURSIVE tree AS (SELECT id, name, 0 as level FROM {table} WHERE id = 1 UNION ALL SELECT c.id, c.name, p.level + 1 FROM {table} c JOIN tree p ON c.parent_id = p.id) SELECT * FROM tree",
        ]

        return random.choice(slow_queries)

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]
