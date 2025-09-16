# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Multi-File Output Support**: 로그 타입별 별도 파일 생성 기능
  - `multi_file` 출력 형식 추가
  - 커스터마이징 가능한 파일명 패턴 (`{log_type}_{date}.log`)
  - 로그 타입별 독립적인 파일 로테이션
  - CLI 및 설정 파일에서 멀티 파일 출력 지원

### Changed
- **기본 출력 형식 변경**: `file`에서 `multi_file`로 변경
  - 더 나은 로그 관리를 위해 기본적으로 로그 타입별 별도 파일 생성
  - CLI `--types` 옵션에서 콤마로 구분된 값 지원 개선
- Initial release preparation
- Comprehensive documentation suite
- Docker containerization support
- CI/CD pipeline with GitHub Actions

## [1.0.0] - 2023-12-25

### Added
- **Core Features**
  - Multi-threaded log generation engine
  - Support for 10+ log types (Nginx, Apache, Syslog, FastAPI, Django, Docker, Kubernetes, MySQL, PostgreSQL)
  - Configurable log patterns and custom fields
  - Real-world error pattern library
  - Multiple output formats (file, console, network, JSON)
  - High-performance async I/O support

- **Log Generators**
  - Nginx access and error log generators with realistic patterns
  - Apache web server log generator
  - Syslog generator supporting RFC 3164 and RFC 5424
  - FastAPI application log generator with request tracking
  - Django framework log generator with SQL query logging
  - Docker container log generator with metadata
  - Kubernetes pod and event log generator
  - MySQL and PostgreSQL database log generators

- **Output Handlers**
  - File output with automatic log rotation
  - Console output with color support
  - Network output (TCP/UDP) for remote log servers
  - JSON structured output for modern log pipelines
  - Syslog protocol support for standard log aggregation

- **Pattern System**
  - Faker integration for realistic data generation
  - Custom log pattern templates
  - Error pattern library with frequency control
  - Template parser for dynamic log generation
  - Pattern validation and testing tools

- **Configuration**
  - YAML-based configuration system
  - Multiple configuration templates (basic, advanced, microservices)
  - Runtime configuration updates
  - Environment variable support
  - Configuration validation and error reporting

- **CLI Interface**
  - Comprehensive command-line interface using Typer
  - Real-time monitoring and statistics
  - Interactive configuration management
  - Log generation control (start/stop/pause/resume)
  - Sample log generation and validation tools

- **Performance Features**
  - Multi-threading support for high throughput
  - Configurable batch processing
  - Memory usage optimization
  - Async I/O for network operations
  - Performance monitoring and metrics

- **Quality Assurance**
  - Comprehensive test suite (unit, integration, performance)
  - Log validation and quality checking
  - Error handling and recovery mechanisms
  - Memory leak prevention
  - Performance benchmarking

### Documentation
- **User Documentation**
  - Comprehensive user guide with examples
  - API reference documentation
  - Performance optimization guide
  - Troubleshooting guide with common solutions
  - Configuration templates and examples

- **Developer Documentation**
  - Architecture overview and design decisions
  - Plugin development guide
  - Contributing guidelines
  - Code style and standards
  - Testing procedures

### Deployment
- **Packaging**
  - PyPI package with proper metadata
  - Docker image with multi-stage build
  - Docker Compose for easy deployment
  - GitHub Container Registry support
  - Binary distributions for major platforms

- **CI/CD**
  - GitHub Actions workflow for testing and deployment
  - Automated code quality checks (Black, isort, flake8, mypy)
  - Security scanning (Bandit, Safety)
  - Multi-platform testing (Linux, Windows, macOS)
  - Automated PyPI and Docker Hub publishing

### Configuration Templates
- **Basic Configuration**: Simple setup for getting started
- **Advanced Configuration**: Full-featured setup with all options
- **Microservices Configuration**: Specialized setup for microservices testing
- **Performance Configuration**: Optimized for high-throughput scenarios

### Examples
- Basic usage examples for all log types
- Advanced pattern customization examples
- Performance optimization examples
- Integration examples with popular log analysis tools
- Docker deployment examples

## [0.1.0] - 2023-11-01

### Added
- Initial project structure
- Basic log generation framework
- Core interfaces and abstract classes
- Simple Nginx log generator
- File output handler
- Basic CLI interface

### Development
- Project scaffolding
- Initial test framework
- Basic documentation structure
- Development environment setup

---

## Release Notes

### Version 1.0.0 Highlights

This is the first stable release of Log Generator Tool, providing a comprehensive solution for generating realistic log data for testing and development purposes.

**Key Features:**
- **High Performance**: Generate up to 50,000+ logs per second with optimized multi-threading
- **Realistic Data**: Uses real-world error patterns and log formats collected from production systems
- **Flexible Output**: Support for files, console, network protocols, and structured JSON
- **Easy Configuration**: YAML-based configuration with multiple templates for different use cases
- **Extensible**: Plugin architecture allows easy addition of new log types
- **Production Ready**: Comprehensive testing, documentation, and deployment options

**Use Cases:**
- Log analysis system testing and validation
- Performance testing of log processing pipelines
- Development and debugging of log monitoring tools
- Training and demonstration of log analysis techniques
- Load testing of log aggregation systems

**Getting Started:**
```bash
# Install from PyPI
pip install log-generator-tool

# Generate basic logs
log-generator start

# Use Docker
docker run -v $(pwd)/logs:/app/logs loggenerator/log-generator-tool
```

For detailed usage instructions, see the [User Guide](docs/USER_GUIDE.md).

### Upgrade Notes

This is the initial stable release. Future versions will maintain backward compatibility for configuration files and CLI interfaces.

### Known Issues

- Windows performance may be lower than Linux/macOS due to threading limitations
- Very large log files (>10GB) may require manual log rotation configuration
- Network output may experience delays under high load without proper buffer tuning

### Support

- **Documentation**: https://log-generator-tool.readthedocs.io/
- **Issues**: https://github.com/log-generator/log-generator-tool/issues
- **Discussions**: https://github.com/log-generator/log-generator-tool/discussions
- **Email**: support@loggenerator.dev