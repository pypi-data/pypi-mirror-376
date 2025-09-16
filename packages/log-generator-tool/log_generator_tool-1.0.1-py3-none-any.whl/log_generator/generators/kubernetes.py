"""
Kubernetes log generators for pod and cluster logs.

This module implements log generators that produce realistic Kubernetes logs
including pod logs, system component logs, and cluster events with proper
metadata, labels, and annotations.
"""

import json
import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from faker import Faker

from ..core.interfaces import LogGenerator
from ..core.models import LogEntry


class KubernetesPodLogGenerator(LogGenerator):
    """
    Generates Kubernetes pod logs with realistic patterns.

    Produces logs similar to kubectl logs output including application logs,
    system messages, and pod lifecycle events with proper metadata and labels.
    """

    # Log levels with distribution
    LOG_LEVELS = {
        "INFO": 0.50,
        "WARN": 0.25,
        "ERROR": 0.15,
        "DEBUG": 0.08,
        "FATAL": 0.02,
    }

    # Common Kubernetes namespaces
    NAMESPACES = [
        "default",
        "kube-system",
        "kube-public",
        "monitoring",
        "logging",
        "ingress-nginx",
        "cert-manager",
        "prometheus",
        "grafana",
        "elasticsearch",
    ]

    # Common pod names and prefixes
    POD_PREFIXES = [
        "web-app",
        "api-server",
        "database",
        "redis-cache",
        "worker",
        "nginx-ingress",
        "prometheus",
        "grafana",
        "elasticsearch",
        "fluentd",
    ]

    # Common container names
    CONTAINER_NAMES = [
        "app",
        "sidecar",
        "proxy",
        "init",
        "monitoring",
        "logging",
        "backup",
        "health-check",
    ]

    # Application log patterns
    APP_LOG_PATTERNS = [
        "Starting {service} service on port {port}",
        "Kubernetes probe succeeded for {probe_type}",
        "Received SIGTERM, gracefully shutting down",
        "Connected to service {service} at {endpoint}",
        "Processing request {request_id} in namespace {namespace}",
        "ConfigMap {configmap} updated, reloading configuration",
        "Secret {secret} mounted successfully",
        "Persistent volume {pv} attached to {mount_path}",
        "Service discovery found {count} endpoints for {service}",
        "Ingress rule updated for host {host}",
    ]

    # Error patterns
    ERROR_PATTERNS = [
        "Failed to connect to service {service}: connection refused",
        "Pod {pod} in namespace {namespace} failed readiness probe",
        "ImagePullBackOff: failed to pull image {image}",
        "CrashLoopBackOff: container {container} exited with code {exit_code}",
        "Insufficient resources: cannot schedule pod {pod}",
        "ConfigMap {configmap} not found in namespace {namespace}",
        "Secret {secret} access denied: insufficient permissions",
        "Volume mount failed: {pv} not available",
        "Network policy denied connection from {source} to {destination}",
        "Certificate {cert} expired, TLS handshake failed",
    ]

    # Kubernetes system components
    SYSTEM_COMPONENTS = [
        "kubelet",
        "kube-proxy",
        "kube-apiserver",
        "kube-controller-manager",
        "kube-scheduler",
        "etcd",
        "coredns",
        "calico-node",
        "flannel",
    ]

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Kubernetes pod log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        # Pod metadata
        self.namespace = self._get_namespace()
        self.pod_name = self._generate_pod_name()
        self.container_name = self._get_container_name()
        self.labels = self._generate_labels()

        # Override defaults with custom config
        if "log_levels" in self.custom_config:
            self.LOG_LEVELS = self.custom_config["log_levels"]
        if "namespaces" in self.custom_config:
            self.NAMESPACES = self.custom_config["namespaces"]

    def generate_log(self) -> str:
        """
        Generate a single Kubernetes pod log entry.

        Returns:
            str: Formatted Kubernetes pod log entry
        """
        timestamp = self._generate_timestamp()
        level = self._weighted_choice(self.LOG_LEVELS)

        # Generate log message based on level
        if level in ["ERROR", "FATAL"]:
            message = self._generate_error_message()
        else:
            message = self._generate_app_message()

        # Kubernetes log format (similar to kubectl logs output)
        log_entry = f"{timestamp} {level} {message}"

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for Kubernetes pod logs.

        Returns:
            str: Regular expression pattern
        """
        return r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) " r"(\w+) (.+)$"

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches Kubernetes pod log format.

        Args:
            log_entry (str): Log entry to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pattern = self.get_log_pattern()
        return bool(re.match(pattern, log_entry))

    def set_custom_fields(self, fields: Dict[str, Any]) -> None:
        """
        Set custom fields for log generation.

        Args:
            fields (Dict[str, Any]): Custom field definitions
        """
        self.custom_config.update(fields)

        if "log_levels" in fields:
            self.LOG_LEVELS = fields["log_levels"]
        if "namespaces" in fields:
            self.NAMESPACES = fields["namespaces"]
        if "pod_name" in fields:
            self.pod_name = fields["pod_name"]
        if "namespace" in fields:
            self.namespace = fields["namespace"]

    def get_pod_metadata(self) -> Dict[str, Any]:
        """
        Get pod metadata.

        Returns:
            Dict containing pod metadata
        """
        return {
            "namespace": self.namespace,
            "pod_name": self.pod_name,
            "container_name": self.container_name,
            "labels": self.labels,
        }

    def _generate_timestamp(self) -> str:
        """Generate timestamp in Kubernetes format."""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def _get_namespace(self) -> str:
        """Get namespace."""
        if "namespace" in self.custom_config:
            return self.custom_config["namespace"]

        return random.choice(self.NAMESPACES)

    def _generate_pod_name(self) -> str:
        """Generate realistic pod name."""
        if "pod_name" in self.custom_config:
            return self.custom_config["pod_name"]

        prefix = random.choice(self.POD_PREFIXES)
        suffix = "".join(random.choices("0123456789abcdef", k=10))
        return f"{prefix}-{suffix}"

    def _get_container_name(self) -> str:
        """Get container name."""
        if "container_name" in self.custom_config:
            return self.custom_config["container_name"]

        return random.choice(self.CONTAINER_NAMES)

    def _generate_labels(self) -> Dict[str, str]:
        """Generate realistic Kubernetes labels."""
        labels = {
            "app": random.choice(["web", "api", "database", "cache"]),
            "version": f"v{random.randint(1, 5)}.{random.randint(0, 10)}.{random.randint(0, 20)}",
            "environment": random.choice(["production", "staging", "development"]),
            "tier": random.choice(["frontend", "backend", "database"]),
        }

        if "labels" in self.custom_config:
            labels.update(self.custom_config["labels"])

        return labels

    def _generate_app_message(self) -> str:
        """Generate application log message."""
        pattern = random.choice(self.APP_LOG_PATTERNS)

        # Fill in placeholders with realistic data
        replacements = {
            "service": random.choice(["api", "database", "cache", "auth"]),
            "port": str(random.randint(3000, 9000)),
            "probe_type": random.choice(["liveness", "readiness", "startup"]),
            "request_id": self.faker.uuid4()[:8],
            "namespace": self.namespace,
            "configmap": f"{self.faker.word()}-config",
            "secret": f"{self.faker.word()}-secret",
            "pv": f"pv-{self.faker.uuid4()[:8]}",
            "mount_path": f"/mnt/{self.faker.word()}",
            "count": str(random.randint(1, 10)),
            "host": self.faker.domain_name(),
            "endpoint": f"http://{self.faker.word()}-service:8080",
        }

        for key, value in replacements.items():
            pattern = pattern.replace(f"{{{key}}}", value)

        return pattern

    def _generate_error_message(self) -> str:
        """Generate error log message."""
        pattern = random.choice(self.ERROR_PATTERNS)

        # Fill in placeholders with realistic data
        replacements = {
            "service": random.choice(["api", "database", "cache", "auth"]),
            "pod": self.pod_name,
            "namespace": self.namespace,
            "image": f"{self.faker.word()}:latest",
            "container": self.container_name,
            "exit_code": str(random.choice([1, 2, 125, 126, 127, 130, 137, 143])),
            "configmap": f"{self.faker.word()}-config",
            "secret": f"{self.faker.word()}-secret",
            "pv": f"pv-{self.faker.uuid4()[:8]}",
            "source": f"{self.faker.word()}-pod",
            "destination": f"{self.faker.word()}-service",
            "cert": f"{self.faker.domain_name()}-tls",
        }

        for key, value in replacements.items():
            pattern = pattern.replace(f"{{{key}}}", value)

        return pattern

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]


class KubernetesEventLogGenerator(LogGenerator):
    """
    Generates Kubernetes cluster event logs.

    Produces logs similar to kubectl get events output including pod lifecycle
    events, scheduling events, and cluster component events.
    """

    # Event types with distribution
    EVENT_TYPES = {"Normal": 0.70, "Warning": 0.30}

    # Event reasons
    NORMAL_REASONS = [
        "Scheduled",
        "Pulled",
        "Created",
        "Started",
        "Killing",
        "SuccessfulMountVolume",
        "SuccessfulAttachVolume",
        "NodeReady",
        "NodeNotReady",
        "Sync",
    ]

    WARNING_REASONS = [
        "Failed",
        "FailedScheduling",
        "FailedMount",
        "FailedAttachVolume",
        "Unhealthy",
        "BackOff",
        "FailedCreatePodSandBox",
        "NetworkNotReady",
        "FreeDiskSpaceFailed",
    ]

    # Object kinds
    OBJECT_KINDS = [
        "Pod",
        "Node",
        "Service",
        "Deployment",
        "ReplicaSet",
        "ConfigMap",
        "Secret",
        "PersistentVolume",
        "PersistentVolumeClaim",
    ]

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Kubernetes event log generator.

        Args:
            custom_config (Dict[str, Any], optional): Custom configuration
        """
        self.faker = Faker()
        self.custom_config = custom_config or {}

        if "event_types" in self.custom_config:
            self.EVENT_TYPES = self.custom_config["event_types"]

    def generate_log(self) -> str:
        """
        Generate a single Kubernetes event log entry.

        Returns:
            str: Formatted Kubernetes event log entry
        """
        timestamp = self._generate_timestamp()
        event_type = self._weighted_choice(self.EVENT_TYPES)
        reason = self._get_reason(event_type)
        object_kind = random.choice(self.OBJECT_KINDS)
        object_name = self._generate_object_name(object_kind)
        message = self._generate_event_message(
            event_type, reason, object_kind, object_name
        )

        # Kubernetes event log format
        log_entry = (
            f"{timestamp} {event_type} {reason} "
            f"{object_kind}/{object_name} {message}"
        )

        return log_entry

    def get_log_pattern(self) -> str:
        """
        Get regex pattern for Kubernetes event logs.

        Returns:
            str: Regular expression pattern
        """
        return (
            r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) "
            r"(Normal|Warning) (\w+) "
            r"(\w+)/([^\s]+) (.+)$"
        )

    def validate_log(self, log_entry: str) -> bool:
        """
        Validate if log entry matches Kubernetes event log format.

        Args:
            log_entry (str): Log entry to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pattern = self.get_log_pattern()
        return bool(re.match(pattern, log_entry))

    def set_custom_fields(self, fields: Dict[str, Any]) -> None:
        """
        Set custom fields for log generation.

        Args:
            fields (Dict[str, Any]): Custom field definitions
        """
        self.custom_config.update(fields)

        if "event_types" in fields:
            self.EVENT_TYPES = fields["event_types"]

    def _generate_timestamp(self) -> str:
        """Generate timestamp in Kubernetes format."""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def _get_reason(self, event_type: str) -> str:
        """Get event reason based on type."""
        if event_type == "Normal":
            return random.choice(self.NORMAL_REASONS)
        else:
            return random.choice(self.WARNING_REASONS)

    def _generate_object_name(self, object_kind: str) -> str:
        """Generate object name based on kind."""
        if object_kind == "Pod":
            prefix = random.choice(["web-app", "api-server", "database"])
            suffix = "".join(random.choices("0123456789abcdef", k=10))
            return f"{prefix}-{suffix}"
        elif object_kind == "Node":
            return f"node-{random.randint(1, 10)}"
        elif object_kind in ["Service", "Deployment"]:
            return f"{self.faker.word()}-{object_kind.lower()}"
        else:
            return f"{self.faker.word()}-{self.faker.uuid4()[:8]}"

    def _generate_event_message(
        self, event_type: str, reason: str, object_kind: str, object_name: str
    ) -> str:
        """Generate event message based on type and reason."""
        if event_type == "Normal":
            if reason == "Scheduled":
                return f"Successfully assigned {object_name} to node-{random.randint(1, 10)}"
            elif reason == "Pulled":
                return f'Container image "{self.faker.word()}:latest" already present on machine'
            elif reason == "Created":
                return f"Created container {self.faker.word()}"
            elif reason == "Started":
                return f"Started container {self.faker.word()}"
            elif reason == "Killing":
                return f"Stopping container {self.faker.word()}"
            else:
                return f"{reason} operation completed successfully"
        else:
            if reason == "Failed":
                return f"Error: {random.choice(['ImagePullBackOff', 'CrashLoopBackOff', 'CreateContainerConfigError'])}"
            elif reason == "FailedScheduling":
                return f"0/3 nodes are available: 3 Insufficient {random.choice(['cpu', 'memory'])}"
            elif reason == "FailedMount":
                return f'Unable to mount volumes for pod "{object_name}": timeout expired waiting for volumes to attach or mount'
            elif reason == "Unhealthy":
                return f"{random.choice(['Liveness', 'Readiness'])} probe failed: {random.choice(['HTTP probe failed', 'Get timeout'])}"
            else:
                return f"{reason}: operation failed with error"

    def _weighted_choice(self, choices: Dict[Any, float]) -> Any:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]
