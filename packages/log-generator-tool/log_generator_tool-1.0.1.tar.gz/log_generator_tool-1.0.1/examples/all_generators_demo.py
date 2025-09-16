#!/usr/bin/env python3
"""
All Log Generators Demo

This script demonstrates all implemented log generators:
- Nginx Access and Error logs
- Syslog (RFC 3164 and RFC 5424)
- FastAPI application logs
"""

from log_generator.generators import (
    NginxAccessLogGenerator, 
    NginxErrorLogGenerator,
    SyslogGenerator,
    FastAPILogGenerator
)


def demo_nginx_generators():
    """Demonstrate Nginx log generators."""
    print("=== NGINX LOG GENERATORS ===\n")
    
    # Nginx Access Logs
    print("1. Nginx Access Logs (Combined Format):")
    nginx_access = NginxAccessLogGenerator(format_type="combined")
    for i in range(3):
        print(f"   {nginx_access.generate_log()}")
    
    print("\n2. Nginx Access Logs (Common Format):")
    nginx_common = NginxAccessLogGenerator(format_type="common")
    for i in range(3):
        print(f"   {nginx_common.generate_log()}")
    
    print("\n3. Nginx Error Logs:")
    nginx_error = NginxErrorLogGenerator()
    for i in range(3):
        print(f"   {nginx_error.generate_log()}")


def demo_syslog_generators():
    """Demonstrate Syslog generators."""
    print("\n\n=== SYSLOG GENERATORS ===\n")
    
    # RFC 3164 Syslog
    print("1. Syslog RFC 3164 (BSD Syslog):")
    syslog_3164 = SyslogGenerator(rfc_format="3164")
    for i in range(3):
        print(f"   {syslog_3164.generate_log()}")
    
    print("\n2. Syslog RFC 5424 (Structured Syslog):")
    syslog_5424 = SyslogGenerator(rfc_format="5424")
    for i in range(3):
        print(f"   {syslog_5424.generate_log()}")
    
    # Custom syslog with specific facility
    print("\n3. Custom Syslog (Auth facility only):")
    custom_syslog = SyslogGenerator(
        rfc_format="3164",
        custom_config={'facilities': {'auth': 1.0}}
    )
    for i in range(3):
        print(f"   {custom_syslog.generate_log()}")


def demo_fastapi_generators():
    """Demonstrate FastAPI log generators."""
    print("\n\n=== FASTAPI LOG GENERATORS ===\n")
    
    print("1. FastAPI Application Logs (Mixed levels):")
    fastapi_gen = FastAPILogGenerator()
    for i in range(5):
        print(f"   {fastapi_gen.generate_log()}")
    
    print("\n2. FastAPI Error Logs Only:")
    fastapi_errors = FastAPILogGenerator({
        'log_levels': {'ERROR': 1.0}
    })
    for i in range(3):
        print(f"   {fastapi_errors.generate_log()}")
    
    print("\n3. FastAPI Custom Endpoints:")
    fastapi_custom = FastAPILogGenerator({
        'endpoints': ['/api/v2/custom', '/health/check', '/metrics/system']
    })
    for i in range(3):
        print(f"   {fastapi_custom.generate_log()}")


def demo_validation():
    """Demonstrate log validation across all generators."""
    print("\n\n=== LOG VALIDATION DEMO ===\n")
    
    generators = [
        ("Nginx Access", NginxAccessLogGenerator()),
        ("Nginx Error", NginxErrorLogGenerator()),
        ("Syslog RFC3164", SyslogGenerator("3164")),
        ("Syslog RFC5424", SyslogGenerator("5424")),
        ("FastAPI", FastAPILogGenerator())
    ]
    
    for name, generator in generators:
        log = generator.generate_log()
        is_valid = generator.validate_log(log)
        print(f"{name:15} | Valid: {is_valid} | {log[:80]}...")


def demo_custom_configurations():
    """Demonstrate custom configurations."""
    print("\n\n=== CUSTOM CONFIGURATIONS ===\n")
    
    print("1. High Error Rate Nginx:")
    nginx_errors = NginxAccessLogGenerator(
        format_type="combined",
        custom_config={
            'status_codes': {500: 0.5, 404: 0.3, 403: 0.2}
        }
    )
    for i in range(3):
        print(f"   {nginx_errors.generate_log()}")
    
    print("\n2. Critical Syslog Messages:")
    critical_syslog = SyslogGenerator(
        rfc_format="3164",
        custom_config={
            'severities': {'crit': 0.6, 'alert': 0.4},
            'facilities': {'kern': 1.0}
        }
    )
    for i in range(3):
        print(f"   {critical_syslog.generate_log()}")
    
    print("\n3. FastAPI Debug Mode:")
    debug_fastapi = FastAPILogGenerator({
        'log_levels': {'DEBUG': 0.7, 'INFO': 0.3}
    })
    for i in range(3):
        print(f"   {debug_fastapi.generate_log()}")


def demo_patterns():
    """Demonstrate regex patterns for each generator."""
    print("\n\n=== REGEX PATTERNS ===\n")
    
    generators = [
        ("Nginx Access (Combined)", NginxAccessLogGenerator("combined")),
        ("Nginx Access (Common)", NginxAccessLogGenerator("common")),
        ("Nginx Error", NginxErrorLogGenerator()),
        ("Syslog RFC3164", SyslogGenerator("3164")),
        ("Syslog RFC5424", SyslogGenerator("5424")),
        ("FastAPI", FastAPILogGenerator())
    ]
    
    for name, generator in generators:
        pattern = generator.get_log_pattern()
        print(f"{name}:")
        print(f"   Pattern: {pattern}")
        
        # Test the pattern with a sample log
        sample = generator.generate_log()
        import re
        match = re.match(pattern, sample)
        print(f"   Sample:  {sample[:60]}...")
        print(f"   Matches: {match is not None}")
        print()


def demo_sample_generation():
    """Demonstrate sample generation for testing."""
    print("\n\n=== SAMPLE GENERATION FOR TESTING ===\n")
    
    generators = [
        ("Nginx Access", NginxAccessLogGenerator()),
        ("Syslog", SyslogGenerator()),
        ("FastAPI", FastAPILogGenerator())
    ]
    
    for name, generator in generators:
        print(f"{name} Samples:")
        samples = generator.get_sample_logs(count=2)
        for i, sample in enumerate(samples, 1):
            print(f"   {i}. {sample}")
        print()


if __name__ == "__main__":
    print("Log Generator Comprehensive Demo")
    print("=" * 50)
    
    try:
        demo_nginx_generators()
        demo_syslog_generators()
        demo_fastapi_generators()
        demo_validation()
        demo_custom_configurations()
        demo_patterns()
        demo_sample_generation()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nAll generators are working correctly and can be used")
        print("for testing log analysis systems, parsers, and monitoring tools.")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()