# Log Generator Tool 성능 최적화 가이드

## 목차

1. [성능 개요](#성능-개요)
2. [하드웨어 요구사항](#하드웨어-요구사항)
3. [설정 최적화](#설정-최적화)
4. [메모리 최적화](#메모리-최적화)
5. [I/O 최적화](#io-최적화)
6. [네트워크 최적화](#네트워크-최적화)
7. [대용량 로그 생성](#대용량-로그-생성)
8. [성능 모니터링](#성능-모니터링)
9. [벤치마크 결과](#벤치마크-결과)

## 성능 개요

Log Generator Tool의 성능은 다음 요소들에 의해 결정됩니다:

- **CPU**: 로그 생성 및 패턴 처리
- **메모리**: 버퍼링 및 캐싱
- **디스크 I/O**: 파일 출력 성능
- **네트워크**: 원격 로그 전송
- **설정**: 스레드 수, 배치 크기 등

### 기본 성능 지표

| 환경 | 로그/초 | 메모리 사용량 | CPU 사용률 | 설정 |
|------|---------|---------------|------------|------|
| 기본 설정 | 100 | 30MB | 5% | generation_interval: 1.0 |
| 최적화 설정 | 1,000 | 80MB | 15% | generation_interval: 0.1 |
| 고성능 설정 | 3,000+ | 150MB | 25% | generation_interval: 0.01 |
| 극한 성능 | 5,000+ | 300MB | 50% | generation_interval: 0.001 |

## 하드웨어 요구사항

### 최소 요구사항

- **CPU**: 2 코어
- **메모리**: 2GB RAM
- **디스크**: 10GB 여유 공간
- **네트워크**: 100Mbps

### 권장 사양

- **CPU**: 8 코어 이상
- **메모리**: 8GB RAM 이상
- **디스크**: SSD, 100GB 이상
- **네트워크**: 1Gbps 이상

### 고성능 환경

- **CPU**: 16 코어 이상
- **메모리**: 32GB RAM 이상
- **디스크**: NVMe SSD, 500GB 이상
- **네트워크**: 10Gbps 이상

## 설정 최적화

### 1. 생성 간격 최적화 (핵심)

```yaml
log_generator:
  global:
    generation_interval: 0.01  # 10ms - 고성능 설정
    # generation_interval: 0.1   # 100ms - 기본 설정
    # generation_interval: 1.0   # 1초 - 저성능 설정
```

**성능 영향:**
- `0.001` (1ms): 극한 성능 (5,000+ logs/sec)
- `0.01` (10ms): 고성능 (3,000+ logs/sec) ⭐ **권장**
- `0.1` (100ms): 표준 성능 (1,000 logs/sec)
- `1.0` (1초): 저성능 (100 logs/sec)

### 2. 멀티 파일 출력 최적화

```yaml
log_generator:
  global:
    output_format: "multi_file"  # 로그 타입별 분리로 I/O 분산
    
    multi_file:
      file_pattern: "{log_type}_{date}.log"
      date_format: "%Y%m%d"
    
    # 파일 버퍼 크기 증가
    buffer_size: 65536  # 64KB (기본값: 8192)
```

### 3. 로그 타입 frequency 최적화

```yaml
log_types:
  nginx_access:
    enabled: true
    frequency: 0.4  # 40% - 가장 빠른 생성
    
  fastapi:
    enabled: true
    frequency: 0.35  # 35% - 중간 속도
    
  syslog:
    enabled: true
    frequency: 0.25  # 25% - 상대적으로 느림
```

**frequency 최적화 팁:**
- 간단한 로그 타입(nginx_access)에 높은 frequency 할당
- 복잡한 로그 타입(database)에 낮은 frequency 할당
- 총 frequency 합계는 1.0 이하로 유지
  
  # I/O 버퍼 크기
  io_buffer_size: 65536  # 64KB
  
  # 동시 I/O 작업 수
  max_concurrent_io: 10
```

## 메모리 최적화

### 1. 메모리 제한 설정

```yaml
performance:
  # 전체 메모리 제한
  memory_limit: "2GB"
  
  # 가비지 컬렉션 임계값
  gc_threshold: 1000
  
  # 지연 로딩 활성화
  lazy_loading: true
```

### 2. 객체 풀링

```python
# 객체 재사용으로 메모리 할당 최소화
from log_generator.core.performance import ObjectPool

class OptimizedGenerator:
    def __init__(self):
        self.log_entry_pool = ObjectPool(LogEntry, initial_size=1000)
        
    def generate_log(self):
        # 풀에서 객체 가져오기
        log_entry = self.log_entry_pool.get()
        
        # 로그 생성 로직
        # ...
        
        # 풀에 객체 반환
        self.log_entry_pool.return_object(log_entry)
```

### 3. 메모리 모니터링

```python
import psutil
import gc

def monitor_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
    print(f"Garbage objects: {len(gc.garbage)}")
    
    # 메모리 사용량이 임계값 초과 시 가비지 컬렉션
    if memory_info.rss > 1024 * 1024 * 1024:  # 1GB
        gc.collect()
```

## I/O 최적화

### 1. 파일 I/O 최적화

```yaml
output:
  type: "file"
  file_path: "./logs/output.log"
  
  # I/O 최적화 설정
  buffer_size: 1048576  # 1MB 버퍼
  sync_mode: false  # 비동기 쓰기
  direct_io: true   # 직접 I/O (Linux)
  
  # 로그 로테이션 최적화
  rotation:
    max_size: "500MB"  # 적절한 크기로 설정
    compress: false    # 압축 비활성화 (성능 우선)
    async_rotation: true  # 비동기 로테이션
```

### 2. SSD 최적화

```bash
# SSD 최적화 설정 (Linux)
# I/O 스케줄러 변경
echo noop > /sys/block/sda/queue/scheduler

# 파일시스템 마운트 옵션
mount -o noatime,nodiratime /dev/sda1 /logs
```

### 3. 메모리 맵 파일 사용

```python
import mmap

class MemoryMappedOutput:
    def __init__(self, file_path, size=1024*1024*100):  # 100MB
        self.file = open(file_path, 'r+b')
        self.mmap = mmap.mmap(self.file.fileno(), size)
        self.position = 0
        
    def write_log(self, log_entry):
        data = log_entry.encode('utf-8') + b'\n'
        self.mmap[self.position:self.position + len(data)] = data
        self.position += len(data)
```

## 네트워크 최적화

### 1. TCP 최적화

```yaml
output:
  type: "network"
  protocol: "tcp"
  host: "logserver"
  port: 5140
  
  # TCP 최적화
  tcp_nodelay: true      # Nagle 알고리즘 비활성화
  tcp_keepalive: true    # Keep-alive 활성화
  send_buffer_size: 65536  # 송신 버퍼 크기
  recv_buffer_size: 65536  # 수신 버퍼 크기
  
  # 연결 풀링
  connection_pool_size: 10
  max_connections: 50
```

### 2. UDP 최적화 (고성능)

```yaml
output:
  type: "network"
  protocol: "udp"
  host: "logserver"
  port: 5140
  
  # UDP 최적화
  batch_udp_packets: true  # 패킷 배치 전송
  udp_buffer_size: 65536   # UDP 버퍼 크기
  
  # 패킷 손실 대응
  enable_ack: false        # ACK 비활성화 (성능 우선)
  retry_on_error: false    # 재시도 비활성화
```

### 3. 압축 사용

```yaml
output:
  type: "network"
  compression: "gzip"      # gzip, lz4, snappy
  compression_level: 1     # 1-9 (낮을수록 빠름)
  
  # 압축 임계값
  compress_threshold: 1024  # 1KB 이상만 압축
```

## 대용량 로그 생성

### 1. 스트리밍 모드

```bash
# 무제한 스트리밍 생성
log-generator start --streaming --no-limit

# 메모리 효율적인 대용량 생성
log-generator start --count 10000000 --streaming --batch-size 5000
```

### 2. 분산 생성

```yaml
# 여러 인스턴스로 분산 생성
distributed:
  enabled: true
  instances: 4
  
  # 각 인스턴스별 설정
  instance_config:
    - id: 1
      log_types: ["nginx_access", "syslog"]
      output_path: "./logs/instance1"
    - id: 2
      log_types: ["fastapi", "docker"]
      output_path: "./logs/instance2"
```

### 3. 파티셔닝

```python
# 시간 기반 파티셔닝
class TimePartitionedOutput:
    def __init__(self, base_path):
        self.base_path = base_path
        
    def get_file_path(self):
        now = datetime.now()
        return f"{self.base_path}/{now.strftime('%Y%m%d_%H')}.log"
        
    def write_log(self, log_entry):
        file_path = self.get_file_path()
        with open(file_path, 'a') as f:
            f.write(log_entry + '\n')
```

## 성능 모니터링

### 1. 실시간 통계

```bash
# 실시간 성능 모니터링
log-generator monitor --interval 1

# 상세 성능 통계
log-generator stats --detailed --performance
```

### 2. 프로파일링

```bash
# CPU 프로파일링
python -m cProfile -o profile.stats -m log_generator.cli start --count 10000

# 메모리 프로파일링
python -m memory_profiler log_generator/cli.py
```

### 3. 시스템 리소스 모니터링

```python
import psutil
import time

def monitor_system():
    while True:
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        
        # 디스크 I/O
        disk_io = psutil.disk_io_counters()
        
        # 네트워크 I/O
        net_io = psutil.net_io_counters()
        
        print(f"CPU: {cpu_percent}%, Memory: {memory.percent}%")
        print(f"Disk Read: {disk_io.read_bytes}, Write: {disk_io.write_bytes}")
        print(f"Net Sent: {net_io.bytes_sent}, Recv: {net_io.bytes_recv}")
        
        time.sleep(5)
```

## 벤치마크 결과

### 테스트 환경

- **CPU**: Apple M2 Pro (10 cores)
- **메모리**: 16GB Unified Memory
- **디스크**: 1TB SSD
- **OS**: macOS Sonoma

### 성능 테스트 결과 (2024년 12월 업데이트)

#### 1. 로그 생성 속도 (최신 최적화 적용)

| 설정 | generation_interval | 로그/초 | CPU 사용률 | 메모리 사용량 | 평가 |
|------|---------------------|---------|------------|---------------|------|
| 저성능 | 1.0s | 100 | 5% | 30MB | ❌ 느림 |
| 기본 | 0.1s | 1,000 | 15% | 80MB | ✅ 양호 |
| 고성능 | 0.01s | **3,000** | 25% | 150MB | 🚀 우수 |
| 극한 | 0.001s | **5,000+** | 50% | 300MB | ⚡ 최고 |

#### 2. 실제 벤치마크 결과

**가상 시간 최적화 적용 후 (100,000개 로그 생성 테스트):**
- **평균 속도**: **4,095 logs/sec** 🚀
- **총 소요시간**: 24.46초
- **에러율**: 0%
- **로그 타입 분포**: nginx_access(70.0%), fastapi(30.0%)

**성능 개선 요약:**
- 이전 버전 (sleep 기반): ~500 logs/sec
- 중간 버전 (최적화): ~3,000 logs/sec
- **현재 버전 (가상 시간)**: **4,000+ logs/sec** (8배 향상 ⚡)

**핵심 개선사항:**
- ✅ **가상 시간 사용**: 실제 sleep 없이 타임스탬프만 시뮬레이션
- ✅ **배치 처리**: 사이클당 여러 로그 생성
- ✅ **최소 CPU 대기**: 1ms sleep으로 CPU 과부하 방지

#### 2. 출력 방식별 성능

| 출력 방식 | 로그/초 | 지연시간 | 리소스 사용량 |
|-----------|---------|----------|---------------|
| 콘솔 | 5,000 | 낮음 | CPU 높음 |
| 파일 (HDD) | 8,000 | 중간 | I/O 높음 |
| 파일 (SSD) | 25,000 | 낮음 | I/O 중간 |
| 네트워크 (TCP) | 12,000 | 중간 | 네트워크 중간 |
| 네트워크 (UDP) | 35,000 | 낮음 | 네트워크 낮음 |

#### 3. 로그 타입별 성능

| 로그 타입 | 복잡도 | 로그/초 | 메모리/로그 |
|-----------|--------|---------|-------------|
| Nginx Access | 낮음 | 30,000 | 150B |
| Syslog | 낮음 | 28,000 | 120B |
| FastAPI | 중간 | 20,000 | 200B |
| JSON 구조화 | 높음 | 15,000 | 300B |
| 커스텀 패턴 | 높음 | 12,000 | 250B |

### 최적화 권장사항

#### 높은 처리량이 필요한 경우

```yaml
performance:
  threads: 8
  batch_size: 2000
  buffer_size: 20000
  async_io: true
  memory_limit: "2GB"

output:
  type: "file"  # 또는 UDP
  buffer_size: 1048576
  sync_mode: false
```

#### 낮은 지연시간이 필요한 경우

```yaml
performance:
  threads: 4
  batch_size: 100
  buffer_size: 1000
  flush_interval: 0.1

output:
  type: "network"
  protocol: "udp"
  tcp_nodelay: true
```

#### 메모리 제약이 있는 경우

```yaml
performance:
  threads: 2
  batch_size: 500
  buffer_size: 2000
  memory_limit: "512MB"
  lazy_loading: true
  gc_threshold: 500
```

## 성능 문제 해결

### 일반적인 성능 병목

1. **CPU 병목**
   - 스레드 수 증가
   - 로그 패턴 단순화
   - 불필요한 검증 비활성화

2. **메모리 병목**
   - 배치 크기 감소
   - 가비지 컬렉션 튜닝
   - 객체 풀링 사용

3. **I/O 병목**
   - SSD 사용
   - 비동기 I/O 활성화
   - 버퍼 크기 증가

4. **네트워크 병목**
   - UDP 사용 고려
   - 압축 활성화
   - 연결 풀링 사용

이 가이드를 통해 Log Generator Tool의 성능을 최대한 활용하여 요구사항에 맞는 최적의 설정을 찾을 수 있습니다.