"""
MySQL log generators for database logs.

This module implements log generators that produce realistic MySQL database logs
including query logs, error logs, slow query logs, and general logs following
MySQL's standard logging formats.
"""

import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from faker import Faker

from ..core.interfaces import LogGenerator
from ..core.models import LogEntry


class MySQLQueryLogGenerator(LogGenerator):
    """
    Generates MySQL query logs with realistic patterns.

    Produces logs similar to MySQL's general query log including
    connections, queries, and administrative commands.
    """

    # Query types with distribution
    QUERY_TYPES = {
        "SELECT": 0.60,
        "INSERT": 0.15,
        "UPDATE": 0.12,
        "DELETE": 0.08,
        "SHOW": 0.03,
        "DESCRIBE": 0.02,
    }

    # Common MySQL commands
    ADMIN_COMMANDS = [
        "Connect",
        "Quit",
        "Init DB",
        "Field List",
        "Refresh",
        "Statistics",
        "Ping",
    ]

    # Common table names
    TABLE_NAMES = [
        "users",
        "orders",
        "products",
        "categories",
        "sessions",
        "logs",
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
        "password",
        "created_at",
        "updated_at",
        "status",
        "type",
        "value",
        "description",
    ]

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize MySQL query log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Override defaults with custom config
        if "query_types" in self.custom_config:
            self.QUERY_TYPES = self.custom_config["query_types"]
        if "table_names" in self.custom_config:
            self.TABLE_NAMES = self.custom_config["table_names"]

    def generate_log(self) -> str:
        """
        Generate a single MySQL query log entry.

        Returns:
            str: Formatted MySQL query log entry
        """
        timestamp = self._generate_timestamp()
        connection_id = random.randint(1, 10000)

        # Decide between query and admin command
        if random.random() < 0.8:
            # Generate SQL query
            command_type = "Query"
            query_type = self._weighted_choice(self.QUERY_TYPES)
            query = self._generate_sql_query(query_type)
        else:
            # Generate admin command
            command_type = random.choice(self.ADMIN_COMMANDS)
            query = self._generate_admin_command(command_type)

        # MySQL general log format
        log_entry = f"{timestamp} {connection_id:6d} {command_type:12s} {query}"

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for MySQL query logs.

        Returns:
            str: Regular expression pattern
        """
        return r"^(\d{6} \d{2}:\d{2}:\d{2})\s+" r"(\d+)\s+" r"(\w+)\s+" r"(.+)$"

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches MySQL query log format.

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

        if "query_types" in fields:
            self.QUERY_TYPES = fields["query_types"]
        if "table_names" in fields:
            self.TABLE_NAMES = fields["table_names"]

    def _generate_timestamp(self) -> str:
        """Generate timestamp in MySQL format."""
        now = datetime.now()
        return now.strftime("%y%m%d %H:%M:%S")

    def _generate_sql_query(self, query_type: str) -> str:
        """Generate SQL query based on type."""
        table = random.choice(self.TABLE_NAMES)

        if query_type == "SELECT":
            columns = random.sample(self.COLUMN_NAMES, random.randint(1, 3))
            columns_str = ", ".join(columns)

            if random.random() < 0.3:
                # Simple select
                return f"SELECT {columns_str} FROM {table}"
            elif random.random() < 0.6:
                # Select with WHERE
                condition_col = random.choice(self.COLUMN_NAMES)
                return f"SELECT {columns_str} FROM {table} WHERE {condition_col} = {random.randint(1, 1000)}"
            else:
                # Select with JOIN
                join_table = random.choice([t for t in self.TABLE_NAMES if t != table])
                return f"SELECT {columns_str} FROM {table} t1 JOIN {join_table} t2 ON t1.id = t2.{table[:-1]}_id"

        elif query_type == "INSERT":
            columns = random.sample(
                self.COLUMN_NAMES[1:], random.randint(2, 4)
            )  # Skip 'id'
            values = []
            for col in columns:
                if "email" in col:
                    values.append(f"'{self.faker.email()}'")
                elif "name" in col:
                    values.append(f"'{self.faker.name()}'")
                elif "at" in col:
                    values.append("NOW()")
                else:
                    values.append(f"'{self.faker.word()}'")

            columns_str = ", ".join(columns)
            values_str = ", ".join(values)
            return f"INSERT INTO {table} ({columns_str}) VALUES ({values_str})"

        elif query_type == "UPDATE":
            set_col = random.choice(self.COLUMN_NAMES[1:])  # Skip 'id'
            condition_col = random.choice(self.COLUMN_NAMES)

            if "email" in set_col:
                set_value = f"'{self.faker.email()}'"
            elif "name" in set_col:
                set_value = f"'{self.faker.name()}'"
            elif "at" in set_col:
                set_value = "NOW()"
            else:
                set_value = f"'{self.faker.word()}'"

            return f"UPDATE {table} SET {set_col} = {set_value} WHERE {condition_col} = {random.randint(1, 1000)}"

        elif query_type == "DELETE":
            condition_col = random.choice(self.COLUMN_NAMES)
            return (
                f"DELETE FROM {table} WHERE {condition_col} = {random.randint(1, 1000)}"
            )

        elif query_type == "SHOW":
            show_options = [
                "TABLES",
                "DATABASES",
                "COLUMNS FROM " + table,
                "INDEX FROM " + table,
            ]
            return f"SHOW {random.choice(show_options)}"

        elif query_type == "DESCRIBE":
            return f"DESCRIBE {table}"

        return f"SELECT * FROM {table}"

    def _generate_admin_command(self, command_type: str) -> str:
        """Generate admin command based on type."""
        if command_type == "Connect":
            return f"root@localhost on {random.choice(['', 'test', 'production'])}"
        elif command_type == "Init DB":
            return random.choice(["test", "production", "development"])
        elif command_type == "Field List":
            return random.choice(self.TABLE_NAMES)
        else:
            return ""

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]


class MySQLErrorLogGenerator(LogGenerator):
    """
    Generates MySQL error logs with realistic error patterns.

    Produces logs similar to MySQL's error log including startup messages,
    warnings, errors, and shutdown messages.
    """

    # Log levels with distribution
    LOG_LEVELS = {"Note": 0.50, "Warning": 0.30, "Error": 0.20}

    # Common MySQL error patterns
    ERROR_PATTERNS = [
        "Access denied for user '{user}'@'{host}' (using password: {password})",
        "Table '{database}.{table}' doesn't exist",
        "Unknown column '{column}' in 'field list'",
        "Duplicate entry '{value}' for key '{key}'",
        "Data too long for column '{column}' at row {row}",
        "Cannot add or update a child row: a foreign key constraint fails",
        "Lock wait timeout exceeded; try restarting transaction",
        "Deadlock found when trying to get lock; try restarting transaction",
        "Out of range value for column '{column}' at row {row}",
        "Incorrect {type} value: '{value}' for column '{column}' at row {row}",
    ]

    # Warning patterns
    WARNING_PATTERNS = [
        "Using a password on the command line interface can be insecure",
        "Unsafe statement written to the binary log using statement format",
        "The table '{table}' is full",
        "Hostname '{hostname}' does not resolve to '{ip}'",
        "Changed limits: max_open_files: {old_value} (requested {new_value})",
        "Changed limits: max_connections: {old_value} (requested {new_value})",
        "InnoDB: Buffer pool(s) load completed at {timestamp}",
        "Slave SQL thread initialized, starting replication in log '{log}' at position {position}",
        "Event Scheduler: Loaded {count} events",
        "The server quit without updating PID file ({pid_file})",
    ]

    # Note patterns
    NOTE_PATTERNS = [
        "mysqld: ready for connections",
        "Version: '{version}' socket: '{socket}' port: {port} MySQL Community Server",
        "InnoDB: {pages} pages in the buffer pool",
        "InnoDB: Highest supported file format is Barracuda",
        "InnoDB: Log scan progressed past the checkpoint lsn {lsn}",
        "InnoDB: Database was not shutdown normally!",
        "InnoDB: Starting crash recovery",
        "InnoDB: Reading tablespace information from the .ibd files...",
        "InnoDB: Restoring possible half-written data pages",
        "InnoDB: {count} transaction(s) which must be rolled back or cleaned up",
    ]

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize MySQL error log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Override defaults with custom config
        if "log_levels" in self.custom_config:
            self.LOG_LEVELS = self.custom_config["log_levels"]

    def generate_log(self) -> str:
        """
        Generate a single MySQL error log entry.

        Returns:
            str: Formatted MySQL error log entry
        """
        timestamp = self._generate_timestamp()
        level = self._weighted_choice(self.LOG_LEVELS)
        message = self._generate_message(level)

        # MySQL error log format
        log_entry = f"{timestamp} [{level}] {message}"

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for MySQL error logs.

        Returns:
            str: Regular expression pattern
        """
        return r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) " r"\[(\w+)\] (.+)$"

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches MySQL error log format.

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

    def _generate_timestamp(self) -> str:
        """Generate timestamp in MySQL error log format."""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def _generate_message(self, level: str) -> str:
        """Generate message based on level."""
        if level == "Error":
            pattern = random.choice(self.ERROR_PATTERNS)
        elif level == "Warning":
            pattern = random.choice(self.WARNING_PATTERNS)
        else:  # Note
            pattern = random.choice(self.NOTE_PATTERNS)

        # Fill in placeholders
        replacements = {
            "user": self.faker.user_name(),
            "host": self.faker.ipv4(),
            "password": random.choice(["YES", "NO"]),
            "database": random.choice(["test", "production", "app"]),
            "table": random.choice(["users", "orders", "products"]),
            "column": random.choice(["id", "name", "email", "status"]),
            "value": str(random.randint(1, 1000)),
            "key": "PRIMARY",
            "row": str(random.randint(1, 100)),
            "type": random.choice(["integer", "datetime", "varchar"]),
            "hostname": self.faker.domain_name(),
            "ip": self.faker.ipv4(),
            "old_value": str(random.randint(100, 1000)),
            "new_value": str(random.randint(1000, 5000)),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "log": f"mysql-bin.{random.randint(100000, 999999)}",
            "position": str(random.randint(1000, 99999)),
            "count": str(random.randint(1, 100)),
            "pid_file": "/var/run/mysqld/mysqld.pid",
            "version": f"8.0.{random.randint(20, 35)}",
            "socket": "/var/run/mysqld/mysqld.sock",
            "port": str(random.choice([3306, 3307, 3308])),
            "pages": str(random.randint(1000, 50000)),
            "lsn": str(random.randint(1000000, 9999999)),
        }

        for key, value in replacements.items():
            pattern = pattern.replace(f"{{{key}}}", value)

        return pattern

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]


class MySQLSlowQueryLogGenerator(LogGenerator):
    """
    Generates MySQL slow query logs with realistic patterns.

    Produces logs similar to MySQL's slow query log including
    query execution time, rows examined, and SQL statements.
    """

    # Query types that are commonly slow
    SLOW_QUERY_TYPES = {"SELECT": 0.70, "UPDATE": 0.15, "DELETE": 0.10, "INSERT": 0.05}

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize MySQL slow query log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Reuse table and column names from query generator
        self.TABLE_NAMES = ["users", "orders", "products", "categories", "logs"]
        self.COLUMN_NAMES = ["id", "name", "email", "created_at", "status"]

    def generate_log(self) -> str:
        """
        Generate a single MySQL slow query log entry.

        Returns:
            str: Formatted MySQL slow query log entry
        """
        timestamp = self._generate_timestamp()
        user_host = f"{self.faker.user_name()}[{self.faker.user_name()}] @ localhost []"
        thread_id = random.randint(1, 1000)
        schema = random.choice(["test", "production", "app"])

        # Query execution metrics
        query_time = self._generate_query_time()
        lock_time = self._generate_lock_time()
        rows_sent = random.randint(0, 10000)
        rows_examined = random.randint(rows_sent, rows_sent * 10)

        # Generate slow SQL query
        query_type = self._weighted_choice(self.SLOW_QUERY_TYPES)
        sql_query = self._generate_slow_query(query_type)

        # MySQL slow query log format
        log_entry = (
            f"# Time: {timestamp}\n"
            f"# User@Host: {user_host}\n"
            f"# Thread_id: {thread_id}  Schema: {schema}\n"
            f"# Query_time: {query_time}  Lock_time: {lock_time}  "
            f"Rows_sent: {rows_sent}  Rows_examined: {rows_examined}\n"
            f"SET timestamp={int(datetime.now().timestamp())};\n"
            f"{sql_query};"
        )

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for MySQL slow query logs.

        Returns:
            str: Regular expression pattern
        """
        return (
            r"^# Time: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\n"
            r"# User@Host: ([^\n]+)\n"
            r"# Thread_id: (\d+)\s+Schema: ([^\n]*)\n"
            r"# Query_time: ([\d.]+)\s+Lock_time: ([\d.]+)\s+"
            r"Rows_sent: (\d+)\s+Rows_examined: (\d+)\n"
            r"SET timestamp=(\d+);\n"
            r"(.+);$"
        )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches MySQL slow query log format.

        Args:
            log_entry (str): Log entry to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pattern = self.get_log_pattern()
        return bool(re.match(pattern, log_entry, re.MULTILINE | re.DOTALL))

    def set_custom_fields(self, fields: Dict[str, Any]) -> None:
        """
        Set custom fields for log generation.

        Args:
            fields (Dict[str, Any]): Custom field definitions
        """
        self.custom_config.update(fields)

    def _generate_timestamp(self) -> str:
        """Generate timestamp in MySQL slow query log format."""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def _generate_query_time(self) -> str:
        """Generate realistic query execution time."""
        # Slow queries typically take more than 1 second
        if random.random() < 0.6:
            # Moderately slow (1-10 seconds)
            return f"{random.uniform(1.0, 10.0):.6f}"
        elif random.random() < 0.9:
            # Very slow (10-60 seconds)
            return f"{random.uniform(10.0, 60.0):.6f}"
        else:
            # Extremely slow (1+ minutes)
            return f"{random.uniform(60.0, 300.0):.6f}"

    def _generate_lock_time(self) -> str:
        """Generate realistic lock time."""
        # Lock time is usually much smaller than query time
        return f"{random.uniform(0.0, 1.0):.6f}"

    def _generate_slow_query(self, query_type: str) -> str:
        """Generate slow SQL query based on type."""
        table = random.choice(self.TABLE_NAMES)

        if query_type == "SELECT":
            # Generate queries that would be slow (no indexes, large scans, etc.)
            if random.random() < 0.4:
                # Full table scan without WHERE
                return f"SELECT * FROM {table}"
            elif random.random() < 0.7:
                # Complex JOIN without proper indexes
                join_table = random.choice([t for t in self.TABLE_NAMES if t != table])
                return (
                    f"SELECT t1.*, t2.* FROM {table} t1 "
                    f"JOIN {join_table} t2 ON t1.name LIKE CONCAT('%', t2.name, '%')"
                )
            else:
                # Subquery that scans large amounts of data
                return (
                    f"SELECT * FROM {table} WHERE id IN "
                    f"(SELECT {table[:-1]}_id FROM {random.choice(self.TABLE_NAMES)} "
                    f"WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 YEAR))"
                )

        elif query_type == "UPDATE":
            # Update without proper WHERE clause
            return (
                f"UPDATE {table} SET status = 'processed' "
                f"WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)"
            )

        elif query_type == "DELETE":
            # Delete with complex WHERE clause
            return (
                f"DELETE FROM {table} WHERE id NOT IN "
                f"(SELECT DISTINCT {table[:-1]}_id FROM {random.choice(self.TABLE_NAMES)} "
                f"WHERE status = 'active')"
            )

        elif query_type == "INSERT":
            # Bulk insert that takes time
            return (
                f"INSERT INTO {table} (name, email, created_at) "
                f"SELECT CONCAT('user_', id), CONCAT('user_', id, '@example.com'), NOW() "
                f"FROM {random.choice(self.TABLE_NAMES)} WHERE id < 10000"
            )

        return f"SELECT * FROM {table}"

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]
