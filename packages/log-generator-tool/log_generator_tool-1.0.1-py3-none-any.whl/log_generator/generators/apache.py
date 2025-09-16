"""
Apache log generators for access and error logs.

This module implements log generators that produce realistic Apache access and error logs
following standard formats (Common Log Format, Combined Log Format, and Apache error format).
"""

import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from faker import Faker

from ..core.interfaces import LogGenerator
from ..core.models import LogEntry


class ApacheAccessLogGenerator(LogGenerator):
    """
    Generates Apache access logs in Common and Combined log formats.

    Supports both Common Log Format (CLF) and Combined Log Format with
    realistic data patterns including IP addresses, HTTP methods, status codes,
    and user agents.
    """

    # Common HTTP methods with realistic distribution
    HTTP_METHODS = {
        "GET": 0.75,
        "POST": 0.12,
        "HEAD": 0.05,
        "PUT": 0.03,
        "DELETE": 0.02,
        "OPTIONS": 0.02,
        "PATCH": 0.01,
    }

    # HTTP status codes with realistic distribution
    STATUS_CODES = {
        200: 0.75,
        404: 0.08,
        301: 0.04,
        302: 0.04,
        500: 0.02,
        403: 0.02,
        400: 0.02,
        503: 0.01,
        502: 0.01,
        401: 0.01,
    }

    # Common URL patterns for Apache servers
    URL_PATTERNS = [
        "/",
        "/index.html",
        "/index.php",
        "/wp-admin/",
        "/wp-login.php",
        "/wp-content/themes/style.css",
        "/wp-content/uploads/image.jpg",
        "/cgi-bin/script.cgi",
        "/phpmyadmin/",
        "/admin/",
        "/images/logo.png",
        "/css/style.css",
        "/js/script.js",
        "/favicon.ico",
        "/robots.txt",
        "/sitemap.xml",
    ]

    # Common user agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Apache-HttpClient/4.5.13 (Java/11.0.11)",
        "curl/7.68.0",
        "Wget/1.20.3 (linux-gnu)",
        "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    ]

    def __init__(
        self,
        format_type: str = "combined",
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Apache access log generator.

        Args:
            format_type (str): Log format type ("common" or "combined")
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.format_type = format_type.lower()
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Override defaults with custom config
        if "status_codes" in self.custom_config:
            self.STATUS_CODES = self.custom_config["status_codes"]
        if "user_agents" in self.custom_config:
            self.USER_AGENTS = self.custom_config["user_agents"]
        if "url_patterns" in self.custom_config:
            self.URL_PATTERNS = self.custom_config["url_patterns"]

    def generate_log(self) -> str:
        """
        Generate a single Apache access log entry.

        Returns:
            str: Formatted Apache access log entry
        """
        # Generate log components
        ip_address = self._generate_ip_address()
        remote_logname = "-"  # Usually not used
        remote_user = self._generate_remote_user()
        timestamp = self._generate_timestamp()
        method = self._weighted_choice(self.HTTP_METHODS)
        url = self._generate_url()
        protocol = "HTTP/1.1"
        status_code = self._weighted_choice(self.STATUS_CODES)
        response_size = self._generate_response_size(status_code)

        if self.format_type == "combined":
            referer = self._generate_referer()
            user_agent = random.choice(self.USER_AGENTS)

            # Combined Log Format
            log_entry = (
                f"{ip_address} {remote_logname} {remote_user} [{timestamp}] "
                f'"{method} {url} {protocol}" {status_code} {response_size} '
                f'"{referer}" "{user_agent}"'
            )
        else:
            # Common Log Format
            log_entry = (
                f"{ip_address} {remote_logname} {remote_user} [{timestamp}] "
                f'"{method} {url} {protocol}" {status_code} {response_size}'
            )

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for Apache access logs.

        Returns:
            str: Regular expression pattern
        """
        if self.format_type == "combined":
            # Combined Log Format pattern
            return (
                r"^(\S+) (\S+) (\S+) \[([^\]]+)\] "
                r'"([A-Z]+) ([^\s"]+) HTTP/[\d\.]+"\s+'
                r'(\d+) (\d+|-) "([^"]*)" "([^"]*)"$'
            )
        else:
            # Common Log Format pattern
            return (
                r"^(\S+) (\S+) (\S+) \[([^\]]+)\] "
                r'"([A-Z]+) ([^\s"]+) HTTP/[\d\.]+"\s+'
                r"(\d+) (\d+|-)$"
            )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches Apache access log format.

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

        # Update internal configurations
        if "status_codes" in fields:
            self.STATUS_CODES = fields["status_codes"]
        if "user_agents" in fields:
            self.USER_AGENTS = fields["user_agents"]
        if "url_patterns" in fields:
            self.URL_PATTERNS = fields["url_patterns"]

    def _generate_ip_address(self) -> str:
        """Generate realistic IP address."""
        if "ip_ranges" in self.custom_config:
            # Use custom IP ranges if provided
            return self.faker.ipv4_private()

        # Generate mix of private and public IPs
        if random.random() < 0.6:
            return self.faker.ipv4_private()
        else:
            return self.faker.ipv4_public()

    def _generate_remote_user(self) -> str:
        """Generate remote user (usually - for anonymous)."""
        if random.random() < 0.95:
            return "-"
        else:
            return self.faker.user_name()

    def _generate_timestamp(self) -> str:
        """Generate timestamp in Apache format."""
        now = datetime.now(timezone.utc)
        return now.strftime("%d/%b/%Y:%H:%M:%S %z")

    def _generate_url(self) -> str:
        """Generate realistic URL."""
        if random.random() < 0.8:
            return random.choice(self.URL_PATTERNS)
        else:
            # Generate dynamic URLs
            dynamic_patterns = [
                f"/user/{self.faker.random_int(1, 10000)}",
                f"/product/{self.faker.slug()}",
                f"/search.php?q={self.faker.word()}",
                f"/category/{self.faker.word()}",
                f"/page.php?id={self.faker.random_int(1, 100)}",
                f"/wp-content/uploads/{self.faker.file_name()}",
            ]
            return random.choice(dynamic_patterns)

    def _generate_response_size(self, status_code: int) -> str:
        """Generate realistic response size based on status code."""
        if status_code == 404:
            return str(random.randint(200, 600))
        elif status_code >= 500:
            return str(random.randint(150, 400))
        elif status_code in [301, 302]:
            return str(random.randint(250, 500))
        else:
            return str(random.randint(800, 75000))

    def _generate_referer(self) -> str:
        """Generate realistic referer."""
        referers = [
            "-",
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://duckduckgo.com/",
            "https://github.com/",
            "https://stackoverflow.com/",
            f"https://{self.faker.domain_name()}/",
            f"https://{self.faker.domain_name()}/page.html",
        ]
        return random.choice(referers)

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]


class ApacheErrorLogGenerator(LogGenerator):
    """
    Generates Apache error logs with realistic error patterns.

    Produces error logs following Apache error log format with various
    error levels and realistic error messages.
    """

    # Error levels with distribution
    ERROR_LEVELS = {
        "error": 0.45,
        "warn": 0.30,
        "notice": 0.15,
        "info": 0.05,
        "crit": 0.03,
        "alert": 0.01,
        "emerg": 0.01,
    }

    # Common Apache error patterns
    ERROR_PATTERNS = [
        "File does not exist: /var/www/html/favicon.ico",
        "script '/var/www/html/cgi-bin/test.cgi' not found or unable to stat",
        "client denied by server configuration: /var/www/html/admin/",
        "PHP Fatal error: Call to undefined function mysql_connect()",
        "PHP Parse error: syntax error, unexpected '}' in /var/www/html/index.php on line 42",
        "server reached MaxRequestWorkers setting, consider raising the MaxRequestWorkers setting",
        "SSL Library Error: error:14094418:SSL routines:ssl3_read_bytes:tlsv1 alert unknown ca",
        "Invalid method in request \\x16\\x03\\x01",
        "request failed: error reading the headers",
        "Timeout waiting for output from CGI script /var/www/html/cgi-bin/script.cgi",
        "mod_fcgid: read data timeout in 40 seconds",
        "Directory index forbidden by Options directive: /var/www/html/uploads/",
        "client sent HTTP/1.1 request without hostname (see RFC2616 section 14.23)",
        "Invalid URI in request GET /\\x22\\x3E\\x3Cscript\\x3Ealert(1)\\x3C/script\\x3E",
    ]

    # Apache modules that commonly generate errors
    MODULES = [
        "core",
        "mod_ssl",
        "mod_rewrite",
        "mod_php",
        "mod_fcgid",
        "mod_security",
        "mod_dir",
        "mod_auth",
    ]

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Apache error log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Override defaults with custom config
        if "error_levels" in self.custom_config:
            self.ERROR_LEVELS = self.custom_config["error_levels"]
        if "error_patterns" in self.custom_config:
            self.ERROR_PATTERNS = self.custom_config["error_patterns"]

    def generate_log(self) -> str:
        """
        Generate a single Apache error log entry.

        Returns:
            str: Formatted Apache error log entry
        """
        timestamp = self._generate_timestamp()
        level = self._weighted_choice(self.ERROR_LEVELS)
        module = random.choice(self.MODULES)
        pid = random.randint(1000, 99999)

        error_message = self._generate_error_message(level)
        client_ip = self.faker.ipv4()

        # Apache error log format
        log_entry = (
            f"[{timestamp}] [{level}] [{module}:error] [pid {pid}] "
            f"[client {client_ip}] {error_message}"
        )

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for Apache error logs.

        Returns:
            str: Regular expression pattern
        """
        return (
            r"^\[([^\]]+)\] \[(\w+)\] \[([^\]]+)\] \[pid (\d+)\] "
            r"\[client ([\d\.]+)\] (.+)$"
        )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches Apache error log format.

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

        if "error_levels" in fields:
            self.ERROR_LEVELS = fields["error_levels"]
        if "error_patterns" in fields:
            self.ERROR_PATTERNS = fields["error_patterns"]

    def _generate_timestamp(self) -> str:
        """Generate timestamp in Apache error log format."""
        now = datetime.now()
        # Apache format: [Wed Oct 11 14:32:52.123456 2023]
        return now.strftime("%a %b %d %H:%M:%S.%f %Y")

    def _generate_error_message(self, level: str) -> str:
        """Generate error message based on level."""
        if level in ["crit", "alert", "emerg"]:
            critical_errors = [
                "server is within MinSpareServers of MaxRequestWorkers, consider raising the MaxRequestWorkers setting",
                "caught SIGTERM, shutting down",
                "aborting: unable to determine if daemon is running",
                "No space left on device: mod_rewrite: could not create rewrite_log_lock",
            ]
            return random.choice(critical_errors)

        return random.choice(self.ERROR_PATTERNS)

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]
