"""
Core module - 로그 생성기의 핵심 엔진 및 팩토리 클래스들

이 모듈은 로그 생성 시스템의 핵심 컴포넌트들을 포함합니다:
- 추상 인터페이스 및 기본 클래스
- 데이터 모델
- 예외 클래스
- 핵심 엔진 및 팩토리 구현
"""

from .config import ConfigurationManager as ConfigManager
from .engine import LogGeneratorCore
from .exceptions import (
    ConfigurationError,
    FactoryError,
    GenerationError,
    LogGeneratorError,
    OutputError,
    PatternError,
    ValidationError,
)
from .factory import LogFactory as LogFactoryImpl
from .interfaces import ConfigurationManager, LogFactory, LogGenerator, OutputHandler
from .log_analyzer import LogAnalyzer, LogSample, LogStatistics, QualityReport
from .log_validator import LogValidator, ValidationResult, ValidationStatistics
from .models import GenerationStatistics, LogEntry

__all__ = [
    # Interfaces
    "LogGenerator",
    "OutputHandler",
    "ConfigurationManager",
    "LogFactory",
    # Models
    "LogEntry",
    "GenerationStatistics",
    # Exceptions
    "LogGeneratorError",
    "ConfigurationError",
    "GenerationError",
    "OutputError",
    "ValidationError",
    "FactoryError",
    "PatternError",
    # Implementations
    "ConfigManager",
    "LogGeneratorCore",
    "LogFactoryImpl",
    # Validation and Analysis
    "LogValidator",
    "ValidationResult",
    "ValidationStatistics",
    "LogAnalyzer",
    "LogSample",
    "LogStatistics",
    "QualityReport",
]
