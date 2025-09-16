#!/usr/bin/env python3
"""
Demo script for Apache and Django log generators.

This script demonstrates the usage of the new Apache and Django log generators,
showing how to create different types of logs with various configurations.
"""

import sys
import os

# Add the parent directory to the path so we can import log_generator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_generator.generators.apache import ApacheAccessLogGenerator, ApacheErrorLogGenerator
from log_generator.generators.django import DjangoRequestLogGenerator, DjangoSQLLogGenerator
from log_generator.core.factory import LogFactory


def demo_apache_generators():
    """Demonstrate Apache log generators."""
    print("=" * 60)
    print("APACHE LOG GENERATORS DEMO")
    print("=" * 60)
    
    # Apache Access Log Generator - Combined Format
    print("\n1. Apache Access Log Generator (Combined Format)")
    print("-" * 50)
    
    apache_access = ApacheAccessLogGenerator(format_type="combined")
    
    for i in range(3):
        log_entry = apache_access.generate_log()
        print(f"Log {i+1}: {log_entry}")
    
    # Apache Access Log Generator - Common Format
    print("\n2. Apache Access Log Generator (Common Format)")
    print("-" * 50)
    
    apache_access_common = ApacheAccessLogGenerator(format_type="common")
    
    for i in range(3):
        log_entry = apache_access_common.generate_log()
        print(f"Log {i+1}: {log_entry}")
    
    # Apache Error Log Generator
    print("\n3. Apache Error Log Generator")
    print("-" * 50)
    
    apache_error = ApacheErrorLogGenerator()
    
    for i in range(3):
        log_entry = apache_error.generate_log()
        print(f"Log {i+1}: {log_entry}")
    
    # Custom configuration example
    print("\n4. Apache Access Log with Custom Configuration")
    print("-" * 50)
    
    custom_config = {
        'status_codes': {200: 0.5, 404: 0.3, 500: 0.2},
        'url_patterns': ['/api/v1/users', '/api/v1/orders', '/api/v1/products'],
        'user_agents': ['CustomBot/1.0', 'TestAgent/2.0']
    }
    
    apache_custom = ApacheAccessLogGenerator(custom_config=custom_config)
    
    for i in range(3):
        log_entry = apache_custom.generate_log()
        print(f"Log {i+1}: {log_entry}")


def demo_django_generators():
    """Demonstrate Django log generators."""
    print("\n\n" + "=" * 60)
    print("DJANGO LOG GENERATORS DEMO")
    print("=" * 60)
    
    # Django Request Log Generator
    print("\n1. Django Request Log Generator")
    print("-" * 50)
    
    django_request = DjangoRequestLogGenerator()
    
    for i in range(5):
        log_entry = django_request.generate_log()
        print(f"Log {i+1}: {log_entry}")
        print()  # Add blank line for readability
    
    # Django SQL Log Generator
    print("\n2. Django SQL Log Generator")
    print("-" * 50)
    
    django_sql = DjangoSQLLogGenerator()
    
    for i in range(5):
        log_entry = django_sql.generate_log()
        print(f"Log {i+1}: {log_entry}")
    
    # Custom Django configuration
    print("\n3. Django Request Log with Custom Configuration")
    print("-" * 50)
    
    custom_config = {
        'status_codes': {200: 0.8, 404: 0.1, 500: 0.1},
        'url_patterns': ['/api/users/', '/api/orders/', '/admin/'],
        'log_levels': {'INFO': 0.7, 'ERROR': 0.3}
    }
    
    django_custom = DjangoRequestLogGenerator(custom_config=custom_config)
    
    for i in range(3):
        log_entry = django_custom.generate_log()
        print(f"Log {i+1}: {log_entry}")
        print()


def demo_factory_integration():
    """Demonstrate factory integration with new generators."""
    print("\n\n" + "=" * 60)
    print("FACTORY INTEGRATION DEMO")
    print("=" * 60)
    
    factory = LogFactory()
    
    print("\nAvailable generator types:")
    for log_type in sorted(factory.get_available_types()):
        print(f"  - {log_type}")
    
    print("\nCreating generators through factory:")
    print("-" * 40)
    
    # Create Apache generators through factory
    apache_access = factory.create_generator('apache_access', {
        'custom_fields': {
            'status_codes': {200: 0.9, 404: 0.1}
        }
    })
    
    apache_error = factory.create_generator('apache_error', {})
    
    # Create Django generators through factory
    django_request = factory.create_generator('django_request', {})
    django_sql = factory.create_generator('django_sql', {})
    
    print(f"Apache Access: {apache_access.generate_log()}")
    print(f"Apache Error: {apache_error.generate_log()}")
    print(f"Django Request: {django_request.generate_log()}")
    print(f"Django SQL: {django_sql.generate_log()}")


def demo_log_validation():
    """Demonstrate log validation capabilities."""
    print("\n\n" + "=" * 60)
    print("LOG VALIDATION DEMO")
    print("=" * 60)
    
    # Apache validation
    print("\n1. Apache Log Validation")
    print("-" * 30)
    
    apache_access = ApacheAccessLogGenerator()
    generated_log = apache_access.generate_log()
    is_valid = apache_access.validate_log(generated_log)
    
    print(f"Generated log: {generated_log}")
    print(f"Is valid: {is_valid}")
    
    # Test with invalid log
    invalid_log = "This is not a valid Apache log"
    is_valid_invalid = apache_access.validate_log(invalid_log)
    print(f"Invalid log: {invalid_log}")
    print(f"Is valid: {is_valid_invalid}")
    
    # Django validation
    print("\n2. Django Log Validation")
    print("-" * 30)
    
    django_request = DjangoRequestLogGenerator()
    generated_log = django_request.generate_log()
    is_valid = django_request.validate_log(generated_log)
    
    print(f"Generated log: {generated_log}")
    print(f"Is valid: {is_valid}")


def main():
    """Main demo function."""
    print("Apache and Django Log Generators Demo")
    print("=====================================")
    
    try:
        demo_apache_generators()
        demo_django_generators()
        demo_factory_integration()
        demo_log_validation()
        
        print("\n\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())