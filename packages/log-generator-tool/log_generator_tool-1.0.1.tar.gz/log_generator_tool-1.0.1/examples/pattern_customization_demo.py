#!/usr/bin/env python3
"""
Demonstration of pattern customization and Faker integration.
Shows how to create custom log patterns with realistic data generation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from log_generator.patterns import (
    TemplateParser, 
    PatternManager, 
    LogPattern, 
    FakerDataGenerator,
    FrequencyController,
    PatternValidator
)


def demo_template_parser():
    """Demonstrate template parser functionality"""
    print("=== Template Parser Demo ===")
    
    # Create parser with Faker integration
    parser = TemplateParser(faker_locale='en_US', faker_seed=42)
    
    # Simple template
    simple_template = "{timestamp} [INFO] Application started"
    print(f"Simple template: {simple_template}")
    print(f"Generated: {parser.generate_log(simple_template)}")
    print()
    
    # Template with choices
    choice_template = "{timestamp} [{log_level:INFO,WARN,ERROR}] {message}"
    print(f"Choice template: {choice_template}")
    for i in range(3):
        print(f"Generated {i+1}: {parser.generate_log(choice_template, {'message': f'Message {i+1}'})}")
    print()
    
    # Template with Faker fields
    faker_template = "{iso_timestamp} [{log_level}] Request from {ip_address} - User: {username} - Status: {http_status_code}"
    print(f"Faker template: {faker_template}")
    for i in range(3):
        print(f"Generated {i+1}: {parser.generate_log(faker_template)}")
    print()
    
    # Complex template with parameters
    complex_template = (
        "{timestamp} [{log_level:INFO,WARN,ERROR}] "
        "{http_method} {url} - Status: {http_status_code} - "
        "Response Time: {response_time}ms - "
        "User-Agent: {user_agent}"
    )
    print(f"Complex template: {complex_template}")
    print(f"Generated: {parser.generate_log(complex_template)}")
    print()


def demo_pattern_manager():
    """Demonstrate pattern manager functionality"""
    print("=== Pattern Manager Demo ===")
    
    # Create pattern manager
    manager = PatternManager(patterns_dir="demo_patterns")
    
    # Create custom patterns
    web_pattern = LogPattern(
        name="custom_web_access",
        template="{timestamp} {ip_address} - {username} [{iso_timestamp}] \"{http_method} {url} HTTP/1.1\" {http_status_code} {file_size} \"{referer}\" \"{user_agent}\"",
        description="Custom web access log pattern with Faker integration",
        category="web_server",
        fields={
            "ip_address": {"type": "faker", "generator": "ip_address"},
            "username": {"type": "faker", "generator": "username"},
            "http_method": {"type": "faker", "generator": "http_method"},
            "url": {"type": "choice", "options": ["/", "/api/users", "/api/orders", "/health"]},
            "http_status_code": {"type": "faker", "generator": "http_status_code"},
            "file_size": {"type": "faker", "generator": "file_size"},
            "referer": {"type": "faker", "generator": "referer"},
            "user_agent": {"type": "faker", "generator": "user_agent"}
        }
    )
    
    api_pattern = LogPattern(
        name="api_request_detailed",
        template="{iso_timestamp} [API] {session_id} {http_method} {endpoint} - Status: {http_status_code} - Duration: {response_time}ms - User: {email}",
        description="Detailed API request log pattern",
        category="application",
        fields={
            "session_id": {"type": "faker", "generator": "session_id"},
            "http_method": {"type": "faker", "generator": "http_method"},
            "endpoint": {"type": "choice", "options": ["/api/v1/users", "/api/v1/orders", "/api/v1/products", "/api/v1/auth"]},
            "http_status_code": {"type": "faker", "generator": "http_status_code"},
            "response_time": {"type": "faker", "generator": "response_time"},
            "email": {"type": "faker", "generator": "email"}
        }
    )
    
    # Add patterns
    manager.add_pattern(web_pattern)
    manager.add_pattern(api_pattern)
    
    print("Added patterns:")
    for pattern in manager.list_patterns():
        print(f"- {pattern.name}: {pattern.description}")
    print()
    
    # Generate logs from patterns
    print("Generated logs:")
    for i in range(3):
        web_log = manager.generate_log_from_pattern("custom_web_access")
        print(f"Web {i+1}: {web_log}")
    
    for i in range(3):
        api_log = manager.generate_log_from_pattern("api_request_detailed")
        print(f"API {i+1}: {api_log}")
    print()


def demo_faker_integration():
    """Demonstrate Faker integration"""
    print("=== Faker Integration Demo ===")
    
    # Create Faker generator
    faker_gen = FakerDataGenerator(seed=42)
    
    print("Available Faker generators:")
    generators = faker_gen.get_available_generators()
    for i, gen in enumerate(sorted(generators)[:20]):  # Show first 20
        print(f"  {gen}")
    print(f"... and {len(generators) - 20} more")
    print()
    
    # Demonstrate different data types
    print("Sample generated data:")
    sample_fields = [
        'ip_address', 'user_agent', 'http_method', 'http_status_code',
        'timestamp', 'username', 'email', 'response_time', 'file_size'
    ]
    
    for field in sample_fields:
        values = [faker_gen.generate(field) for _ in range(3)]
        print(f"{field:15}: {', '.join(values)}")
    print()
    
    # Demonstrate frequency control
    print("Frequency control demo:")
    faker_gen.set_frequency_control('http_status_code', {
        '200': 0.8,
        '404': 0.1,
        '500': 0.1
    })
    
    status_codes = [faker_gen.generate('http_status_code_controlled') for _ in range(20)]
    print(f"Status codes with frequency control: {status_codes}")
    print(f"200 count: {status_codes.count('200')}, 404 count: {status_codes.count('404')}, 500 count: {status_codes.count('500')}")
    print()


def demo_frequency_controller():
    """Demonstrate frequency controller"""
    print("=== Frequency Controller Demo ===")
    
    controller = FrequencyController()
    
    # Set up realistic web patterns
    controller.create_realistic_web_patterns()
    
    print("Created realistic web patterns")
    stats = controller.get_statistics()
    print(f"Statistics: {stats}")
    print()
    
    # Demonstrate controlled value generation
    def mock_status_generator():
        return "200"  # Default generator always returns 200
    
    print("Controlled value generation:")
    status_codes = []
    for _ in range(20):
        status = controller.get_controlled_value('http_status_code', mock_status_generator)
        status_codes.append(status)
    
    print(f"Generated status codes: {status_codes}")
    print(f"Distribution: 200={status_codes.count('200')}, 404={status_codes.count('404')}, 500={status_codes.count('500')}")
    print()
    
    # Demonstrate correlation
    print("Correlation demo:")
    for _ in range(5):
        context = {'http_status_code': '500'}  # Simulate 500 error
        response_time = controller.get_controlled_value('response_time', lambda: "50", context)
        print(f"Status 500 -> Response time: {response_time}")
    print()


def demo_pattern_validation():
    """Demonstrate pattern validation"""
    print("=== Pattern Validation Demo ===")
    
    validator = PatternValidator()
    
    # Test valid pattern
    valid_pattern = "{timestamp} [{log_level:INFO,WARN,ERROR}] {message}"
    validation = validator.validate_pattern_syntax(valid_pattern)
    print(f"Valid pattern: {valid_pattern}")
    print(f"Validation result: Valid={validation['valid']}, Errors={len(validation['errors'])}, Fields={len(validation['fields'])}")
    print()
    
    # Test pattern generation
    print("Pattern generation test:")
    test_result = validator.test_pattern_generation(valid_pattern, count=5)
    print(f"Success: {test_result['success']}")
    print("Generated samples:")
    for i, sample in enumerate(test_result['samples']):
        print(f"  {i+1}: {sample}")
    print()
    
    # Performance benchmark
    print("Performance benchmark:")
    perf_result = validator.benchmark_pattern_performance(valid_pattern, iterations=100)
    print(f"Average time: {perf_result['average_time']:.6f}s")
    print(f"Success rate: {perf_result['success_rate']:.2%}")
    print()
    
    # Pattern improvement suggestions
    simple_pattern = "{message}"
    suggestions = validator.suggest_pattern_improvements(simple_pattern)
    print(f"Improvement suggestions for '{simple_pattern}':")
    for suggestion in suggestions:
        print(f"  - {suggestion}")
    print()


def demo_integration_example():
    """Demonstrate full integration example"""
    print("=== Full Integration Example ===")
    
    # Create integrated system
    parser = TemplateParser(faker_locale='en_US', faker_seed=42)
    controller = FrequencyController()
    controller.create_realistic_web_patterns()
    
    # Complex template with realistic patterns
    template = (
        "{timestamp} {ip_address} - {username} [{iso_timestamp}] "
        "\"{http_method} {endpoint:/,/api/users,/api/orders,/health,/login} HTTP/1.1\" "
        "{http_status_code} {file_size} \"{referer}\" \"{user_agent}\" "
        "rt={response_time}ms"
    )
    
    print(f"Integrated template: {template}")
    print("\nGenerated realistic logs:")
    
    for i in range(5):
        log = parser.generate_log(template)
        print(f"{i+1:2d}: {log}")
    
    print("\nThis demonstrates:")
    print("- Faker integration for realistic data (IP, user agent, etc.)")
    print("- Choice fields for endpoints")
    print("- Realistic distributions (status codes, response times)")
    print("- Complex template parsing")
    print()


def main():
    """Run all demonstrations"""
    print("Pattern Customization and Faker Integration Demo")
    print("=" * 50)
    print()
    
    demo_template_parser()
    demo_pattern_manager()
    demo_faker_integration()
    demo_frequency_controller()
    demo_pattern_validation()
    demo_integration_example()
    
    print("Demo completed!")


if __name__ == "__main__":
    main()