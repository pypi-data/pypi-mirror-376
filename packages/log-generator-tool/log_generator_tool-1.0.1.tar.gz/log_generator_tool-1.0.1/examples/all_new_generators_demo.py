#!/usr/bin/env python3
"""
Demo script for all new log generators implemented in task 7.

This script demonstrates the usage of Apache, Django, Docker, Kubernetes, 
MySQL, and PostgreSQL log generators, showing how to create different types 
of logs with various configurations.
"""

import sys
import os

# Add the parent directory to the path so we can import log_generator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_generator.generators.apache import ApacheAccessLogGenerator, ApacheErrorLogGenerator
from log_generator.generators.django import DjangoRequestLogGenerator, DjangoSQLLogGenerator
from log_generator.generators.docker import DockerLogGenerator
from log_generator.generators.kubernetes import KubernetesPodLogGenerator, KubernetesEventLogGenerator
from log_generator.generators.mysql import MySQLQueryLogGenerator, MySQLErrorLogGenerator, MySQLSlowQueryLogGenerator
from log_generator.generators.postgresql import PostgreSQLLogGenerator, PostgreSQLSlowQueryLogGenerator
from log_generator.core.factory import LogFactory


def demo_apache_generators():
    """Demonstrate Apache log generators."""
    print("=" * 60)
    print("APACHE LOG GENERATORS")
    print("=" * 60)
    
    print("\n1. Apache Access Log (Combined Format)")
    print("-" * 40)
    apache_access = ApacheAccessLogGenerator(format_type="combined")
    for i in range(2):
        print(f"  {apache_access.generate_log()}")
    
    print("\n2. Apache Error Log")
    print("-" * 40)
    apache_error = ApacheErrorLogGenerator()
    for i in range(2):
        print(f"  {apache_error.generate_log()}")


def demo_django_generators():
    """Demonstrate Django log generators."""
    print("\n\n" + "=" * 60)
    print("DJANGO LOG GENERATORS")
    print("=" * 60)
    
    print("\n1. Django Request Log")
    print("-" * 40)
    django_request = DjangoRequestLogGenerator()
    for i in range(2):
        log = django_request.generate_log()
        # Print first line only for readability
        print(f"  {log.split(chr(10))[0]}")
    
    print("\n2. Django SQL Log")
    print("-" * 40)
    django_sql = DjangoSQLLogGenerator()
    for i in range(2):
        print(f"  {django_sql.generate_log()}")


def demo_docker_generators():
    """Demonstrate Docker log generators."""
    print("\n\n" + "=" * 60)
    print("DOCKER LOG GENERATORS")
    print("=" * 60)
    
    print("\n1. Docker JSON Format")
    print("-" * 40)
    docker_json = DockerLogGenerator(format_type="json")
    for i in range(2):
        print(f"  {docker_json.generate_log()}")
    
    print("\n2. Docker Text Format")
    print("-" * 40)
    docker_text = DockerLogGenerator(format_type="text")
    for i in range(2):
        print(f"  {docker_text.generate_log()}")


def demo_kubernetes_generators():
    """Demonstrate Kubernetes log generators."""
    print("\n\n" + "=" * 60)
    print("KUBERNETES LOG GENERATORS")
    print("=" * 60)
    
    print("\n1. Kubernetes Pod Logs")
    print("-" * 40)
    k8s_pod = KubernetesPodLogGenerator()
    for i in range(2):
        print(f"  {k8s_pod.generate_log()}")
    
    print("\n2. Kubernetes Event Logs")
    print("-" * 40)
    k8s_event = KubernetesEventLogGenerator()
    for i in range(2):
        print(f"  {k8s_event.generate_log()}")


def demo_mysql_generators():
    """Demonstrate MySQL log generators."""
    print("\n\n" + "=" * 60)
    print("MYSQL LOG GENERATORS")
    print("=" * 60)
    
    print("\n1. MySQL Query Log")
    print("-" * 40)
    mysql_query = MySQLQueryLogGenerator()
    for i in range(2):
        print(f"  {mysql_query.generate_log()}")
    
    print("\n2. MySQL Error Log")
    print("-" * 40)
    mysql_error = MySQLErrorLogGenerator()
    for i in range(2):
        print(f"  {mysql_error.generate_log()}")
    
    print("\n3. MySQL Slow Query Log")
    print("-" * 40)
    mysql_slow = MySQLSlowQueryLogGenerator()
    slow_log = mysql_slow.generate_log()
    # Print first few lines for readability
    lines = slow_log.split('\n')
    for line in lines[:4]:
        print(f"  {line}")
    print(f"  {lines[-1]}")


def demo_postgresql_generators():
    """Demonstrate PostgreSQL log generators."""
    print("\n\n" + "=" * 60)
    print("POSTGRESQL LOG GENERATORS")
    print("=" * 60)
    
    print("\n1. PostgreSQL General Log")
    print("-" * 40)
    postgresql = PostgreSQLLogGenerator()
    for i in range(2):
        print(f"  {postgresql.generate_log()}")
    
    print("\n2. PostgreSQL Slow Query Log")
    print("-" * 40)
    postgresql_slow = PostgreSQLSlowQueryLogGenerator()
    for i in range(2):
        print(f"  {postgresql_slow.generate_log()}")


def demo_factory_integration():
    """Demonstrate factory integration with all new generators."""
    print("\n\n" + "=" * 60)
    print("FACTORY INTEGRATION - ALL NEW GENERATORS")
    print("=" * 60)
    
    factory = LogFactory()
    
    # Show all available types
    print("\nAll Available Generator Types:")
    all_types = sorted(factory.get_available_types())
    for i, log_type in enumerate(all_types, 1):
        print(f"  {i:2d}. {log_type}")
    
    print(f"\nTotal: {len(all_types)} generator types available")
    
    # Demonstrate creating generators through factory
    print("\nSample logs from each new generator type:")
    print("-" * 50)
    
    new_generators = [
        'apache_access', 'apache_error',
        'django_request', 'django_sql',
        'docker', 'kubernetes_pod', 'kubernetes_event',
        'mysql_query', 'mysql_error', 'mysql_slow',
        'postgresql', 'postgresql_slow'
    ]
    
    for gen_type in new_generators:
        try:
            generator = factory.create_generator(gen_type, {})
            log = generator.generate_log()
            # Truncate long logs for display
            if len(log) > 100:
                log = log[:97] + "..."
            # Show only first line for multi-line logs
            log = log.split('\n')[0]
            print(f"  {gen_type:15s}: {log}")
        except Exception as e:
            print(f"  {gen_type:15s}: Error - {e}")


def demo_custom_configurations():
    """Demonstrate custom configurations for new generators."""
    print("\n\n" + "=" * 60)
    print("CUSTOM CONFIGURATIONS DEMO")
    print("=" * 60)
    
    print("\n1. Apache with Custom Status Codes")
    print("-" * 40)
    apache_custom = ApacheAccessLogGenerator(custom_config={
        'status_codes': {404: 0.8, 500: 0.2},
        'url_patterns': ['/missing-page', '/broken-endpoint']
    })
    for i in range(2):
        print(f"  {apache_custom.generate_log()}")
    
    print("\n2. Docker with Custom Container")
    print("-" * 40)
    docker_custom = DockerLogGenerator(custom_config={
        'container_name': 'my-web-app',
        'image_name': 'nginx:alpine'
    })
    metadata = docker_custom.get_container_metadata()
    print(f"  Container: {metadata['container_name']}")
    print(f"  Image: {metadata['image_name']}")
    print(f"  Log: {docker_custom.generate_log()}")
    
    print("\n3. Kubernetes with Custom Namespace")
    print("-" * 40)
    k8s_custom = KubernetesPodLogGenerator(custom_config={
        'namespace': 'production',
        'pod_name': 'web-app-prod-12345'
    })
    metadata = k8s_custom.get_pod_metadata()
    print(f"  Namespace: {metadata['namespace']}")
    print(f"  Pod: {metadata['pod_name']}")
    print(f"  Log: {k8s_custom.generate_log()}")


def main():
    """Main demo function."""
    print("Comprehensive Demo: All New Log Generators (Task 7)")
    print("=" * 60)
    print("Demonstrating Apache, Django, Docker, Kubernetes, MySQL, and PostgreSQL generators")
    
    try:
        demo_apache_generators()
        demo_django_generators()
        demo_docker_generators()
        demo_kubernetes_generators()
        demo_mysql_generators()
        demo_postgresql_generators()
        demo_factory_integration()
        demo_custom_configurations()
        
        print("\n\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("All new log generators are working correctly.")
        print("Task 7 implementation is complete!")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())