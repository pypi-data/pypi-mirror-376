# Log Generator Tool

A comprehensive Python tool for generating realistic log data for testing and development of log analysis systems.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Log Generator Tool is designed to help developers and testers create realistic log data for various applications and systems. It supports multiple log formats including Nginx, Apache, system logs, application logs, and more.

### Key Benefits

- **Realistic Data**: Generates logs that closely mimic real-world patterns
- **Multiple Formats**: Support for 9+ different log types
- **Customizable**: Flexible configuration and custom pattern support
- **High Performance**: Efficient generation for large datasets
- **Easy Integration**: Simple CLI and Python API

## Features

### Supported Log Types

- **Web Servers**: Nginx (access/error), Apache
- **Applications**: FastAPI, Django
- **Systems**: Syslog, rsyslog
- **Containers**: Docker, Kubernetes
- **Databases**: MySQL, PostgreSQL

### Output Options

- **File Output**: With automatic rotation support
- **Console Output**: Real-time display with color coding
- **Network Output**: TCP/UDP streaming
- **JSON Format**: Structured logging support

### Advanced Features

- **Error Pattern Library**: Real-world error scenarios
- **Custom Templates**: User-defined log patterns
- **Frequency Control**: Configurable generation rates
- **Statistics**: Real-time generation monitoring
- **Validation**: Built-in log format verification

## Installation

### From PyPI (Recommended)

```bash
pip install log-generator-tool
```

### From Source

```bash
git clone https://github.com/your-org/log-generator-tool.git
cd log-generator-tool
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/your-org/log-generator-tool.git
cd log-generator-tool
pip install -e ".[dev]"
```

## Quick Start

### Command Line Usage

1. **Generate basic logs**:
```bash
log-generator start --config config/default_config.yaml
```

2. **Generate specific log types**:
```bash
log-generator start --types nginx,fastapi --output ./logs
```

3. **Real-time console output**:
```bash
log-generator start --output console --count 100
```

### Python API Usage

```python
from log_generator import LogGeneratorCore
from log_generator.core.factory import LogFactory
from log_generator.outputs.file_handler import FileOutputHandler

# Initialize core engine
core = LogGeneratorCore("config/default_config.yaml")

# Set up factory and output
factory = LogFactory()
core.set_log_factory(factory)
core.add_output_handler(FileOutputHandler("./logs/output.log"))

# Start generation
core.start_generation()

# Get statistics
stats = core.get_statistics()
print(f"Generated {stats['total_logs_generated']} logs")

# Stop generation
core.stop_generation()
```

## Configuration

### Basic Configuration File

Create a `config.yaml` file:

```yaml
log_generator:
  global:
    output_format: "file"
    output_path: "./logs"
    generation_interval: 1.0
    total_logs: 10000
    
  log_types:
    nginx_access:
      enabled: true
      frequency: 0.4
      patterns: ["combined", "common"]
      custom_fields:
        ip_ranges: ["192.168.1.0/24", "10.0.0.0/8"]
        status_codes: {200: 0.7, 404: 0.15, 500: 0.1, 403: 0.05}
        
    fastapi:
      enabled: true
      frequency: 0.2
      log_levels: ["INFO", "DEBUG", "WARNING", "ERROR"]
      endpoints: ["/api/users", "/api/orders", "/health"]
```

### Configuration Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `output_format` | string | Output format (file/console/network/json) | "file" |
| `output_path` | string | Output directory path | "./logs" |
| `generation_interval` | float | Seconds between log generations | 1.0 |
| `total_logs` | integer | Total number of logs to generate | 10000 |
| `enabled` | boolean | Enable/disable log type | false |
| `frequency` | float | Relative frequency (0.0-1.0) | 0.1 |

## Usage Examples

### Example 1: Web Server Log Testing

```python
from log_generator import LogGeneratorCore
from log_generator.generators.nginx import NginxAccessLogGenerator
from log_generator.outputs.file_handler import FileOutputHandler

# Create generator for nginx logs
generator = NginxAccessLogGenerator()
generator.set_custom_fields({
    "ip_ranges": ["192.168.1.0/24"],
    "status_codes": {200: 0.8, 404: 0.15, 500: 0.05}
})

# Generate sample logs
samples = generator.get_sample_logs(5)
for log in samples:
    print(log)
```

### Example 2: Application Error Testing

```python
from log_generator.patterns.error_manager import ErrorManager
from log_generator.generators.fastapi import FastAPILogGenerator

# Set up error patterns
error_manager = ErrorManager()
error_manager.load_patterns("error_patterns/")

# Generate application logs with errors
generator = FastAPILogGenerator()
generator.set_error_manager(error_manager)

# Generate logs with 10% error rate
for _ in range(100):
    log = generator.generate_log()
    print(log)
```

### Example 3: Custom Log Patterns

```python
from log_generator.patterns.template_parser import TemplateParser
from log_generator.generators.custom import CustomLogGenerator

# Define custom template
template = "{timestamp} [{level}] {service}: {message} (user={user_id})"

# Create custom generator
parser = TemplateParser()
generator = CustomLogGenerator(template, parser)

# Set custom field generators
generator.set_custom_fields({
    "service": ["auth", "api", "db"],
    "user_id": "uuid4",
    "level": ["INFO", "WARN", "ERROR"]
})

# Generate custom logs
log = generator.generate_log()
print(log)
```

### Example 4: Network Streaming

```python
from log_generator.outputs.network_handler import NetworkOutputHandler
from log_generator import LogGeneratorCore

# Set up network output
network_handler = NetworkOutputHandler("localhost", 5140, "tcp")

# Configure core with network output
core = LogGeneratorCore("config.yaml")
core.add_output_handler(network_handler)

# Stream logs to network
core.start_generation()
```

### Example 5: Real-time Monitoring

```python
import time
from log_generator import LogGeneratorCore

core = LogGeneratorCore("config.yaml")

# Start generation in background
core.start_generation()

# Monitor progress
while core.is_running():
    stats = core.get_statistics()
    print(f"Generated: {stats['total_logs_generated']}, "
          f"Rate: {stats['generation_rate']:.2f} logs/sec")
    time.sleep(5)
```

## CLI Reference

### Commands

#### `start`
Start log generation with specified configuration.

```bash
log-generator start [OPTIONS]
```

**Options:**
- `--config PATH`: Configuration file path
- `--types TEXT`: Comma-separated log types to generate
- `--output PATH`: Output directory or format
- `--count INTEGER`: Number of logs to generate
- `--interval FLOAT`: Generation interval in seconds
- `--verbose`: Enable verbose output

#### `validate`
Validate configuration file.

```bash
log-generator validate --config PATH
```

#### `sample`
Generate sample logs for testing.

```bash
log-generator sample --type TYPE --count INTEGER
```

#### `stats`
Show generation statistics.

```bash
log-generator stats
```

### Examples

```bash
# Generate 1000 nginx logs
log-generator start --types nginx_access --count 1000 --output ./test_logs

# Validate configuration
log-generator validate --config my_config.yaml

# Generate samples for testing
log-generator sample --type fastapi --count 10

# Real-time console output
log-generator start --output console --interval 0.5
```

## Troubleshooting

### Common Issues

1. **Configuration Errors**
   - Ensure YAML syntax is correct
   - Check that all required fields are present
   - Verify frequency values sum to ≤ 1.0

2. **Permission Errors**
   - Check write permissions for output directory
   - Ensure network ports are available

3. **Performance Issues**
   - Reduce generation interval for higher throughput
   - Use file output instead of console for large volumes
   - Consider memory usage with large log counts

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or use CLI verbose mode:

```bash
log-generator start --verbose --config config.yaml
```

## Advanced Usage

### Custom Log Generators

Create your own log generator by extending the base class:

```python
from log_generator.core.interfaces import LogGenerator
import random

class MyCustomGenerator(LogGenerator):
    def generate_log(self) -> str:
        return f"CUSTOM: {random.choice(['INFO', 'ERROR'])} - Custom message"
    
    def get_log_pattern(self) -> str:
        return r"CUSTOM: (INFO|ERROR) - .*"
    
    def validate_log(self, log_entry: str) -> bool:
        return log_entry.startswith("CUSTOM:")
```

### Error Pattern Management

Add custom error patterns:

```python
from log_generator.patterns.error_manager import ErrorManager

error_manager = ErrorManager()
error_manager.add_pattern("custom_error", {
    "pattern": "Database connection failed: {error_detail}",
    "frequency": 0.05,
    "severity": "ERROR"
})
```

### Performance Optimization

For high-volume generation:

```python
# Use batch processing
core = LogGeneratorCore()
core.set_batch_size(1000)  # Process in batches

# Use multiple threads
core.set_thread_count(4)

# Optimize output buffering
file_handler = FileOutputHandler("output.log", buffer_size=8192)
```

## API Reference

See [API Documentation](api/README.md) for detailed class and method documentation.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/your-org/log-generator-tool.git
cd log-generator-tool
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black log_generator/
flake8 log_generator/
mypy log_generator/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.