"""
Syslog generators for RFC 3164 and RFC 5424 formats.

This module implements syslog generators that produce realistic system logs
following RFC 3164 (BSD Syslog Protocol) and RFC 5424 (The Syslog Protocol) standards.
"""

import random
import re
import socket
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from faker import Faker

from ..core.interfaces import LogGenerator
from ..core.models import LogEntry


class SyslogGenerator(LogGenerator):
    """
    Generates syslog messages in RFC 3164 and RFC 5424 formats.

    Options:
      - rfc_format: "3164" | "5424"
      - priority_style:
          "pri"     -> <134> (숫자 PRI, 기본)
          "bracket" -> [local0.info]
          "plain"   -> local0.info
          "none"    -> 프리픽스 없음
    """

    # Syslog facilities (RFC 3164/5424)
    FACILITIES = {
        "kern": 0,
        "user": 1,
        "mail": 2,
        "daemon": 3,
        "auth": 4,
        "syslog": 5,
        "lpr": 6,
        "news": 7,
        "uucp": 8,
        "cron": 9,
        "authpriv": 10,
        "ftp": 11,
        "local0": 16,
        "local1": 17,
        "local2": 18,
        "local3": 19,
        "local4": 20,
        "local5": 21,
        "local6": 22,
        "local7": 23,
    }

    SEVERITIES = {
        "emerg": 0,
        "alert": 1,
        "crit": 2,
        "err": 3,
        "warning": 4,
        "notice": 5,
        "info": 6,
        "debug": 7,
    }

    FACILITY_BY_CODE = {v: k for k, v in FACILITIES.items()}
    SEVERITY_BY_CODE = {v: k for k, v in SEVERITIES.items()}

    # Facility/Severity distributions
    FACILITY_DISTRIBUTION = {
        "kern": 0.15,
        "daemon": 0.20,
        "auth": 0.15,
        "mail": 0.05,
        "cron": 0.10,
        "syslog": 0.05,
        "user": 0.10,
        "local0": 0.05,
        "local1": 0.05,
        "local2": 0.05,
        "local3": 0.05,
    }
    SEVERITY_DISTRIBUTION = {
        "info": 0.40,
        "notice": 0.25,
        "warning": 0.15,
        "err": 0.10,
        "debug": 0.05,
        "crit": 0.03,
        "alert": 0.01,
        "emerg": 0.01,
    }

    MESSAGE_PATTERNS = {
        "kern": [
            "Out of memory: Kill process {pid} ({process}) score {score} or sacrifice child",
            "TCP: Peer {ip}:{port} unexpectedly shrunk window",
            "device eth0 entered promiscuous mode",
            "device eth0 left promiscuous mode",
            "segfault at {address} ip {ip} sp {sp} error {error} in {process}[{address}+{size}]",
            "CPU{cpu}: Core temperature above threshold, cpu clock throttled",
            "ACPI: Battery Slot (BAT0) {status}",
            "USB disconnect, address {address}",
            "kernel: [ {uptime:.6f} ] {iface}: link is {link_state}",
            "iptables: IN={iface} OUT= MAC={mac} SRC={ip} DST={ip2} LEN={len} TOS=0x00 PREC=0x00 TTL={ttl} ID={ip_id} PROTO={proto} SPT={sport} DPT={dport} WINDOW={window} RES=0x00 {tcp_flags}",
            "EXT4-fs ({disk}): mounted filesystem with ordered data mode. Opts: {mount_opts}",
            "block {disk}: I/O error, dev {disk}, sector {sector}",
            'audit: type=ANOM_ABEND msg=audit({epoch}.{msec}): auid={uid} uid={uid} gid={gid} ses={ses} pid={pid} comm="{process}"',
            "perf: interrupt took too long ({latency} > {latency_thresh}), lowering kernel.perf_event_max_sample_rate to {sample_rate}",
        ],
        "daemon": [
            "Starting {service} daemon",
            "Stopping {service} daemon",
            "{service}: configuration reloaded",
            "{service}: worker process {pid} exited with code {code}",
            "{service}: bind() to {ip}:{port} failed ({errno}: {error})",
            "{service}: accept() failed ({errno}: {error})",
            "{service}: connection from {ip} refused (access denied)",
            "systemd[1]: Started {service}.service",
            "systemd[1]: Failed to start {service}.service",
            "systemd[1]: {service}.service: Main process exited, code=exited, status={code}",
            "NetworkManager[{pid}]: <info>  [{time}] device ({iface}): state change: {nm_old_state} -> {nm_new_state}",
            "dnsmasq[{pid}]: reply {fqdn} is {ip}",
            "docker[{pid}]: Container {container_id} ({image}) started",
            "containerd[{pid}]: Task {container_id} exit code {code}",
        ],
        "auth": [
            "Accepted password for {user} from {ip} port {port} ssh2",
            "Failed password for {user} from {ip} port {port} ssh2",
            "Invalid user {user} from {ip} port {port}",
            "Connection closed by {ip} port {port} [preauth]",
            "pam_unix(sshd:session): session opened for user {user} by (uid=0)",
            "pam_unix(sshd:session): session closed for user {user}",
            "sudo: {user} : TTY=pts/{tty} ; PWD={pwd} ; USER=root ; COMMAND={command}",
            "su: (to root) {user} on pts/{tty}",
            "sshd[{pid}]: Did not receive identification string from {ip}",
            "sshd[{pid}]: Received disconnect from {ip} port {port}: 11: disconnected by user",
            "sudo: pam_unix(sudo:auth): authentication failure; logname={user} uid={uid} euid=0 tty=pts/{tty} ruser={user} rhost={hostname}",
        ],
        "mail": [
            "postfix/smtpd[{pid}]: connect from {hostname}[{ip}]",
            "postfix/smtpd[{pid}]: disconnect from {hostname}[{ip}]",
            "postfix/cleanup[{pid}]: {queue_id}: message-id=<{message_id}>",
            "postfix/qmgr[{pid}]: {queue_id}: from=<{from}>, size={size}, nrcpt={nrcpt}",
            "postfix/smtp[{pid}]: {queue_id}: to=<{to}>, relay={relay}, status=sent",
            "dovecot: imap-login: Login: user=<{user}>, method=PLAIN, rip={ip}",
            "dovecot: imap({user}): Disconnected: Logged out",
            "postfix/smtp[{pid}]: {queue_id}: to=<{to}>, relay={relay}, delay={delay}, delays={delays}, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as {queue_id2})",
            "postfix/smtpd[{pid}]: NOQUEUE: reject: RCPT from {hostname}[{ip}]: 554 5.7.1 Relay access denied; from=<{from}> to=<{to}> proto=ESMTP helo=<{hostname}>",
            "dovecot: imap({user}): Connection closed (bytes={bytes_in}/{bytes_out})",
        ],
        "cron": [
            "({user}) CMD ({command})",
            "pam_unix(cron:session): session opened for user {user} by (uid=0)",
            "pam_unix(cron:session): session closed for user {user}",
            "({user}) RELOAD ({file})",
            "({user}) LIST ({user})",
            "({user}) DELETE ({user})",
            "Maximum number of errors from {user} reached. Disabling until next restart.",
            "CRON[{pid}]: pam_unix(cron:session): session opened for user {user} by (uid=0)",
            "CRON[{pid}]: pam_unix(cron:session): session closed for user {user}",
            "(root) CMD ({command})",
        ],
        "syslog": [
            "rsyslogd was HUPed",
            'rsyslogd: [origin software="rsyslogd" swVersion="{version}"] start',
            'rsyslogd: [origin software="rsyslogd" swVersion="{version}"] exiting on signal 15',
            "rsyslogd-2007: action 'action 17' suspended, next retry is {time}",
            "rsyslogd: imuxsock begins to drop messages from pid {pid} due to rate-limiting",
            "rsyslogd: imjournal: journal files changed, reloading...",
            "rsyslogd: omfile: buffer grown to {bufsize} bytes",
        ],
        "authpriv": [
            "sshd[{pid}]: Accepted publickey for {user} from {ip} port {port} ssh2: RSA {fingerprint}",
            "sshd[{pid}]: Authentication refused: bad ownership or modes for directory {path}",
            "sshd[{pid}]: User {user} from {ip} not allowed because not listed in AllowUsers",
        ],
        "user": [
            "useradd[{pid}]: new user: name={user}, UID={uid}, GID={gid}, home={home}, shell=/bin/bash",
            "passwd[{pid}]: password changed for {user}",
            "chsh[{pid}]: changed user '{user}' shell to /bin/zsh",
        ],
        "local0": [
            'local_app[{pid}]: request_id={req_id} path="{url_path}" status={http_status} latency={latency}ms',
            'local_app[{pid}]: cache {cache_op} key="{cache_key}" result={cache_result}',
        ],
        "local1": [
            "custom_daemon[{pid}]: worker {wid} heartbeat ok (load={load_avg})",
            "custom_daemon[{pid}]: worker {wid} restart due to {reason}",
        ],
        "local2": [
            "monitoring[{pid}]: probe {target} up={up} rtt={rtt}ms",
            'monitoring[{pid}]: alert {alert_id} severity={sev} rule="{rule}"',
        ],
        "local3": [
            "backup[{pid}]: snapshot {snapshot_id} completed size={bytes_out}B duration={duration}s",
            "backup[{pid}]: prune removed={removed} kept={kept}",
        ],
    }

    def __init__(
        self,
        rfc_format: str = "3164",
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize syslog generator.

        Args:
            rfc_format: "3164" or "5424"
            custom_config: optional config dict
        """
        self.rfc_format = rfc_format
        self.faker = Faker()
        self.custom_config = custom_config or {}
        self.hostname = self.custom_config.get("hostname", socket.gethostname())
        self.priority_style = self.custom_config.get(
            "priority_style", "pri"
        )  # "pri"|"bracket"|"plain"|"none"

        # override distributions
        if "facilities" in self.custom_config:
            self.FACILITY_DISTRIBUTION = self.custom_config["facilities"]
        if "severities" in self.custom_config:
            self.SEVERITY_DISTRIBUTION = self.custom_config["severities"]
        if "priority_style" in self.custom_config:
            self.priority_style = self.custom_config["priority_style"]

    # ---- Public API ----
    def generate_log(self) -> str:
        return self.generate_log_with_time(datetime.now())

    def generate_log_with_time(self, timestamp: datetime) -> str:
        facility = self._weighted_choice(self.FACILITY_DISTRIBUTION)
        severity = self._weighted_choice(self.SEVERITY_DISTRIBUTION)
        priority = self._calculate_priority(facility, severity)

        if self.rfc_format == "5424":
            return self._generate_rfc5424_log_with_time(
                priority, facility, severity, timestamp
            )
        else:
            return self._generate_rfc3164_log_with_time(
                priority, facility, severity, timestamp
            )

    def get_log_pattern(self) -> str:
        """
        Return regex pattern according to RFC + priority_style.
        """
        if self.rfc_format == "5424":
            if self.priority_style == "pri":
                return (
                    r"^<(\d+)>1 (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})) "
                    r"(\S+) (\S+) (\S+) (\S+) (\S+) (.*)$"
                )
            elif self.priority_style == "bracket":
                return (
                    r"^\[(\w+\.\w+)\]1 (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})) "
                    r"(\S+) (\S+) (\S+) (\S+) (\S+) (.*)$"
                )
            elif self.priority_style == "plain":
                return (
                    r"^(\w+\.\w+) 1 (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})) "
                    r"(\S+) (\S+) (\S+) (\S+) (\S+) (.*)$"
                )
            else:  # none
                return (
                    r"^1 (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})) "
                    r"(\S+) (\S+) (\S+) (\S+) (\S+) (.*)$"
                )
        else:  # 3164
            if self.priority_style == "pri":
                return (
                    r"^<(\d+)>(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})(?:\s+\w+\s+\d{4})?\s+"
                    r"(\S+)\s+(\S+?)(?:\[(\d+)\])?: (.*)$"
                )
            elif self.priority_style == "bracket":
                return (
                    r"^\[(\w+\.\w+)\](\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})(?:\s+\w+\s+\d{4})?\s+"
                    r"(\S+)\s+(\S+?)(?:\[(\d+)\])?: (.*)$"
                )
            elif self.priority_style == "plain":
                return (
                    r"^(\w+\.\w+)\s+(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})(?:\s+\w+\s+\d{4})?\s+"
                    r"(\S+)\s+(\S+?)(?:\[(\d+)\])?: (.*)$"
                )
            else:  # none
                return (
                    r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})(?:\s+\w+\s+\d{4})?\s+"
                    r"(\S+)\s+(\S+?)(?:\[(\d+)\])?: (.*)$"
                )

    def validate_log(self, log_entry: str) -> bool:
        return bool(re.match(self.get_log_pattern(), log_entry))

    def set_custom_fields(self, fields: Dict[str, Any]) -> None:
        self.custom_config.update(fields)
        if "facilities" in fields:
            self.FACILITY_DISTRIBUTION = fields["facilities"]
        if "severities" in fields:
            self.SEVERITY_DISTRIBUTION = fields["severities"]
        if "hostname" in fields:
            self.hostname = fields["hostname"]
        if "priority_style" in fields:
            self.priority_style = fields["priority_style"]

    # ---- 3164 ----
    def _generate_rfc3164_log_with_time(
        self, priority: int, facility: str, severity: str, timestamp: datetime
    ) -> str:
        ts = self._format_rfc3164_timestamp(timestamp)
        tag = self._generate_tag(facility)
        pid = str(random.randint(1000, 99999)) if random.random() < 0.7 else None
        msg = self._generate_message(facility, severity)
        prefix = self._format_priority_prefix(
            facility, severity, priority, is_5424=False
        )

        if pid:
            return f"{prefix}{ts} {self.hostname} {tag}[{pid}]: {msg}"
        return f"{prefix}{ts} {self.hostname} {tag}: {msg}"

    def _generate_rfc3164_log(self, priority: int, facility: str, severity: str) -> str:
        # (호출될 수 있으므로 동일 포맷 유지)
        ts = self._format_rfc3164_timestamp(datetime.now())
        tag = self._generate_tag(facility)
        pid = str(random.randint(1000, 99999)) if random.random() < 0.7 else None
        msg = self._generate_message(facility, severity)
        prefix = self._format_priority_prefix(
            facility, severity, priority, is_5424=False
        )

        if pid:
            return f"{prefix}{ts} {self.hostname} {tag}[{pid}]: {msg}"
        return f"{prefix}{ts} {self.hostname} {tag}: {msg}"

    # ---- 5424 ----
    def _generate_rfc5424_log_with_time(
        self, priority: int, facility: str, severity: str, timestamp: datetime
    ) -> str:
        ts = self._format_rfc5424_timestamp(timestamp)
        app = self._generate_app_name(facility)
        procid = str(random.randint(1000, 99999)) if random.random() < 0.7 else "-"
        msgid = self._generate_msgid(facility) if random.random() < 0.5 else "-"
        sd = "-"
        msg = self._generate_message(facility, severity)
        prefix = self._format_priority_prefix(
            facility, severity, priority, is_5424=True
        )
        return f"{prefix}1 {ts} {self.hostname} {app} {procid} {msgid} {sd} {msg}"

    def _generate_rfc5424_log(self, priority: int, facility: str, severity: str) -> str:
        ts = self._format_rfc5424_timestamp(datetime.now(timezone.utc))
        app = self._generate_app_name(facility)
        procid = str(random.randint(1000, 99999)) if random.random() < 0.7 else "-"
        msgid = self._generate_msgid(facility) if random.random() < 0.5 else "-"
        sd = "-"
        msg = self._generate_message(facility, severity)
        prefix = self._format_priority_prefix(
            facility, severity, priority, is_5424=True
        )
        return f"{prefix}1 {ts} {self.hostname} {app} {procid} {msgid} {sd} {msg}"

    # ---- Helpers ----
    def _format_priority_prefix(
        self,
        facility: Optional[str],
        severity: Optional[str],
        priority: int,
        is_5424: bool = False,
    ) -> str:
        """
        priority_style에 따라 프리픽스를 생성.
          - "pri":     <PRI>
          - "bracket": [facility.severity]
          - "plain":   facility.severity + 공백
          - "none":    '' (프리픽스 없음)
        facility/severity가 None이면 priority 숫자에서 역복원.
        """
        style = (self.priority_style or "pri").lower()
        if style == "none":
            return ""

        if style == "pri":
            return f"<{priority}>"

        # 나머지 스타일은 이름이 필요 → 없으면 역복원
        if facility is None or severity is None:
            fac_code = priority // 8
            sev_code = priority % 8
            facility = self.FACILITY_BY_CODE.get(fac_code, f"fac{fac_code}")
            severity = self.SEVERITY_BY_CODE.get(sev_code, f"sev{sev_code}")

        if style == "bracket":
            return f"[{facility}.{severity}]"
        elif style == "plain":
            return f"{facility}.{severity} "
        else:
            # 알 수 없는 값이면 기본 PRI로
            return f"<{priority}>"

    def _calculate_priority(self, facility: str, severity: str) -> int:
        return self.FACILITIES[facility] * 8 + self.SEVERITIES[severity]

    def _format_rfc3164_timestamp(self, ts: datetime) -> str:
        return ts.strftime("%b %d %H:%M:%S")

    def _format_rfc5424_timestamp(self, ts: datetime) -> str:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        s = ts.strftime("%Y-%m-%dT%H:%M:%S.%f")
        return s[:-3] + "Z"  # milliseconds + Z

    def _generate_tag(self, facility: str) -> str:
        tags = {
            "kern": ["kernel"],
            "daemon": ["systemd", "NetworkManager", "dbus", "avahi-daemon", "chronyd"],
            "auth": ["sshd", "sudo", "su", "login"],
            "mail": ["postfix/smtpd", "postfix/cleanup", "postfix/qmgr", "dovecot"],
            "cron": ["cron", "CRON"],
            "syslog": ["rsyslogd"],
            "user": ["user_process"],
            "local0": ["local_app"],
            "local1": ["custom_daemon"],
            "local2": ["monitoring"],
            "local3": ["backup"],
        }
        return random.choice(tags.get(facility, [facility]))

    def _generate_app_name(self, facility: str) -> str:
        return self._generate_tag(facility)

    def _generate_msgid(self, facility: str) -> str:
        msgids = {
            "auth": ["LOGIN", "LOGOUT", "FAILED_LOGIN", "SUDO"],
            "mail": ["CONNECT", "DISCONNECT", "DELIVERY", "BOUNCE"],
            "cron": ["JOB_START", "JOB_END", "JOB_FAILED"],
            "daemon": ["START", "STOP", "RELOAD", "ERROR"],
        }
        return random.choice(msgids.get(facility, ["INFO", "ERROR", "WARNING"]))

    def _generate_message(self, facility: str, severity: str) -> str:
        patterns = self.MESSAGE_PATTERNS.get(facility, ["Generic {facility} message"])
        pattern = random.choice(patterns)
        variables = {
            "pid": random.randint(1000, 99999),
            "process": random.choice(
                ["apache2", "nginx", "mysql", "postgres", "python3"]
            ),
            "score": random.randint(0, 1000),
            "ip": self.faker.ipv4(),
            "port": random.randint(1024, 65535),
            "address": hex(random.randint(0x1000, 0xFFFFFFFF)),
            "size": hex(random.randint(0x1000, 0x10000)),
            "cpu": random.randint(0, 7),
            "status": random.choice(["charging", "discharging", "full"]),
            "service": random.choice(
                ["nginx", "apache2", "mysql", "postgresql", "redis"]
            ),
            "code": random.choice([0, 1, 2, 130, 143]),
            "errno": random.randint(1, 255),
            "error": random.choice(
                ["Connection refused", "Permission denied", "No such file"]
            ),
            "user": self.faker.user_name(),
            "tty": random.randint(0, 9),
            "pwd": random.choice(["/home/user", "/var/log", "/etc", "/tmp"]),
            "command": random.choice(["ls -la", "cat /etc/passwd", "systemctl status"]),
            "hostname": self.faker.domain_name(),
            "queue_id": self.faker.lexify("??????????"),
            "message_id": f"{self.faker.lexify('????????')}.{random.randint(10**9, 10**10-1)}@{self.faker.domain_name()}",
            "from": self.faker.email(),
            "to": self.faker.email(),
            "nrcpt": random.randint(1, 5),
            "relay": f"{self.faker.domain_name()}[{self.faker.ipv4()}]:{random.randint(25, 587)}",
            "file": random.choice(["/etc/crontab", "/var/spool/cron/crontabs/root"]),
            "version": f"{random.randint(8, 9)}.{random.randint(1, 50)}.{random.randint(0, 10)}",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "facility": facility,
            "sp": hex(random.randint(0x1000, 0xFFFFFFFF)),  # segfault stack pointer
            "uptime": random.uniform(0.0, 86400.0),  # 커널 uptime
            "iface": random.choice(["eth0", "ens33", "enp0s3", "wlan0"]),
            "link_state": random.choice(["up", "down"]),
            "mac": ":".join(f"{random.randint(0,255):02x}" for _ in range(6)),
            "ip2": self.faker.ipv4(),
            "len": random.randint(40, 1500),
            "ttl": random.randint(32, 255),
            "ip_id": random.randint(1, 65535),
            "proto": random.choice(["TCP", "UDP", "ICMP"]),
            "sport": random.randint(1024, 65535),
            "dport": random.randint(1, 65535),
            "window": random.randint(512, 65535),
            "tcp_flags": random.choice(["SYN", "SYN,ACK", "ACK", "FIN", "RST"]),
            "disk": random.choice(["sda", "sdb", "nvme0n1"]),
            "mount_opts": random.choice(["errors=remount-ro", "noatime", "barrier=1"]),
            "sector": random.randint(8, 10**7),
            "epoch": int(datetime.now().timestamp()),
            "msec": random.randint(100000, 999999),
            "uid": random.randint(1000, 60000),
            "gid": random.randint(1000, 60000),
            "ses": random.randint(1, 999),
            "latency": random.randint(1, 500),
            "latency_thresh": random.choice([100, 200, 250]),
            "sample_rate": random.choice([50000, 25000, 10000]),
            "nm_old_state": random.choice(["disconnected", "connecting", "connected"]),
            "nm_new_state": random.choice(["connected", "disconnecting"]),
            "fqdn": self.faker.domain_name(),
            "container_id": self.faker.lexify("????????????"),
            "image": random.choice(["nginx:1.25", "redis:7", "alpine:3.20"]),
            "delay": f"{random.uniform(0.1, 10.0):.2f}",
            "delays": ",".join(f"{random.uniform(0,3):.1f}" for _ in range(4)),
            "queue_id2": self.faker.lexify("??????????"),
            "bytes_in": random.randint(100, 10**6),
            "bytes_out": random.randint(100, 10**6),
            "home": f"/home/{self.faker.user_name()}",
            "req_id": self.faker.lexify("????????-????????"),
            "url_path": random.choice(["/api/v1/health", "/login", "/orders"]),
            "http_status": random.choice([200, 201, 204, 301, 400, 401, 403, 404, 500]),
            "cache_op": random.choice(["GET", "SET", "DEL"]),
            "cache_key": self.faker.lexify("key-????????"),
            "cache_result": random.choice(["hit", "miss", "set"]),
            "wid": random.randint(1, 16),
            "load_avg": f"{random.uniform(0.0, 8.0):.2f}",
            "reason": random.choice(["OOM", "SIGSEGV", "healthcheck-fail"]),
            "target": self.faker.hostname(),
            "up": random.choice([True, False]),
            "rtt": random.randint(1, 250),
            "alert_id": self.faker.lexify("alert-????"),
            "sev": random.choice(["low", "medium", "high", "critical"]),
            "rule": random.choice(["disk_usage > 90%", "latency_p95 > 200ms"]),
            "snapshot_id": self.faker.lexify("snap-????????"),
            "duration": random.randint(1, 600),
            "removed": random.randint(1, 50),
            "kept": random.randint(10, 100),
            "fingerprint": self.faker.sha1(),
            "path": random.choice(["/home", "/var/log", "/etc/ssh"]),
            "bufsize": random.choice([65536, 131072, 262144]),
        }

        try:
            return pattern.format(**variables)
        except KeyError:
            return pattern

    def _generate_rfc3164_timestamp(self) -> str:
        return self._format_rfc3164_timestamp(datetime.now())

    def _generate_rfc5424_timestamp(self) -> str:
        return self._format_rfc5424_timestamp(datetime.now(timezone.utc))

    def _weighted_choice(self, choices: Dict[str, float]) -> str:
        items, weights = list(choices.keys()), list(choices.values())
        return random.choices(items, weights=weights)[0]
