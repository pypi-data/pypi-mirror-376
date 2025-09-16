# Log Generator Tool API 참조 문서

## 목차

1. [Core API](#core-api)
2. [Configuration API](#configuration-api)
3. [Generator API](#generator-api)
4. [Output Handler API](#output-handler-api)
5. [Pattern API](#pattern-api)
6. [CLI API](#cli-api)
7. [예외 처리](#예외-처리)

## Core API

### LogGeneratorCore

로그 생성의 핵심 엔진 클래스입니다.

```python
from log_generator.core.engine import LogGeneratorCore

class LogGeneratorCore:
    def __init__(self, config_path: str = None, config_dict: Dict = None)
    def start_generation(self) -> None
    def stop_generation(self) -> None
    def pause_generation(self) -> None
    def resume_generation(self) -> None
    def get_statistics(self) -> Dict[str, Any]
    def add_log_type(self, log_type: str, generator: LogGenerator) -> None
    def remove_log_type(self, log_type: str) -> None
    def is_running(self) -> bool
```

#### 사용 예제

```python
# 기본 사용법
core = LogGeneratorCore("config.yaml")
core.start_generation()

# 통계 확인
stats = core.get_statistics()
print(f"Generated logs: {stats['total_logs']}")

# 중지
core.stop_generation()
```

#### 메서드 상세

##### `__init__(config_path: str = None, config_dict: Dict = None)`

**매개변수:**
- `config_path`: 설정 파일 경로
- `config_dict`: 설정 딕셔너리 (config_path와 둘 중 하나만 사용)

**예외:**
- `ConfigurationError`: 설정 파일이 유효하지 않은 경우

##### `start_generation() -> None`

로그 생성을 시작합니다.

**예외:**
- `GenerationError`: 이미 실행 중이거나 설정에 오류가 있는 경우

##### `get_statistics() -> Dict[str, Any]`

현재 생성 통계를 반환합니다.

**반환값:**
```python
{
    "total_logs": 1000,
    "logs_per_second": 10.5,
    "running_time": 95.2,
    "log_types": {
        "nginx_access": 600,
        "syslog": 300,
        "fastapi": 100
    },
    "errors": 2,
    "status": "running"
}
```

### LogFactory

로그 생성기 인스턴스를 생성하고 관리하는 팩토리 클래스입니다.

```python
from log_generator.core.factory import LogFactory

class LogFactory:
    @staticmethod
    def create_generator(log_type: str, config: Dict[str, Any]) -> LogGenerator
    @staticmethod
    def get_available_types() -> List[str]
    @staticmethod
    def register_generator(log_type: str, generator_class: Type[LogGenerator]) -> None
```

#### 사용 예제

```python
# 사용 가능한 로그 타입 확인
types = LogFactory.get_available_types()
print(types)  # ['nginx', 'apache', 'syslog', 'fastapi', ...]

# 특정 생성기 생성
config = {"patterns": ["combined"], "frequency": 0.3}
nginx_gen = LogFactory.create_generator("nginx", config)

# 커스텀 생성기 등록
LogFactory.register_generator("custom_app", CustomAppGenerator)
```

## Configuration API

### ConfigurationManager

설정 파일을 로드하고 관리하는 클래스입니다.

```python
from log_generator.core.config import ConfigurationManager

class ConfigurationManager:
    def __init__(self, config_path: str = None)
    def load_config(self, path: str) -> Dict[str, Any]
    def save_config(self, config: Dict[str, Any], path: str) -> None
    def validate_config(self, config: Dict[str, Any]) -> bool
    def get_log_type_config(self, log_type: str) -> Dict[str, Any]
    def update_config(self, updates: Dict[str, Any]) -> None
    def get_default_config(self) -> Dict[str, Any]
```

#### 사용 예제

```python
# 설정 로드
config_manager = ConfigurationManager("config.yaml")
config = config_manager.load_config("config.yaml")

# 설정 검증
is_valid = config_manager.validate_config(config)

# 특정 로그 타입 설정 가져오기
nginx_config = config_manager.get_log_type_config("nginx_access")

# 설정 업데이트
config_manager.update_config({
    "log_types.nginx_access.frequency": 0.5
})
```

## Generator API

### 기본 LogGenerator 인터페이스

모든 로그 생성기가 구현해야 하는 기본 인터페이스입니다.

```python
from abc import ABC, abstractmethod
from log_generator.core.interfaces import LogGenerator

class LogGenerator(ABC):
    @abstractmethod
    def generate_log(self) -> str
    
    @abstractmethod
    def get_log_pattern(self) -> str
    
    @abstractmethod
    def validate_log(self, log_entry: str) -> bool
    
    def set_custom_fields(self, fields: Dict[str, Any]) -> None
    def get_sample_logs(self, count: int = 5) -> List[str]
    def get_statistics(self) -> Dict[str, Any]
```

### 구체적인 생성기들

#### NginxAccessLogGenerator

```python
from log_generator.generators.nginx import NginxAccessLogGenerator

class NginxAccessLogGenerator(LogGenerator):
    def __init__(self, config: Dict[str, Any])
    def generate_log(self) -> str
    def set_log_format(self, format_type: str) -> None  # "common", "combined"
    def set_ip_ranges(self, ip_ranges: List[str]) -> None
    def set_status_code_distribution(self, distribution: Dict[int, float]) -> None
```

**사용 예제:**
```python
config = {
    "patterns": ["combined"],
    "custom_fields": {
        "ip_ranges": ["192.168.1.0/24"],
        "status_codes": {200: 0.8, 404: 0.15, 500: 0.05}
    }
}

nginx_gen = NginxAccessLogGenerator(config)
log_entry = nginx_gen.generate_log()
print(log_entry)
# 출력: 192.168.1.100 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 1234
```

#### SyslogGenerator

```python
from log_generator.generators.syslog import SyslogGenerator

class SyslogGenerator(LogGenerator):
    def __init__(self, rfc_format: str = "3164", custom_config: Dict[str, Any] = None)
    def set_facility(self, facility: str) -> None
    def set_severity(self, severity: str) -> None
    def set_rfc_format(self, rfc: str) -> None  # "3164", "5424"
```

**사용 예제:**
```python
# 기본 사용법
syslog_gen = SyslogGenerator()

# RFC 5424 형식으로 설정
syslog_gen = SyslogGenerator(rfc_format="5424")

# 커스텀 설정으로 생성
custom_config = {
    "hostname": "web-server-01",
    "priority_style": "bracket",  # "pri", "bracket", "plain", "none"
    "facilities": {
        "daemon": 0.4,
        "auth": 0.3,
        "mail": 0.2,
        "kern": 0.1
    },
    "severities": {
        "info": 0.5,
        "warning": 0.3,
        "error": 0.2
    }
}
syslog_gen = SyslogGenerator(rfc_format="3164", custom_config=custom_config)

log_entry = syslog_gen.generate_log()
print(log_entry)
# 출력 (priority_style="bracket"): [daemon.info]Dec 25 10:00:00 web-server-01 nginx[1234]: Starting nginx daemon
```

**custom_config 옵션:**
- `hostname`: 로그에 사용할 호스트명 (기본값: 시스템 호스트명)
- `priority_style`: 우선순위 표시 방식
  - `"pri"`: `<134>` (숫자 PRI 형식)
  - `"bracket"`: `[local0.info]` (대괄호 형식)
  - `"plain"`: `local0.info ` (평문 형식)
  - `"none"`: 우선순위 프리픽스 없음
- `facilities`: 시설(facility) 분포 설정 (딕셔너리)
- `severities`: 심각도(severity) 분포 설정 (딕셔너리)

#### FastAPILogGenerator

```python
from log_generator.generators.fastapi import FastAPILogGenerator

class FastAPILogGenerator(LogGenerator):
    def __init__(self, config: Dict[str, Any])
    def set_endpoints(self, endpoints: List[str]) -> None
    def set_log_levels(self, levels: List[str]) -> None
    def include_request_id(self, include: bool) -> None
    def include_response_time(self, include: bool) -> None
```

## Output Handler API

### 기본 OutputHandler 인터페이스

```python
from abc import ABC, abstractmethod
from log_generator.core.interfaces import OutputHandler

class OutputHandler(ABC):
    @abstractmethod
    def write_log(self, log_entry: str) -> None
    
    @abstractmethod
    def close(self) -> None
    
    def flush(self) -> None
    def get_statistics(self) -> Dict[str, Any]
```

### 구체적인 출력 핸들러들

#### MultiFileOutputHandler (기본값)

로그 타입별로 별도 파일을 생성하는 출력 핸들러입니다.

```python
from log_generator.outputs.multi_file_handler import MultiFileOutputHandler

class MultiFileOutputHandler(OutputHandler):
    def __init__(self, base_path: str, file_pattern: str = "{log_type}_{date}.log")
    def write_log(self, log_entry: str, log_type: str = "default") -> None
    def get_active_log_types(self) -> List[str]
    def get_file_path_for_type(self, log_type: str) -> Path
```

**사용 예제:**
```python
# 기본 멀티 파일 출력
multi_handler = MultiFileOutputHandler("./logs")

# 커스텀 파일 패턴
multi_handler = MultiFileOutputHandler(
    base_path="./logs",
    file_pattern="{log_type}_{datetime}.log",
    date_format="%Y%m%d_%H%M%S"
)

# 로그 쓰기 (로그 타입별로 자동 분류)
multi_handler.write_log("Nginx access log", log_type="nginx_access")
multi_handler.write_log("System log", log_type="syslog")
```

#### FileOutputHandler

```python
from log_generator.outputs.file_handler import FileOutputHandler

class FileOutputHandler(OutputHandler):
    def __init__(self, file_path: str, rotation_config: Dict = None)
    def write_log(self, log_entry: str) -> None
    def rotate_log(self) -> None
    def set_rotation_policy(self, policy: Dict[str, Any]) -> None
```

**사용 예제:**
```python
# 기본 파일 출력
file_handler = FileOutputHandler("./logs/output.log")

# 로테이션 설정
rotation_config = {
    "max_size": "100MB",
    "max_files": 10,
    "compress": True
}
file_handler = FileOutputHandler("./logs/output.log", rotation_config)

# 로그 쓰기
file_handler.write_log("Sample log entry")
file_handler.close()
```

#### NetworkOutputHandler

```python
from log_generator.outputs.network_handler import NetworkOutputHandler

class NetworkOutputHandler(OutputHandler):
    def __init__(self, host: str, port: int, protocol: str = "tcp")
    def write_log(self, log_entry: str) -> None
    def reconnect(self) -> None
    def set_retry_policy(self, max_retries: int, retry_delay: float) -> None
```

#### JSONOutputHandler

```python
from log_generator.outputs.json_handler import JSONOutputHandler

class JSONOutputHandler(OutputHandler):
    def __init__(self, output_handler: OutputHandler, structured: bool = True)
    def write_log(self, log_entry: str) -> None
    def set_metadata_fields(self, fields: List[str]) -> None
```

## Pattern API

### PatternManager

로그 패턴을 관리하는 클래스입니다.

```python
from log_generator.patterns.pattern_manager import PatternManager

class PatternManager:
    def __init__(self)
    def add_pattern(self, name: str, pattern: str) -> None
    def get_pattern(self, name: str) -> str
    def list_patterns(self) -> List[str]
    def remove_pattern(self, name: str) -> None
    def validate_pattern(self, pattern: str) -> bool
```

### TemplateParser

템플릿 기반 로그 생성을 위한 파서입니다.

```python
from log_generator.patterns.template_parser import TemplateParser

class TemplateParser:
    def __init__(self, template: str)
    def parse(self, data: Dict[str, Any]) -> str
    def get_required_fields(self) -> List[str]
    def validate_template(self) -> bool
```

**사용 예제:**
```python
# 템플릿 정의
template = "{timestamp} [{level}] {component}: {message}"
parser = TemplateParser(template)

# 데이터로 로그 생성
data = {
    "timestamp": "2023-12-25 10:00:00",
    "level": "INFO",
    "component": "auth",
    "message": "User login successful"
}
log_entry = parser.parse(data)
print(log_entry)
# 출력: 2023-12-25 10:00:00 [INFO] auth: User login successful
```

### FakerIntegration

Faker 라이브러리와의 통합을 제공합니다.

```python
from log_generator.patterns.faker_integration import FakerIntegration

class FakerIntegration:
    def __init__(self, locale: str = "en_US")
    def generate_ip(self, ip_range: str = None) -> str
    def generate_user_agent(self) -> str
    def generate_timestamp(self, format_str: str = None) -> str
    def generate_http_status_code(self, distribution: Dict[int, float] = None) -> int
    def add_custom_provider(self, provider_name: str, provider_class: Type) -> None
```

## CLI API

### 명령줄 인터페이스

CLI는 Typer 라이브러리를 사용하여 구현되었습니다.

```python
from log_generator.cli import app

# 프로그래밍 방식으로 CLI 실행
import typer

# 로그 생성 시작
typer.run(app, ["start", "--type", "nginx", "--count", "1000"])

# 설정 파일 생성
typer.run(app, ["config", "create", "--output", "config.yaml"])
```

### CLI 명령어

#### start

```bash
log-generator start [OPTIONS]
```

**옵션:**
- `--config PATH`: 설정 파일 경로
- `--type TEXT`: 로그 타입 (쉼표로 구분)
- `--count INTEGER`: 생성할 로그 수
- `--duration INTEGER`: 실행 시간 (초)
- `--interval FLOAT`: 생성 간격 (초, 기본값: 0.1)
- `--random-interval/--fixed-interval`: 랜덤 간격 사용 여부 (기본값: 고정 간격)
- `--output [file|console|network|json]`: 출력 방식
- `--file-path PATH`: 출력 파일 경로
- `--host TEXT`: 네트워크 호스트
- `--port INTEGER`: 네트워크 포트

**사용 예제:**
```bash
# 기본 로그 생성 (고정 간격)
log-generator start --interval 1.0

# 랜덤 간격으로 로그 생성 (0~5초 사이)
log-generator start --interval 5.0 --random-interval

# 특정 로그 타입만 랜덤 간격으로 생성
log-generator start --types nginx_access,syslog --interval 2.0 --random-interval
```

#### config

```bash
log-generator config [COMMAND] [OPTIONS]
```

**하위 명령어:**
- `create`: 새 설정 파일 생성
- `validate`: 설정 파일 검증
- `show`: 현재 설정 표시
- `set`: 설정 값 변경

#### status

```bash
log-generator status [OPTIONS]
```

**옵션:**
- `--detailed`: 상세 정보 표시
- `--json`: JSON 형식으로 출력

## 예외 처리

### 예외 클래스 계층

```python
class LogGeneratorError(Exception):
    """기본 예외 클래스"""
    pass

class ConfigurationError(LogGeneratorError):
    """설정 관련 오류"""
    pass

class GenerationError(LogGeneratorError):
    """로그 생성 관련 오류"""
    pass

class OutputError(LogGeneratorError):
    """출력 관련 오류"""
    pass

class ValidationError(LogGeneratorError):
    """검증 관련 오류"""
    pass

class PatternError(LogGeneratorError):
    """패턴 관련 오류"""
    pass
```

### 예외 처리 예제

```python
from log_generator.core.exceptions import *

try:
    core = LogGeneratorCore("invalid_config.yaml")
    core.start_generation()
except ConfigurationError as e:
    print(f"설정 오류: {e}")
except GenerationError as e:
    print(f"생성 오류: {e}")
except Exception as e:
    print(f"예상치 못한 오류: {e}")
```

## 확장 가이드

### 커스텀 로그 생성기 작성

```python
from log_generator.core.interfaces import LogGenerator
from typing import Dict, Any, List

class CustomAppLogGenerator(LogGenerator):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.custom_fields = {}
        
    def generate_log(self) -> str:
        # 커스텀 로그 생성 로직
        timestamp = self._generate_timestamp()
        level = self._generate_level()
        message = self._generate_message()
        
        return f"{timestamp} [{level}] {message}"
        
    def get_log_pattern(self) -> str:
        return r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[.*\] .*$"
        
    def validate_log(self, log_entry: str) -> bool:
        import re
        pattern = self.get_log_pattern()
        return bool(re.match(pattern, log_entry))
        
    def set_custom_fields(self, fields: Dict[str, Any]) -> None:
        self.custom_fields.update(fields)

# 팩토리에 등록
from log_generator.core.factory import LogFactory
LogFactory.register_generator("custom_app", CustomAppLogGenerator)
```

### 커스텀 출력 핸들러 작성

```python
from log_generator.core.interfaces import OutputHandler
import requests

class WebhookOutputHandler(OutputHandler):
    def __init__(self, webhook_url: str, batch_size: int = 10):
        self.webhook_url = webhook_url
        self.batch_size = batch_size
        self.buffer = []
        
    def write_log(self, log_entry: str) -> None:
        self.buffer.append(log_entry)
        if len(self.buffer) >= self.batch_size:
            self._send_batch()
            
    def _send_batch(self) -> None:
        payload = {"logs": self.buffer}
        response = requests.post(self.webhook_url, json=payload)
        response.raise_for_status()
        self.buffer.clear()
        
    def close(self) -> None:
        if self.buffer:
            self._send_batch()
```

## 성능 고려사항

### 메모리 사용량 최적화

```python
# 대용량 로그 생성 시 메모리 효율적인 방법
from log_generator.core.engine import LogGeneratorCore

config = {
    "performance": {
        "batch_size": 1000,
        "buffer_size": 10000,
        "lazy_loading": True
    }
}

core = LogGeneratorCore(config_dict=config)
```

### 멀티스레딩 활용

```python
# 멀티스레드 설정
config = {
    "performance": {
        "threads": 4,
        "thread_pool_size": 8
    }
}
```

### 랜덤 간격 설정

```python
# 랜덤 간격으로 로그 생성 (0~5초 사이)
config = {
    "log_generator": {
        "global": {
            "generation_interval": 5.0,
            "random_interval": True
        }
    }
}

core = LogGeneratorCore(config_dict=config)
core.start_generation()
```

**랜덤 간격 옵션:**
- `random_interval: false` (기본값): 고정 간격으로 로그 생성
- `random_interval: true`: 0부터 `generation_interval` 사이의 랜덤 간격으로 로그 생성

이 기능은 더 현실적인 로그 패턴을 시뮬레이션하는 데 유용합니다. 실제 시스템에서는 로그가 일정한 간격으로 생성되지 않기 때문입니다.

이 API 참조 문서는 Log Generator Tool의 모든 주요 클래스와 메서드에 대한 상세한 정보를 제공합니다. 각 API의 사용법과 예제를 통해 개발자가 도구를 효과적으로 활용할 수 있도록 돕습니다.