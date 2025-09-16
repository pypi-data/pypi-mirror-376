# Log Generator Tool 사용자 가이드

## 목차

1. [개요](#개요)
2. [설치](#설치)
3. [기본 사용법](#기본-사용법)
4. [설정 파일](#설정-파일)
5. [로그 타입별 사용법](#로그-타입별-사용법)
6. [출력 방식](#출력-방식)
7. [커스터마이징](#커스터마이징)
8. [성능 최적화](#성능-최적화)
9. [모니터링 및 제어](#모니터링-및-제어)

## 개요

Log Generator Tool은 로그 분석기 개발 및 테스트를 위한 자동 로그 생성 도구입니다. 실제 운영 환경과 유사한 다양한 형태의 로그를 생성하여 현실적인 테스트 데이터를 제공합니다.

### 지원하는 로그 타입

- **웹 서버**: Nginx, Apache
- **애플리케이션**: FastAPI, Django
- **시스템**: Syslog, Rsyslog
- **컨테이너**: Docker, Kubernetes
- **데이터베이스**: MySQL, PostgreSQL
- **커스텀**: 사용자 정의 패턴

## 설치

### PyPI에서 설치 (권장)

```bash
pip install log-generator-tool
```

### 소스에서 설치

```bash
git clone https://github.com/your-org/log-generator-tool.git
cd log-generator-tool
pip install -e .
```

### 개발 환경 설치

```bash
pip install -e ".[dev]"
```

## 기본 사용법

### 1. 간단한 로그 생성

```bash
# 기본 설정으로 로그 생성 시작 (멀티 파일 출력)
log-generator start

# 특정 개수의 로그 생성
log-generator start --total 1000

# 특정 로그 타입만 생성
log-generator start --types nginx_access,syslog
```

### 2. 출력 형식 변경

```bash
# 기본값: 멀티 파일 출력 (로그 타입별 별도 파일)
log-generator start

# 단일 파일로 출력
log-generator start --output file --path ./logs/all_logs.log

# 콘솔로 출력
log-generator start --output console
```

### 3. 고급 옵션

```bash
# 생성 간격 조정
log-generator start --interval 0.5  # 0.5초마다 로그 생성

# 네트워크로 전송
log-generator start --output network --host localhost --port 5140

# 설정 파일 사용
log-generator start --config custom_config.yaml
```

### 4. 설정 파일 사용

```bash
# 설정 파일로 실행
log-generator start --config config.yaml

# 설정 파일 생성
log-generator config create --output config.yaml
```

## 설정 파일

### 기본 설정 구조

```yaml
# config.yaml
log_generator:
  global:
    output_format: "file"
    output_path: "./logs"
    generation_interval: 1.0
    total_logs: 10000
    
  log_types:
    nginx_access:
      enabled: true
      frequency: 0.3
      patterns: ["combined", "common"]
      
    syslog:
      enabled: true
      frequency: 0.2
      facilities: ["kern", "mail", "daemon"]
```

### 설정 옵션 설명

#### Global 설정

- `output_format`: 출력 형식 (file, console, network, json)
- `output_path`: 출력 파일 경로
- `generation_interval`: 로그 생성 간격 (초)
- `total_logs`: 총 생성할 로그 수
- `log_rotation`: 로그 로테이션 설정

#### 로그 타입별 설정

- `enabled`: 해당 로그 타입 활성화 여부
- `frequency`: 전체 로그 중 해당 타입의 비율 (0.0-1.0)
- `patterns`: 사용할 로그 패턴 목록
- `custom_fields`: 커스텀 필드 설정

## 로그 타입별 사용법

### Nginx 로그

```yaml
nginx_access:
  enabled: true
  frequency: 0.4
  patterns: ["combined", "common"]
  custom_fields:
    ip_ranges: ["192.168.1.0/24", "10.0.0.0/8"]
    status_codes: {200: 0.7, 404: 0.15, 500: 0.1, 403: 0.05}
    user_agents: 
      - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      - "curl/7.68.0"

nginx_error:
  enabled: true
  frequency: 0.05
  error_levels: ["error", "warn", "crit"]
```

**생성되는 로그 예시:**
```
192.168.1.100 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 1234 "http://example.com" "Mozilla/5.0..."
2023/12/25 10:00:01 [error] 1234#0: *567 connect() failed (111: Connection refused)
```

### Apache 로그

```yaml
apache_access:
  enabled: true
  frequency: 0.3
  log_format: "combined"
  virtual_hosts: ["example.com", "api.example.com"]
```

### Syslog

```yaml
syslog:
  enabled: true
  frequency: 0.2
  facilities: ["kern", "mail", "daemon", "auth"]
  severities: ["info", "notice", "warning", "err"]
  rfc_format: "3164"  # 또는 "5424"
```

**생성되는 로그 예시:**
```
Dec 25 10:00:00 server01 kernel: [12345.678901] Out of memory: Kill process 1234
Dec 25 10:00:01 server01 sshd[5678]: Failed password for root from 192.168.1.100
```

### FastAPI 애플리케이션 로그

```yaml
fastapi:
  enabled: true
  frequency: 0.25
  log_levels: ["INFO", "DEBUG", "WARNING", "ERROR"]
  endpoints: 
    - "/api/users"
    - "/api/orders"
    - "/health"
  include_request_id: true
  include_response_time: true
```

### Docker 로그

```yaml
docker:
  enabled: true
  frequency: 0.1
  container_names: ["web-app", "database", "redis"]
  log_drivers: ["json-file", "syslog"]
```

### Kubernetes 로그

```yaml
kubernetes:
  enabled: true
  frequency: 0.1
  namespaces: ["default", "kube-system", "monitoring"]
  pod_patterns: ["web-*", "api-*", "worker-*"]
```

## 출력 방식

### 1. 멀티 파일 출력 (기본값)

로그 타입별로 별도 파일을 생성하여 관리가 용이합니다.

```yaml
log_generator:
  global:
    output_format: "multi_file"
    output_path: "./logs"
    
    multi_file:
      file_pattern: "{log_type}_{date}.log"  # 파일명 패턴
      date_format: "%Y%m%d"                  # 날짜 형식
      
    # 파일 로테이션 설정
    rotation_size: 104857600  # 100MB
    max_files: 10
```

```bash
# 기본 설정으로 멀티 파일 출력
log-generator start

# 명시적으로 멀티 파일 출력 지정
log-generator start --output multi_file --path ./logs

# 생성되는 파일 예시:
# ./logs/nginx_access_20241215.log
# ./logs/nginx_error_20241215.log
# ./logs/syslog_20241215.log
# ./logs/fastapi_20241215.log
```

**파일명 패턴 변수:**
- `{log_type}`: 로그 타입 (nginx_access, syslog 등)
- `{date}`: 날짜 (date_format에 따라)
- `{time}`: 시간 (HHMMSS)
- `{datetime}`: 날짜와 시간 조합

### 2. 단일 파일 출력

모든 로그를 하나의 파일에 저장합니다.

```yaml
output:
  type: "file"
  file_path: "./logs/output.log"
  rotation:
    max_size: "100MB"
    max_files: 10
    compress: true
```

```bash
# CLI에서 파일 출력
log-generator start --output file --file-path ./logs/output.log
```

### 2. 콘솔 출력

```yaml
output:
  type: "console"
  colored: true
  timestamp: true
```

```bash
# CLI에서 콘솔 출력
log-generator start --output console --colored
```

### 3. 네트워크 출력

```yaml
output:
  type: "network"
  protocol: "tcp"  # 또는 "udp"
  host: "localhost"
  port: 5140
  retry_attempts: 3
```

```bash
# CLI에서 네트워크 출력
log-generator start --output network --host localhost --port 5140
```

### 4. JSON 출력

```yaml
output:
  type: "json"
  structured: true
  include_metadata: true
```

**JSON 출력 예시:**
```json
{
  "timestamp": "2023-12-25T10:00:00Z",
  "log_type": "nginx_access",
  "level": "info",
  "message": "GET /index.html HTTP/1.1",
  "source_ip": "192.168.1.100",
  "status_code": 200,
  "response_time": 0.123,
  "user_agent": "Mozilla/5.0..."
}
```

## 커스터마이징

### 1. 커스텀 로그 패턴

```yaml
custom_patterns:
  my_app_log:
    template: "{timestamp} [{level}] {component}: {message}"
    fields:
      timestamp: "datetime"
      level: ["INFO", "WARN", "ERROR"]
      component: ["auth", "database", "cache"]
      message: "sentence"
```

### 2. 커스텀 필드 생성

```python
# custom_fields.py
from log_generator.patterns.faker_integration import FakerIntegration

faker = FakerIntegration()

# 커스텀 IP 범위
faker.add_ip_range("internal", "10.0.0.0/8")
faker.add_ip_range("dmz", "172.16.0.0/12")

# 커스텀 사용자 에이전트
faker.add_user_agents([
    "MyApp/1.0",
    "InternalBot/2.1"
])
```

### 3. 에러 패턴 추가

```yaml
error_patterns:
  custom_errors:
    - pattern: "Database connection timeout after {timeout}ms"
      frequency: 0.1
      severity: "error"
    - pattern: "Cache miss for key: {cache_key}"
      frequency: 0.3
      severity: "warning"
```

## 성능 최적화

### 1. 멀티스레딩 설정

```yaml
performance:
  threads: 4
  batch_size: 100
  buffer_size: 1000
```

### 2. 메모리 최적화

```yaml
performance:
  memory_limit: "512MB"
  gc_threshold: 1000
  lazy_loading: true
```

### 3. 대용량 로그 생성

```bash
# 대용량 로그 생성 (100만 개)
log-generator start --count 1000000 --threads 8 --batch-size 1000

# 연속 생성 (24시간)
log-generator start --duration 86400 --interval 0.1
```

## 모니터링 및 제어

### 1. 실시간 통계 확인

```bash
# 현재 상태 확인
log-generator status

# 상세 통계 확인
log-generator stats --detailed

# 실시간 모니터링
log-generator monitor
```

### 2. 로그 생성 제어

```bash
# 로그 생성 시작
log-generator start

# 로그 생성 중지
log-generator stop

# 로그 생성 일시정지
log-generator pause

# 로그 생성 재개
log-generator resume
```

### 3. 설정 동적 변경

```bash
# 생성 간격 변경
log-generator config set generation_interval 0.5

# 로그 타입 활성화/비활성화
log-generator config set nginx_access.enabled false
```

## 예제 시나리오

### 시나리오 1: 웹 서버 로그 분석기 테스트

```yaml
# web_server_test.yaml
log_generator:
  global:
    output_format: "file"
    output_path: "./test_logs"
    generation_interval: 0.1
    total_logs: 50000
    
  log_types:
    nginx_access:
      enabled: true
      frequency: 0.6
      patterns: ["combined"]
      custom_fields:
        status_codes: {200: 0.8, 404: 0.1, 500: 0.05, 403: 0.05}
        
    nginx_error:
      enabled: true
      frequency: 0.1
      
    apache_access:
      enabled: true
      frequency: 0.3
```

### 시나리오 2: 마이크로서비스 로그 테스트

```yaml
# microservices_test.yaml
log_generator:
  global:
    output_format: "json"
    output_path: "./microservices_logs"
    
  log_types:
    fastapi:
      enabled: true
      frequency: 0.4
      endpoints: ["/api/users", "/api/orders", "/api/payments"]
      
    docker:
      enabled: true
      frequency: 0.3
      container_names: ["user-service", "order-service", "payment-service"]
      
    kubernetes:
      enabled: true
      frequency: 0.3
      namespaces: ["production", "staging"]
```

### 시나리오 3: 보안 로그 분석 테스트

```yaml
# security_test.yaml
log_generator:
  log_types:
    syslog:
      enabled: true
      frequency: 0.5
      facilities: ["auth", "authpriv"]
      
    nginx_access:
      enabled: true
      frequency: 0.3
      custom_fields:
        status_codes: {401: 0.2, 403: 0.3, 404: 0.3, 200: 0.2}
        
    custom_security:
      enabled: true
      frequency: 0.2
      patterns:
        - "Failed login attempt from {ip} for user {username}"
        - "Suspicious activity detected: {activity}"
```

## 문제 해결

일반적인 문제와 해결 방법은 [트러블슈팅 가이드](TROUBLESHOOTING.md)를 참조하세요.

## 추가 리소스

- [API 참조 문서](API_REFERENCE.md)
- [설정 파일 템플릿](../config/)
- [예제 코드](../examples/)
- [성능 최적화 가이드](PERFORMANCE.md)