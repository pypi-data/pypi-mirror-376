# Log Generator Tool 트러블슈팅 가이드

## 목차

1. [일반적인 문제](#일반적인-문제)
2. [설치 관련 문제](#설치-관련-문제)
3. [설정 관련 문제](#설정-관련-문제)
4. [로그 생성 문제](#로그-생성-문제)
5. [출력 관련 문제](#출력-관련-문제)
6. [성능 문제](#성능-문제)
7. [네트워크 관련 문제](#네트워크-관련-문제)
8. [디버깅 방법](#디버깅-방법)
9. [FAQ](#faq)

## 일반적인 문제

### 문제: 로그 생성기가 시작되지 않음

**증상:**
```bash
$ log-generator start
Error: Failed to start log generation
```

**원인과 해결방법:**

1. **설정 파일 문제**
   ```bash
   # 설정 파일 검증
   log-generator config validate --config config.yaml
   
   # 기본 설정 파일 생성
   log-generator config create --output config.yaml
   ```

2. **권한 문제**
   ```bash
   # 출력 디렉토리 권한 확인
   ls -la ./logs/
   
   # 권한 부여
   chmod 755 ./logs/
   ```

3. **의존성 문제**
   ```bash
   # 의존성 재설치
   pip install --upgrade log-generator-tool
   ```

### 문제: 로그가 예상과 다르게 생성됨

**증상:**
- 로그 형식이 올바르지 않음
- 필드가 누락됨
- 타임스탬프가 잘못됨

**해결방법:**

1. **로그 패턴 확인**
   ```python
   from log_generator.generators.nginx import NginxAccessLogGenerator
   
   gen = NginxAccessLogGenerator(config)
   pattern = gen.get_log_pattern()
   print(f"Pattern: {pattern}")
   
   # 샘플 로그 확인
   samples = gen.get_sample_logs(5)
   for sample in samples:
       print(sample)
   ```

2. **설정 검증**
   ```bash
   # 현재 설정 확인
   log-generator config show
   
   # 특정 로그 타입 설정 확인
   log-generator config show --type nginx_access
   ```

## 설치 관련 문제

### 문제: pip 설치 실패

**증상:**
```bash
$ pip install log-generator-tool
ERROR: Could not find a version that satisfies the requirement log-generator-tool
```

**해결방법:**

1. **Python 버전 확인**
   ```bash
   python --version  # Python 3.8+ 필요
   ```

2. **pip 업그레이드**
   ```bash
   pip install --upgrade pip
   ```

3. **소스에서 설치**
   ```bash
   git clone https://github.com/your-org/log-generator-tool.git
   cd log-generator-tool
   pip install -e .
   ```

### 문제: 의존성 충돌

**증상:**
```bash
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**해결방법:**

1. **가상 환경 사용**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 또는
   venv\Scripts\activate  # Windows
   
   pip install log-generator-tool
   ```

2. **의존성 강제 업그레이드**
   ```bash
   pip install --upgrade --force-reinstall log-generator-tool
   ```

## 설정 관련 문제

### 문제: 설정 파일 파싱 오류

**증상:**
```bash
ConfigurationError: Invalid YAML format in config file
```

**해결방법:**

1. **YAML 문법 검증**
   ```bash
   # Python으로 YAML 검증
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. **온라인 YAML 검증기 사용**
   - http://www.yamllint.com/

3. **기본 설정으로 시작**
   ```bash
   log-generator config create --output config.yaml --template basic
   ```

### 문제: 설정 값이 적용되지 않음

**증상:**
- 설정을 변경했지만 로그 생성에 반영되지 않음

**해결방법:**

1. **설정 파일 경로 확인**
   ```bash
   # 현재 사용 중인 설정 파일 확인
   log-generator config show --source
   ```

2. **설정 우선순위 확인**
   ```
   우선순위 (높음 → 낮음):
   1. CLI 옵션
   2. 환경 변수
   3. 설정 파일
   4. 기본값
   ```

3. **캐시 클리어**
   ```bash
   # 설정 캐시 클리어
   log-generator config clear-cache
   ```

## 로그 생성 문제

### 문제: 로그 생성 속도가 느림

**증상:**
- 예상보다 로그 생성이 느림
- CPU 사용률이 높음

**해결방법:**

1. **멀티스레딩 활성화**
   ```yaml
   # config.yaml
   performance:
     threads: 4
     batch_size: 1000
   ```

2. **배치 크기 조정**
   ```bash
   log-generator start --batch-size 1000 --threads 4
   ```

3. **성능 프로파일링**
   ```bash
   # 성능 통계 확인
   log-generator stats --performance
   ```

### 문제: 메모리 사용량이 과도함

**증상:**
```bash
MemoryError: Unable to allocate memory
```

**해결방법:**

1. **메모리 제한 설정**
   ```yaml
   performance:
     memory_limit: "512MB"
     buffer_size: 1000
     lazy_loading: true
   ```

2. **가비지 컬렉션 조정**
   ```python
   import gc
   gc.set_threshold(700, 10, 10)
   ```

3. **스트리밍 모드 사용**
   ```bash
   log-generator start --streaming --no-buffer
   ```

### 문제: 특정 로그 타입이 생성되지 않음

**증상:**
- 설정에서 활성화했지만 특정 로그 타입이 생성되지 않음

**해결방법:**

1. **로그 타입 활성화 확인**
   ```yaml
   log_types:
     nginx_access:
       enabled: true  # 반드시 true로 설정
       frequency: 0.3
   ```

2. **빈도 설정 확인**
   ```yaml
   # 모든 로그 타입의 frequency 합이 1.0을 초과하지 않도록
   nginx_access:
     frequency: 0.4
   syslog:
     frequency: 0.3
   fastapi:
     frequency: 0.3
   # 총합: 1.0
   ```

3. **생성기 등록 확인**
   ```python
   from log_generator.core.factory import LogFactory
   
   available_types = LogFactory.get_available_types()
   print("Available log types:", available_types)
   ```

## 출력 관련 문제

### 문제: 파일 출력 실패

**증상:**
```bash
OutputError: Permission denied: ./logs/output.log
```

**해결방법:**

1. **디렉토리 권한 확인**
   ```bash
   # 디렉토리 생성 및 권한 설정
   mkdir -p ./logs
   chmod 755 ./logs
   ```

2. **디스크 공간 확인**
   ```bash
   df -h  # 디스크 사용량 확인
   ```

3. **파일 잠금 확인**
   ```bash
   # 파일이 다른 프로세스에서 사용 중인지 확인
   lsof ./logs/output.log
   ```

### 문제: 로그 로테이션이 작동하지 않음

**증상:**
- 로그 파일이 계속 커짐
- 로테이션 설정이 무시됨

**해결방법:**

1. **로테이션 설정 확인**
   ```yaml
   output:
     type: "file"
     file_path: "./logs/output.log"
     rotation:
       max_size: "100MB"
       max_files: 10
       compress: true
   ```

2. **수동 로테이션 테스트**
   ```python
   from log_generator.outputs.file_handler import FileOutputHandler
   
   handler = FileOutputHandler("./logs/test.log", rotation_config)
   handler.rotate_log()  # 수동 로테이션
   ```

### 문제: 네트워크 출력 연결 실패

**증상:**
```bash
NetworkError: Connection refused to localhost:5140
```

**해결방법:**

1. **포트 사용 확인**
   ```bash
   netstat -an | grep 5140
   telnet localhost 5140
   ```

2. **방화벽 설정 확인**
   ```bash
   # Linux
   sudo ufw status
   sudo ufw allow 5140
   
   # 또는 iptables
   sudo iptables -L
   ```

3. **재연결 정책 설정**
   ```yaml
   output:
     type: "network"
     host: "localhost"
     port: 5140
     retry_attempts: 5
     retry_delay: 2.0
   ```

## 성능 문제

### 문제: 높은 CPU 사용률

**해결방법:**

1. **생성 간격 조정**
   ```yaml
   global:
     generation_interval: 0.1  # 간격을 늘려서 CPU 부하 감소
   ```

2. **프로파일링 실행**
   ```bash
   # cProfile로 성능 분석
   python -m cProfile -o profile.stats -m log_generator.cli start
   
   # 결과 분석
   python -c "import pstats; p=pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(10)"
   ```

### 문제: 메모리 누수

**증상:**
- 시간이 지날수록 메모리 사용량이 계속 증가

**해결방법:**

1. **메모리 모니터링**
   ```python
   import psutil
   import os
   
   process = psutil.Process(os.getpid())
   print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
   ```

2. **가비지 컬렉션 강제 실행**
   ```python
   import gc
   gc.collect()
   ```

3. **객체 참조 확인**
   ```python
   import gc
   
   # 순환 참조 확인
   print(f"Garbage objects: {len(gc.garbage)}")
   ```

## 네트워크 관련 문제

### 문제: Syslog 서버 연결 실패

**해결방법:**

1. **Syslog 서버 상태 확인**
   ```bash
   # rsyslog 서비스 상태 확인
   sudo systemctl status rsyslog
   
   # 포트 리스닝 확인
   sudo netstat -ulnp | grep 514
   ```

2. **설정 파일 확인**
   ```bash
   # rsyslog 설정 확인
   sudo cat /etc/rsyslog.conf | grep -v "^#"
   ```

3. **테스트 메시지 전송**
   ```bash
   # logger 명령으로 테스트
   logger -n localhost -P 514 "Test message"
   ```

## 디버깅 방법

### 로깅 레벨 조정

```python
import logging

# 디버그 로깅 활성화
logging.basicConfig(level=logging.DEBUG)

# 또는 설정 파일에서
```

```yaml
logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/debug.log"
```

### 상세 오류 정보 확인

```bash
# 상세 오류 정보와 함께 실행
log-generator start --verbose --debug

# 스택 트레이스 포함
log-generator start --traceback
```

### 설정 덤프

```bash
# 현재 설정을 파일로 저장
log-generator config dump --output current_config.yaml

# 설정 차이점 확인
diff config.yaml current_config.yaml
```

## FAQ

### Q: 로그 생성을 중간에 중단하고 재시작할 수 있나요?

A: 네, 가능합니다.

```bash
# 일시정지
log-generator pause

# 재개
log-generator resume

# 완전 중지
log-generator stop
```

### Q: 커스텀 로그 패턴을 어떻게 추가하나요?

A: 설정 파일에서 커스텀 패턴을 정의할 수 있습니다.

```yaml
custom_patterns:
  my_app:
    template: "{timestamp} [{level}] {component}: {message}"
    fields:
      timestamp: "datetime"
      level: ["INFO", "WARN", "ERROR"]
      component: ["auth", "db", "cache"]
      message: "sentence"
```

### Q: 생성된 로그의 품질을 어떻게 확인하나요?

A: 내장된 검증 도구를 사용하세요.

```bash
# 로그 검증
log-generator validate --input ./logs/output.log --type nginx

# 샘플 로그 확인
log-generator sample --type nginx --count 10
```

### Q: 대용량 로그 생성 시 주의사항은?

A: 다음 사항들을 고려하세요:

1. **디스크 공간**: 충분한 여유 공간 확보
2. **메모리 제한**: 적절한 버퍼 크기 설정
3. **I/O 성능**: SSD 사용 권장
4. **로그 로테이션**: 자동 로테이션 설정

```yaml
performance:
  memory_limit: "1GB"
  buffer_size: 10000
  threads: 8
  
output:
  rotation:
    max_size: "500MB"
    max_files: 20
```

### Q: 실시간 로그 스트림을 어떻게 생성하나요?

A: 스트리밍 모드를 사용하세요.

```bash
# 무한 스트리밍
log-generator start --streaming --interval 0.1

# 네트워크로 실시간 전송
log-generator start --output network --host logserver --port 514 --streaming
```

### Q: 여러 로그 타입을 동시에 생성할 때 비율을 어떻게 조정하나요?

A: frequency 값으로 비율을 조정합니다.

```yaml
log_types:
  nginx_access:
    frequency: 0.5  # 50%
  syslog:
    frequency: 0.3  # 30%
  fastapi:
    frequency: 0.2  # 20%
```

### Q: 에러 로그의 빈도를 어떻게 조정하나요?

A: 각 로그 타입별로 에러 비율을 설정할 수 있습니다.

```yaml
nginx_access:
  custom_fields:
    status_codes:
      200: 0.7   # 70% 성공
      404: 0.15  # 15% Not Found
      500: 0.1   # 10% 서버 오류
      403: 0.05  # 5% 권한 오류
```

## 지원 및 문의

문제가 해결되지 않는 경우:

1. **GitHub Issues**: https://github.com/your-org/log-generator-tool/issues
2. **문서**: https://log-generator-tool.readthedocs.io/
3. **이메일**: support@your-org.com

문제 보고 시 다음 정보를 포함해 주세요:

- 운영체제 및 Python 버전
- Log Generator Tool 버전
- 설정 파일 내용
- 오류 메시지 및 스택 트레이스
- 재현 단계