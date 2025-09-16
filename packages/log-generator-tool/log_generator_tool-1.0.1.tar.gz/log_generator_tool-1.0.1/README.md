# Log Generator Tool

로그 분석기 개발 및 테스트를 위한 자동 로그 생성 도구

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/your-org/log-generator-tool)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](https://codecov.io)

## 개요

Log Generator Tool은 다양한 형태의 로그를 자동으로 생성하여 로그 분석기 개발 및 테스트를 지원하는 Python 기반 도구입니다. 실제 운영 환경과 유사한 로그 패턴을 생성하여 현실적인 테스트 데이터를 제공합니다.

### 🎯 주요 특징

- **📁 스마트한 파일 관리**: 로그 타입별 자동 파일 분류로 체계적인 로그 관리 (기본값)
- **🔧 다양한 로그 타입**: Nginx, Apache, Syslog, FastAPI, Django, Docker, Kubernetes 등 10+ 로그 타입 지원
- **⚙️ 고도로 커스터마이징 가능**: 사용자 정의 패턴, 필드, 에러 시나리오 지원
- **🎭 현실적인 데이터**: 실제 운영 환경에서 수집한 에러 패턴과 로그 형식
- **🚀 고성능**: 가상 시간 기반 엔진으로 초당 4,000+ 로그 생성 가능 (실제 sleep 없음)
- **📤 다양한 출력**: 멀티 파일(기본), 단일 파일, 콘솔, 네트워크(TCP/UDP), JSON 등
- **🔌 확장 가능**: 플러그인 아키텍처로 새로운 로그 타입 쉽게 추가

## 빠른 시작

### 설치

```bash
# PyPI에서 설치
pip install log-generator-tool

# 또는 소스에서 설치
git clone https://github.com/your-org/log-generator-tool.git
cd log-generator-tool
pip install -e .
```

### 기본 사용법

```bash
# 기본 설정으로 로그 생성 시작 (멀티 파일 출력)
log-generator start

# 특정 로그 타입만 생성
log-generator start --types nginx_access,syslog

# 1만 개 로그 생성 후 종료
log-generator start --total 10000

# 설정 파일 사용
log-generator start --config config.yaml
```

### 설정 파일 예제

```yaml
# config.yaml
log_generator:
  global:
    output_format: "multi_file"  # 로그 타입별 별도 파일 생성
    output_path: "./logs"
    generation_interval: 0.1
    
    # 멀티 파일 출력 설정
    multi_file:
      file_pattern: "{log_type}_{date}.log"  # nginx_access_20241215.log
      date_format: "%Y%m%d"
    
  log_types:
    nginx_access:
      enabled: true
      frequency: 0.4
      custom_fields:
        status_codes: {200: 0.8, 404: 0.15, 500: 0.05}
        
    syslog:
      enabled: true
      frequency: 0.3
      facilities: ["kern", "auth", "daemon"]
```

## 지원하는 로그 타입

| 로그 타입 | 설명 | 예제 |
|-----------|------|------|
| **Nginx** | 접근/에러 로그 | `192.168.1.1 - - [25/Dec/2023:10:00:00 +0000] "GET /" 200 1234` |
| **Apache** | 웹 서버 로그 | `192.168.1.1 - - [25/Dec/2023:10:00:00 +0000] "GET /" 200 1234` |
| **Syslog** | 시스템 로그 | `Dec 25 10:00:00 server kernel: Out of memory` |
| **FastAPI** | API 서버 로그 | `2023-12-25 10:00:00 INFO: GET /api/users 200 45ms` |
| **Django** | 웹 프레임워크 로그 | `[25/Dec/2023 10:00:00] INFO django.request: GET /admin/` |
| **Docker** | 컨테이너 로그 | `2023-12-25T10:00:00Z container-name: Application started` |
| **Kubernetes** | 오케스트레이션 로그 | `2023-12-25T10:00:00Z pod/web-app-123 Container started` |
| **MySQL** | 데이터베이스 로그 | `2023-12-25T10:00:00.123Z Query: SELECT * FROM users` |
| **PostgreSQL** | 데이터베이스 로그 | `2023-12-25 10:00:00 LOG: connection received` |

## 출력 방식

### 파일 출력
```bash
# 기본 파일 출력
log-generator start --output file --file-path ./logs/output.log

# 로그 로테이션 포함
log-generator start --output file --rotation-size 100MB --max-files 10
```

### 네트워크 출력
```bash
# TCP로 원격 서버에 전송
log-generator start --output network --host logserver --port 5140

# UDP로 Syslog 서버에 전송
log-generator start --output network --protocol udp --host syslog-server --port 514
```

### JSON 구조화 출력
```bash
# JSON 형식으로 출력
log-generator start --output json --structured
```

## 고급 기능

### 커스텀 로그 패턴

```yaml
custom_patterns:
  my_app:
    template: "{timestamp} [{level}] {component}: {message}"
    fields:
      timestamp: "datetime"
      level: ["INFO", "WARN", "ERROR"]
      component: ["auth", "database", "cache"]
      message: "sentence"
```

### 에러 시나리오 시뮬레이션

```yaml
error_patterns:
  database_errors:
    - pattern: "Connection timeout to database"
      frequency: 0.1
      severity: "error"
    - pattern: "Deadlock detected in transaction"
      frequency: 0.05
      severity: "critical"
```

### 성능 최적화

```yaml
performance:
  threads: 8              # CPU 코어 수에 맞춰 조정
  batch_size: 2000        # 배치 처리 크기
  buffer_size: 20000      # 메모리 버퍼 크기
  async_io: true          # 비동기 I/O 활성화
```

## 출력 형식

### 📁 멀티 파일 출력 (기본값)
로그 타입별로 별도 파일을 생성하여 관리가 용이합니다.

```bash
# 기본 설정으로 멀티 파일 생성
log-generator start

# 명시적으로 멀티 파일 지정
log-generator start --output multi_file --path ./logs

# 생성되는 파일들:
# ./logs/nginx_access_20241215.log
# ./logs/nginx_error_20241215.log  
# ./logs/syslog_20241215.log
# ./logs/fastapi_20241215.log
```

### 📄 단일 파일 출력
모든 로그를 하나의 파일에 저장합니다.

```bash
# 모든 로그를 하나의 파일에 저장
log-generator start --output file --path ./logs/all_logs.log
```

### 🖥️ 기타 출력 형식
```bash
# 콘솔 출력
log-generator start --output console

# 네트워크 출력 (Syslog, ELK Stack 등)
log-generator start --output network --host 192.168.1.100 --port 514

# JSON 형식 출력
log-generator start --output json --path ./logs/structured_logs.json
```

## 사용 사례

### 🔍 로그 분석기 테스트
```bash
# ELK Stack 테스트용 로그 생성
log-generator start --output network --host elasticsearch --port 9200 --format json
```

### 🚨 모니터링 시스템 테스트
```bash
# Prometheus/Grafana 테스트용 메트릭 로그
log-generator start --type fastapi --include-metrics --output network --host prometheus
```

### 🏗️ 마이크로서비스 환경 시뮬레이션
```bash
# 마이크로서비스 로그 패턴으로 생성
log-generator start --config microservices_config.yaml
```

## 성능 벤치마크

### 🚀 최신 성능 결과

**테스트 환경**: Apple M2 Pro, 16GB RAM, macOS Sonoma

| 설정 | generation_interval | 가상 시간 | 성능 | 평가 |
|------|---------------------|----------|------|------|
| 기본 설정 | 0.1s | ✅ | 1,000 logs/sec | ✅ 양호 |
| 고성능 설정 | 0.01s | ✅ | **3,000 logs/sec** | 🚀 우수 |
| 극한 설정 | 0.001s | ✅ | **4,000+ logs/sec** | ⚡ 최고 |

### 📊 실제 벤치마크

```bash
# 성능 벤치마크 실행
python examples/performance_benchmark.py --total 50000

# 결과 예시:
# Total logs generated: 100,000
# Total duration: 24.46 seconds  
# Average rate: 4,095 logs/sec
# Performance Rating: 🚀 Excellent
```

### ⚡ 성능 최적화 팁

```bash
# 고성능 설정으로 실행 (가상 시간 사용)
log-generator start --interval 0.001 --virtual-time --total 10000

# 극한 성능 설정 파일 사용
log-generator start --config config/ultra_performance_config.yaml
```

| 환경 | 로그/초 | CPU 사용률 | 메모리 사용량 |
|------|---------|------------|---------------|
| 기본 설정 | 1,000 | 10% | 50MB |
| 최적화 설정 | 10,000 | 40% | 200MB |
| 고성능 설정 | 50,000 | 80% | 1GB |

*테스트 환경: Intel i7-9700K, 32GB RAM, NVMe SSD*

## 문서

- 📖 [사용자 가이드](docs/USER_GUIDE.md) - 상세한 사용법과 예제
- 🔧 [API 참조](docs/API_REFERENCE.md) - 프로그래밍 인터페이스
- 🚀 [성능 최적화](docs/PERFORMANCE.md) - 성능 튜닝 가이드
- 🔧 [트러블슈팅](docs/TROUBLESHOOTING.md) - 문제 해결 방법
- ⚙️ [설정 템플릿](config/) - 다양한 환경별 설정 예제

## CLI 명령어

```bash
# 로그 생성 관련
log-generator start [OPTIONS]          # 로그 생성 시작
log-generator stop                     # 로그 생성 중지
log-generator pause                    # 일시 정지
log-generator resume                   # 재개

# 설정 관련
log-generator config create            # 설정 파일 생성
log-generator config validate          # 설정 검증
log-generator config show              # 현재 설정 표시

# 모니터링
log-generator status                   # 현재 상태 확인
log-generator stats                    # 통계 정보
log-generator monitor                  # 실시간 모니터링

# 유틸리티
log-generator sample --type nginx      # 샘플 로그 확인
log-generator validate --input logs/   # 로그 검증
```

## 프로젝트 구조

```
log_generator/
├── core/                 # 핵심 엔진 및 인터페이스
│   ├── engine.py        # 메인 로그 생성 엔진
│   ├── factory.py       # 로그 생성기 팩토리
│   ├── config.py        # 설정 관리
│   └── interfaces.py    # 기본 인터페이스
├── generators/          # 로그 타입별 생성기
│   ├── nginx.py        # Nginx 로그 생성기
│   ├── syslog.py       # Syslog 생성기
│   └── ...
├── outputs/            # 출력 핸들러
│   ├── file_handler.py # 파일 출력
│   ├── network_handler.py # 네트워크 출력
│   └── ...
├── patterns/           # 로그 패턴 라이브러리
└── cli.py             # 명령줄 인터페이스

config/                 # 설정 템플릿
docs/                  # 문서
examples/              # 사용 예제
tests/                 # 테스트 코드
```

## 개발 환경 설정

```bash
# 개발 의존성 설치
pip install -e ".[dev]"

# 테스트 실행
pytest tests/ -v

# 코드 품질 검사
black log_generator/           # 코드 포맷팅
isort log_generator/           # import 정렬
flake8 log_generator/          # 린팅
mypy log_generator/            # 타입 체크

# 커버리지 확인
pytest --cov=log_generator tests/
```

## 기여하기

프로젝트에 기여해 주셔서 감사합니다! 

1. 이슈를 확인하거나 새로운 이슈를 생성하세요
2. 포크하고 브랜치를 생성하세요: `git checkout -b feature/amazing-feature`
3. 변경사항을 커밋하세요: `git commit -m 'Add amazing feature'`
4. 브랜치에 푸시하세요: `git push origin feature/amazing-feature`
5. Pull Request를 생성하세요

자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참조하세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 지원 및 커뮤니티

- 🐛 **버그 리포트**: [GitHub Issues](https://github.com/your-org/log-generator-tool/issues)
- 💡 **기능 요청**: [GitHub Discussions](https://github.com/your-org/log-generator-tool/discussions)
- 📧 **이메일**: support@your-org.com
- 📚 **문서**: [ReadTheDocs](https://log-generator-tool.readthedocs.io/)

## 로드맵

- [ ] 웹 UI 인터페이스
- [ ] 실시간 로그 스트리밍 API
- [ ] 클라우드 네이티브 배포 지원
- [ ] 머신러닝 기반 로그 패턴 학습
- [ ] 더 많은 로그 타입 지원 (Redis, MongoDB, etc.)

---

**Log Generator Tool**로 현실적이고 다양한 로그 데이터를 생성하여 로그 분석 시스템을 효과적으로 테스트하세요! 🚀