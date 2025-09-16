"""
Log Generator Tool - 로그 분석기 개발 및 테스트를 위한 자동 로그 생성 도구

이 패키지는 다양한 형태의 로그를 자동으로 생성하여 로그 분석기 개발 및 테스트를 지원합니다.

주요 기능:
- 다양한 로그 타입 지원 (Nginx, Apache, Syslog, FastAPI, Django, Docker, Kubernetes 등)
- 커스터마이징 가능한 로그 패턴
- 실제 에러 패턴 라이브러리
- 다양한 출력 방식 (파일, 콘솔, 네트워크, JSON)
- 고성능 멀티스레딩 지원
- 확장 가능한 플러그인 아키텍처
"""

__version__ = "1.0.1"
__author__ = "Log Generator Team"
__email__ = "team@loggenerator.dev"
__description__ = (
    "Automatic log generation tool for log analyzer development and testing"
)
__url__ = "https://github.com/log-generator/log-generator-tool"
__license__ = "MIT"

from log_generator.core.config import ConfigurationManager

# 주요 클래스들을 패키지 레벨에서 import 가능하게 함
from log_generator.core.engine import LogGeneratorCore
from log_generator.core.factory import LogFactory
from log_generator.core.models import LogEntry

__all__ = [
    "LogGeneratorCore",
    "LogFactory",
    "ConfigurationManager",
    "LogEntry",
    "__version__",
    "__author__",
    "__description__",
]
