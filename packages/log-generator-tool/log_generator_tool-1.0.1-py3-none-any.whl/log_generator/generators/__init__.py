"""
Log generators package.

This package contains various log generators for different log types
including Nginx, Apache, Django, Docker, Kubernetes, MySQL, PostgreSQL,
system logs, application logs, and more.
"""

from .apache import ApacheAccessLogGenerator, ApacheErrorLogGenerator
from .django import DjangoRequestLogGenerator, DjangoSQLLogGenerator
from .docker import DockerLogGenerator
from .fastapi import FastAPILogGenerator
from .kubernetes import KubernetesEventLogGenerator, KubernetesPodLogGenerator
from .mysql import (
    MySQLErrorLogGenerator,
    MySQLQueryLogGenerator,
    MySQLSlowQueryLogGenerator,
)
from .nginx import NginxAccessLogGenerator, NginxErrorLogGenerator
from .postgresql import PostgreSQLLogGenerator, PostgreSQLSlowQueryLogGenerator
from .syslog import SyslogGenerator

__all__ = [
    "NginxAccessLogGenerator",
    "NginxErrorLogGenerator",
    "ApacheAccessLogGenerator",
    "ApacheErrorLogGenerator",
    "DjangoRequestLogGenerator",
    "DjangoSQLLogGenerator",
    "DockerLogGenerator",
    "KubernetesPodLogGenerator",
    "KubernetesEventLogGenerator",
    "MySQLQueryLogGenerator",
    "MySQLErrorLogGenerator",
    "MySQLSlowQueryLogGenerator",
    "PostgreSQLLogGenerator",
    "PostgreSQLSlowQueryLogGenerator",
    "SyslogGenerator",
    "FastAPILogGenerator",
]
