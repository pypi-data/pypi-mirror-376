"""
Nginx log generators for access and error logs.

This module implements log generators that produce realistic Nginx access and error logs
following standard formats (Common Log Format, Combined Log Format, and Nginx error format).
"""

import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from faker import Faker

from ..core.interfaces import LogGenerator
from ..core.models import LogEntry


class NginxAccessLogGenerator(LogGenerator):
    """
    Generates Nginx access logs in Common and Combined log formats.

    Supports both Common Log Format (CLF) and Combined Log Format with
    realistic data patterns including IP addresses, HTTP methods, status codes,
    and user agents.
    """

    # Common HTTP methods with realistic distribution
    HTTP_METHODS = {
        "GET": 0.73,
        "POST": 0.16,
        "PUT": 0.03,
        "DELETE": 0.02,
        "HEAD": 0.03,
        "OPTIONS": 0.02,
        "PATCH": 0.01,
    }

    # HTTP status codes with realistic distribution
    STATUS_CODES = {
        200: 0.63,
        301: 0.05,
        302: 0.04,
        304: 0.06,
        204: 0.01,
        206: 0.02,
        400: 0.02,
        401: 0.01,
        403: 0.02,
        404: 0.08,
        418: 0.002,
        429: 0.008,
        499: 0.01,
        500: 0.02,
        502: 0.01,
        503: 0.01,
        504: 0.008,
    }

    # Common URL patterns
    URL_PATTERNS = [
        "/",
        "/index.html",
        "/api/users",
        "/api/orders",
        "/api/products",
        "/static/css/style.css",
        "/static/js/app.js",
        "/images/logo.png",
        "/favicon.ico",
        "/robots.txt",
        "/sitemap.xml",
        "/admin/login",
        "/user/profile",
        "/search",
        "/contact",
        "/about",
    ]

    # Common user agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "curl/7.68.0",
        "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    ]

    def __init__(
        self,
        format_type: str = "combined",
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Nginx access log generator.

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
        Generate a single Nginx access log entry.

        Returns:
            str: Formatted Nginx access log entry
        """
        return self.generate_log_with_time(datetime.now())

    def generate_log_with_time(self, timestamp: datetime) -> str:
        """
        Generate a Nginx access log entry with a specific timestamp.

        Args:
            timestamp: The timestamp to use for the log entry

        Returns:
            str: Formatted Nginx access log entry with specified timestamp
        """
        # Generate log components
        ip_address = self._generate_ip_address()
        formatted_timestamp = self._format_timestamp(timestamp)
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
                f"{ip_address} - - [{formatted_timestamp}] "
                f'"{method} {url} {protocol}" {status_code} {response_size} '
                f'"{referer}" "{user_agent}"'
            )
        else:
            # Common Log Format
            log_entry = (
                f"{ip_address} - - [{formatted_timestamp}] "
                f'"{method} {url} {protocol}" {status_code} {response_size}'
            )

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for Nginx access logs.

        Returns:
            str: Regular expression pattern
        """
        if self.format_type == "combined":
            # Combined Log Format pattern
            return (
                r"^(\S+) \S+ \S+ \[([^\]]+)\] "
                r'"([A-Z]+) ([^\s"]+) HTTP/[\d\.]+"\s+'
                r'(\d+) (\d+|-) "([^"]*)" "([^"]*)"$'
            )
        else:
            # Common Log Format pattern
            return (
                r"^(\S+) \S+ \S+ \[([^\]]+)\] "
                r'"([A-Z]+) ([^\s"]+) HTTP/[\d\.]+"\s+'
                r"(\d+) (\d+|-)$"
            )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches Nginx access log format.

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
            ip_range = random.choice(self.custom_config["ip_ranges"])
            return self.faker.ipv4_private()

        # Generate mix of private and public IPs
        if random.random() < 0.7:
            return self.faker.ipv4_private()
        else:
            return self.faker.ipv4_public()

    def _generate_timestamp(self) -> str:
        """Generate timestamp in Nginx format."""
        now = datetime.now(timezone.utc)
        return self._format_timestamp(now)

    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format a specific timestamp in Nginx format."""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp.strftime("%d/%b/%Y:%H:%M:%S %z")

    def _generate_url(self) -> str:
        """Generate realistic URL."""
        if random.random() < 0.8:
            return random.choice(self.URL_PATTERNS)
        else:
            # Generate dynamic URLs
            dynamic_patterns = [
                f"/api/users/{self.faker.random_int(1, 10000)}",
                f"/products/{self.faker.slug()}",
                f"/search?q={self.faker.word()}",
                f"/category/{self.faker.word()}",
                f"/page/{self.faker.random_int(1, 100)}",
            ]
            return random.choice(dynamic_patterns)

    def _generate_response_size(self, status_code: int) -> str:
        """Generate realistic response size based on status code."""
        if status_code == 404:
            return str(random.randint(150, 500))
        elif status_code >= 500:
            return str(random.randint(100, 300))
        elif status_code in [301, 302]:
            return str(random.randint(200, 400))
        else:
            return str(random.randint(500, 50000))

    def _generate_referer(self) -> str:
        """Generate realistic referer."""
        referers = [
            "-",
            "https://www.google.com/?q=" + self.faker.word(),
            "https://www.bing.com/",
            "https://github.com/",
            "https://stackoverflow.com/",
            f"https://{self.faker.domain_name()}/",
            f"https://{self.faker.domain_name()}/page",
        ]
        return random.choice(referers)

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]


class NginxErrorLogGenerator(LogGenerator):
    """
    Generates Nginx error logs with realistic error patterns.

    Produces error logs following Nginx error log format with various
    error levels and realistic error messages.
    """

    # Error levels with distribution
    ERROR_LEVELS = {
        "error": 0.48,
        "warn": 0.25,
        "notice": 0.15,
        "info": 0.08,
        "crit": 0.02,
        "alert": 0.01,
        "emerg": 0.01,
    }

    # Common error patterns
    ERROR_PATTERNS = [
        "connect() failed (111: Connection refused) while connecting to upstream",
        "upstream timed out (110: Connection timed out) while connecting to upstream",
        "no live upstreams while connecting to upstream",
        "SSL_do_handshake() failed (SSL: error:14094418:SSL routines:ssl3_read_bytes:tlsv1 alert unknown ca)",
        "client intended to send too large body",
        "access forbidden by rule",
        'directory index of "/var/www/html/" is forbidden',
        'open() "/var/www/html/favicon.ico" failed (2: No such file or directory)',
        'FastCGI sent in stderr: "PHP message: PHP Fatal error:',
        "recv() failed (104: Connection reset by peer) while reading response header from upstream",
        "upstream server temporarily disabled while connecting to upstream",
        'limiting requests, excess: 5.000 by zone "req_limit_per_ip"',
        "client closed connection while waiting for request",
        'broken header: "GET /admin HTTP/1.1" while reading client request headers',
        "upstream prematurely closed connection while reading response header from upstream",
        "upstream sent too big header while reading response header from upstream",
        "rewrite or internal redirection cycle while processing",
        "invalid host in upstream",
        "client sent invalid method while reading client request line",
        "client sent invalid header while reading client request headers",
        "could not build the proxy_headers_hash, you should increase either proxy_headers_hash_max_size: 512 or proxy_headers_hash_bucket_size: 64",
        "worker_connections are not enough",
        "kevent() reported about an closed connection (54: Connection reset by peer)",
        "kevent() failed (12: Cannot allocate memory)",
        'open() "/var/www/html/.env" failed (13: Permission denied)',
        "SSL_read() failed (SSL: error:1408F119:SSL routines:ssl3_get_record:decryption failed or bad record mac)",
        "SSL_write() failed (SSL: error:1409F07F:SSL routines:ssl3_write_pending:bad write retry)",
        "certificate verification failed (certificate has expired)",
        "upstream response is buffered to a temporary file",
        "cache key too large, cache bypassed",
        'cache file "/var/cache/nginx/proxy_temp/0000012345" had invalid header',
        "header already sent while sending to client",
        "upstream sent invalid chunked response",
        "request body is buffered to a temporary file",
        "an upstream response is buffered to a temporary file to allow caching",
        "zero size buf in writer",
        "sendfile() failed (32: Broken pipe) while sending response to client",
        "client intended to send too large header",
    ]

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Nginx error log generator.

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
        Generate a single Nginx error log entry.

        Returns:
            str: Formatted Nginx error log entry
        """
        timestamp = self._generate_timestamp()
        level = self._weighted_choice(self.ERROR_LEVELS)
        pid = random.randint(1000, 99999)
        tid = random.randint(0, 999)
        connection_id = random.randint(1, 99999)

        error_message = self._generate_error_message(level)
        client_ip = self.faker.ipv4()

        # Nginx error log format
        log_entry = (
            f"{timestamp} [{level}] {pid}#{tid}: *{connection_id} {error_message}, "
            f"client: {client_ip}, server: {self.faker.domain_name()}, "
            f'request: "GET {self._generate_request_path()} HTTP/1.1", '
            f'host: "{self.faker.domain_name()}"'
        )

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for Nginx error logs.

        Returns:
            str: Regular expression pattern
        """
        return (
            r"^(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) "
            r"\[(\w+)\] (\d+)#(\d+): \*(\d+) (.+), "
            r"client: ([\d\.]+), server: ([^,]+), "
            r'request: "([^"]+)", host: "([^"]+)"'
        )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches Nginx error log format.

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
        """Generate timestamp in Nginx error log format."""
        now = datetime.now()
        return now.strftime("%Y/%m/%d %H:%M:%S")

    def _generate_error_message(self, level: str) -> str:
        """Generate error message based on level."""
        if level in ["crit", "alert"]:
            critical_errors = [
                "worker process died unexpectedly",
                "could not open error log file",
                "malloc() failed",
                "mmap() failed",
            ]
            return random.choice(critical_errors)

        return random.choice(self.ERROR_PATTERNS)

    def _generate_request_path(self) -> str:
        """Generate request path for error context."""
        paths = [
            "/",
            "/admin",
            "/api/users",
            "/nonexistent",
            "/favicon.ico",
            "/robots.txt",
        ]
        return random.choice(paths)

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]
