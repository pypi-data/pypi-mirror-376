#!/usr/bin/env python3
"""
Nginx Log Generator Demo

This script demonstrates how to use the Nginx access and error log generators
to create realistic log entries for testing and development purposes.
"""

from log_generator.generators.nginx import NginxAccessLogGenerator, NginxErrorLogGenerator


def demo_nginx_access_logs():
    """Demonstrate Nginx access log generation."""
    print("=== Nginx Access Log Generator Demo ===\n")
    
    # Combined format (default)
    print("1. Combined Log Format (default):")
    combined_gen = NginxAccessLogGenerator(format_type="combined")
    
    for i in range(3):
        log = combined_gen.generate_log()
        print(f"   {log}")
    
    print(f"\nPattern: {combined_gen.get_log_pattern()}")
    
    # Common format
    print("\n2. Common Log Format:")
    common_gen = NginxAccessLogGenerator(format_type="common")
    
    for i in range(3):
        log = common_gen.generate_log()
        print(f"   {log}")
    
    print(f"\nPattern: {common_gen.get_log_pattern()}")
    
    # Custom configuration
    print("\n3. Custom Configuration (404 errors only):")
    custom_config = {
        'status_codes': {404: 1.0},
        'user_agents': ['TestBot/1.0', 'Scanner/2.0']
    }
    custom_gen = NginxAccessLogGenerator(format_type="combined", custom_config=custom_config)
    
    for i in range(3):
        log = custom_gen.generate_log()
        print(f"   {log}")


def demo_nginx_error_logs():
    """Demonstrate Nginx error log generation."""
    print("\n\n=== Nginx Error Log Generator Demo ===\n")
    
    # Default error generator
    print("1. Default Error Logs:")
    error_gen = NginxErrorLogGenerator()
    
    for i in range(5):
        log = error_gen.generate_log()
        print(f"   {log}")
    
    print(f"\nPattern: {error_gen.get_log_pattern()}")
    
    # Custom error configuration
    print("\n2. Custom Configuration (critical errors only):")
    custom_config = {
        'error_levels': {'crit': 0.7, 'alert': 0.3},
        'error_patterns': [
            'worker process died unexpectedly',
            'could not open error log file',
            'malloc() failed'
        ]
    }
    custom_error_gen = NginxErrorLogGenerator(custom_config=custom_config)
    
    for i in range(3):
        log = custom_error_gen.generate_log()
        print(f"   {log}")


def demo_log_validation():
    """Demonstrate log validation functionality."""
    print("\n\n=== Log Validation Demo ===\n")
    
    access_gen = NginxAccessLogGenerator()
    error_gen = NginxErrorLogGenerator()
    
    # Generate and validate access logs
    print("1. Access Log Validation:")
    access_log = access_gen.generate_log()
    print(f"   Generated: {access_log}")
    print(f"   Valid: {access_gen.validate_log(access_log)}")
    
    # Test with invalid log
    invalid_log = "This is not a valid nginx log"
    print(f"   Invalid: {invalid_log}")
    print(f"   Valid: {access_gen.validate_log(invalid_log)}")
    
    # Generate and validate error logs
    print("\n2. Error Log Validation:")
    error_log = error_gen.generate_log()
    print(f"   Generated: {error_log}")
    print(f"   Valid: {error_gen.validate_log(error_log)}")
    
    print(f"   Invalid: {invalid_log}")
    print(f"   Valid: {error_gen.validate_log(invalid_log)}")


def demo_sample_generation():
    """Demonstrate sample log generation."""
    print("\n\n=== Sample Generation Demo ===\n")
    
    access_gen = NginxAccessLogGenerator()
    error_gen = NginxErrorLogGenerator()
    
    print("1. Access Log Samples:")
    access_samples = access_gen.get_sample_logs(count=3)
    for i, sample in enumerate(access_samples, 1):
        print(f"   Sample {i}: {sample}")
    
    print("\n2. Error Log Samples:")
    error_samples = error_gen.get_sample_logs(count=3)
    for i, sample in enumerate(error_samples, 1):
        print(f"   Sample {i}: {sample}")


if __name__ == "__main__":
    print("Nginx Log Generator Demonstration")
    print("=" * 50)
    
    try:
        demo_nginx_access_logs()
        demo_nginx_error_logs()
        demo_log_validation()
        demo_sample_generation()
        
        print("\n\nDemo completed successfully!")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()