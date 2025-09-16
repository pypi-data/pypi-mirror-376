"""
Faker library integration for realistic data generation.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from faker import Faker


class FakerDataGenerator:
    """
    Integrates Faker library for generating realistic log data.
    Provides specialized generators for common log fields.
    """

    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize Faker data generator.

        Args:
            locale: Locale for data generation (e.g., 'en_US', 'ko_KR')
            seed: Random seed for reproducible results
        """
        self.faker = Faker(locale)
        self.seed = seed
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        self.generators = self._setup_generators()

    def _setup_generators(self) -> Dict[str, Callable]:
        """Setup specialized generators for log data"""
        return {
            # Network related
            "ip_address": self._generate_ip_address,
            "ipv4": self.faker.ipv4,
            "ipv6": self.faker.ipv6,
            "mac_address": self.faker.mac_address,
            "domain_name": self.faker.domain_name,
            "url": self.faker.url,
            "uri": self.faker.uri,
            "port": self._generate_port,
            # User agents and browsers
            "user_agent": self._generate_user_agent,
            "browser": self._generate_browser,
            "platform": self._generate_platform,
            # HTTP related
            "http_method": self._generate_http_method,
            "http_status_code": self._generate_http_status_code,
            "http_status_phrase": self._generate_http_status_phrase,
            "content_type": self._generate_content_type,
            "referer": self.faker.url,
            # User and identity
            "username": self.faker.user_name,
            "email": self.faker.email,
            "first_name": self.faker.first_name,
            "last_name": self.faker.last_name,
            "full_name": self.faker.name,
            "company": self.faker.company,
            # Geographic
            "country": self.faker.country,
            "city": self.faker.city,
            "latitude": lambda: str(self.faker.latitude()),
            "longitude": lambda: str(self.faker.longitude()),
            # Time related
            "timestamp": self._generate_timestamp,
            "iso_timestamp": self._generate_iso_timestamp,
            "unix_timestamp": self._generate_unix_timestamp,
            "date": lambda: self.faker.date().isoformat(),
            "time": lambda: self.faker.time().isoformat(),
            # File and path related
            "file_name": self.faker.file_name,
            "file_path": self.faker.file_path,
            "file_extension": self.faker.file_extension,
            "mime_type": self.faker.mime_type,
            # Numeric and measurement
            "response_time": self._generate_response_time,
            "file_size": self._generate_file_size,
            "bandwidth": self._generate_bandwidth,
            "cpu_usage": self._generate_cpu_usage,
            "memory_usage": self._generate_memory_usage,
            # Security related
            "session_id": self._generate_session_id,
            "api_key": self._generate_api_key,
            "jwt_token": self._generate_jwt_token,
            # Error and logging
            "log_level": self._generate_log_level,
            "error_code": self._generate_error_code,
            "process_id": self._generate_process_id,
            "thread_id": self._generate_thread_id,
            # Database related
            "database_name": self._generate_database_name,
            "table_name": self._generate_table_name,
            "query_duration": self._generate_query_duration,
            "rows_affected": self._generate_rows_affected,
        }

    def _generate_ip_address(self) -> str:
        """Generate realistic IP address with weighted distribution"""
        # Weight towards common private IP ranges
        ranges = [
            ("192.168.", 0.4),  # Most common private range
            ("10.", 0.3),  # Private range
            ("172.16.", 0.1),  # Private range
            ("public", 0.2),  # Public IPs
        ]

        choice = random.choices([r[0] for r in ranges], weights=[r[1] for r in ranges])[
            0
        ]

        if choice == "public":
            return self.faker.ipv4_public()
        elif choice == "192.168.":
            return f"192.168.{random.randint(1, 255)}.{random.randint(1, 254)}"
        elif choice == "10.":
            return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        else:  # 172.16.
            return f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

    def _generate_port(self) -> str:
        """Generate realistic port numbers with weighted distribution"""
        common_ports = [
            80,
            443,
            22,
            21,
            25,
            53,
            110,
            143,
            993,
            995,
            8080,
            8443,
            3000,
            5000,
        ]
        if random.random() < 0.6:  # 60% chance of common port
            return str(random.choice(common_ports))
        else:
            return str(random.randint(1024, 65535))

    def _generate_user_agent(self) -> str:
        """Generate realistic user agent strings"""
        browsers = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0",
        ]
        return random.choice(browsers)

    def _generate_browser(self) -> str:
        """Generate browser name"""
        browsers = ["Chrome", "Firefox", "Safari", "Edge", "Opera", "Internet Explorer"]
        return random.choice(browsers)

    def _generate_platform(self) -> str:
        """Generate platform/OS name"""
        platforms = ["Windows", "macOS", "Linux", "iOS", "Android", "Ubuntu", "CentOS"]
        return random.choice(platforms)

    def _generate_http_method(self) -> str:
        """Generate HTTP method with realistic distribution"""
        methods = [
            ("GET", 0.6),
            ("POST", 0.25),
            ("PUT", 0.05),
            ("DELETE", 0.03),
            ("PATCH", 0.02),
            ("HEAD", 0.03),
            ("OPTIONS", 0.02),
        ]
        return random.choices([m[0] for m in methods], weights=[m[1] for m in methods])[
            0
        ]

    def _generate_http_status_code(self) -> str:
        """Generate HTTP status code with realistic distribution"""
        status_codes = [
            ("200", 0.7),  # Success
            ("404", 0.1),  # Not Found
            ("500", 0.05),  # Internal Server Error
            ("301", 0.03),  # Moved Permanently
            ("302", 0.03),  # Found
            ("400", 0.02),  # Bad Request
            ("401", 0.02),  # Unauthorized
            ("403", 0.02),  # Forbidden
            ("503", 0.01),  # Service Unavailable
            ("502", 0.01),  # Bad Gateway
            ("201", 0.01),  # Created
        ]
        return random.choices(
            [s[0] for s in status_codes], weights=[s[1] for s in status_codes]
        )[0]

    def _generate_http_status_phrase(self) -> str:
        """Generate HTTP status phrase"""
        phrases = {
            "200": "OK",
            "201": "Created",
            "301": "Moved Permanently",
            "302": "Found",
            "400": "Bad Request",
            "401": "Unauthorized",
            "403": "Forbidden",
            "404": "Not Found",
            "500": "Internal Server Error",
            "502": "Bad Gateway",
            "503": "Service Unavailable",
        }
        status_code = self._generate_http_status_code()
        return phrases.get(status_code, "Unknown")

    def _generate_content_type(self) -> str:
        """Generate content type"""
        types = [
            "text/html",
            "application/json",
            "text/css",
            "application/javascript",
            "image/png",
            "image/jpeg",
            "image/gif",
            "text/plain",
            "application/xml",
            "application/pdf",
        ]
        return random.choice(types)

    def _generate_timestamp(self) -> str:
        """Generate timestamp in common log format"""
        # Generate timestamp within last 30 days
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        random_time = self.faker.date_time_between(
            start_date=start_time, end_date=end_time
        )
        return random_time.strftime("%Y-%m-%d %H:%M:%S")

    def _generate_iso_timestamp(self) -> str:
        """Generate ISO format timestamp"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        random_time = self.faker.date_time_between(
            start_date=start_time, end_date=end_time
        )
        return random_time.isoformat()

    def _generate_unix_timestamp(self) -> str:
        """Generate Unix timestamp"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        random_time = self.faker.date_time_between(
            start_date=start_time, end_date=end_time
        )
        return str(int(random_time.timestamp()))

    def _generate_response_time(self) -> str:
        """Generate realistic response time in milliseconds"""
        # Most responses are fast, some are slow
        if random.random() < 0.8:  # 80% fast responses
            return str(round(random.uniform(1, 100), 2))
        else:  # 20% slower responses
            return str(round(random.uniform(100, 5000), 2))

    def _generate_file_size(self) -> str:
        """Generate file size in bytes"""
        # Weighted distribution for realistic file sizes
        size_ranges = [
            (1, 1024, 0.3),  # Small files (1B - 1KB)
            (1024, 1024 * 1024, 0.4),  # Medium files (1KB - 1MB)
            (1024 * 1024, 1024 * 1024 * 10, 0.2),  # Large files (1MB - 10MB)
            (
                1024 * 1024 * 10,
                1024 * 1024 * 100,
                0.1,
            ),  # Very large files (10MB - 100MB)
        ]

        range_choice = random.choices(size_ranges, weights=[r[2] for r in size_ranges])[
            0
        ]
        return str(random.randint(range_choice[0], range_choice[1]))

    def _generate_bandwidth(self) -> str:
        """Generate bandwidth usage in bytes/sec"""
        return str(random.randint(1024, 1024 * 1024 * 10))  # 1KB/s to 10MB/s

    def _generate_cpu_usage(self) -> str:
        """Generate CPU usage percentage"""
        # Most of the time CPU usage is low
        if random.random() < 0.7:
            return str(round(random.uniform(0, 30), 1))
        else:
            return str(round(random.uniform(30, 100), 1))

    def _generate_memory_usage(self) -> str:
        """Generate memory usage in MB"""
        return str(random.randint(100, 8192))  # 100MB to 8GB

    def _generate_session_id(self) -> str:
        """Generate session ID"""
        return self.faker.uuid4()

    def _generate_api_key(self) -> str:
        """Generate API key"""
        return self.faker.sha256()[:32]

    def _generate_jwt_token(self) -> str:
        """Generate JWT-like token"""
        header = self.faker.sha256()[:20]
        payload = self.faker.sha256()[:40]
        signature = self.faker.sha256()[:20]
        return f"{header}.{payload}.{signature}"

    def _generate_log_level(self) -> str:
        """Generate log level with realistic distribution"""
        levels = [
            ("INFO", 0.5),
            ("WARN", 0.2),
            ("ERROR", 0.15),
            ("DEBUG", 0.1),
            ("FATAL", 0.03),
            ("TRACE", 0.02),
        ]
        return random.choices([l[0] for l in levels], weights=[l[1] for l in levels])[0]

    def _generate_error_code(self) -> str:
        """Generate error code"""
        return f"E{random.randint(1000, 9999)}"

    def _generate_process_id(self) -> str:
        """Generate process ID"""
        return str(random.randint(1000, 99999))

    def _generate_thread_id(self) -> str:
        """Generate thread ID"""
        return str(random.randint(1, 999))

    def _generate_database_name(self) -> str:
        """Generate database name"""
        names = [
            "users",
            "products",
            "orders",
            "inventory",
            "logs",
            "analytics",
            "cache",
            "sessions",
        ]
        return random.choice(names)

    def _generate_table_name(self) -> str:
        """Generate table name"""
        names = [
            "user_accounts",
            "product_catalog",
            "order_history",
            "payment_info",
            "log_entries",
            "user_sessions",
            "api_keys",
            "system_config",
        ]
        return random.choice(names)

    def _generate_query_duration(self) -> str:
        """Generate database query duration in milliseconds"""
        # Most queries are fast
        if random.random() < 0.9:
            return str(round(random.uniform(0.1, 50), 2))
        else:
            return str(round(random.uniform(50, 1000), 2))

    def _generate_rows_affected(self) -> str:
        """Generate number of rows affected by query"""
        # Most operations affect few rows
        if random.random() < 0.8:
            return str(random.randint(0, 10))
        else:
            return str(random.randint(10, 10000))

    def generate(self, field_type: str, **kwargs) -> str:
        """
        Generate data for specified field type.

        Args:
            field_type: Type of field to generate
            **kwargs: Additional parameters for generation

        Returns:
            Generated data as string
        """
        if field_type in self.generators:
            try:
                generator = self.generators[field_type]
                if kwargs:
                    # Try to pass kwargs to generator if it supports them
                    try:
                        return generator(**kwargs)
                    except TypeError:
                        # Generator doesn't accept kwargs, call without them
                        return generator()
                else:
                    return generator()
            except Exception:
                return ""
        else:
            return ""

    def get_available_generators(self) -> List[str]:
        """Get list of available generator types"""
        return list(self.generators.keys())

    def add_custom_generator(self, field_type: str, generator: Callable) -> None:
        """Add custom generator function"""
        self.generators[field_type] = generator

    def set_frequency_control(
        self, field_type: str, frequency_map: Dict[Any, float]
    ) -> None:
        """
        Set frequency control for a field type.

        Args:
            field_type: Field type to control
            frequency_map: Map of values to their frequencies (probabilities)
        """

        def controlled_generator():
            values = list(frequency_map.keys())
            weights = list(frequency_map.values())
            return str(random.choices(values, weights=weights)[0])

        self.generators[f"{field_type}_controlled"] = controlled_generator
