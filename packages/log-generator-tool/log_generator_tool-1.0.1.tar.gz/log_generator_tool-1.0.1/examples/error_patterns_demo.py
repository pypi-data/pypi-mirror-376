#!/usr/bin/env python3
"""
Demonstration of the error pattern library and management system.
Shows how to use realistic error patterns for log generation testing.
"""

import time
import json
from datetime import datetime, timedelta
from log_generator.patterns import (
    ErrorPattern, ErrorPatternLibrary, ErrorPatternManager,
    ErrorScenario, ErrorFrequencyConfig
)


def demo_error_pattern_library():
    """Demonstrate basic error pattern library functionality"""
    print("=== Error Pattern Library Demo ===")
    
    # Initialize the library
    library = ErrorPatternLibrary()
    
    print(f"Loaded {len(library.patterns)} error patterns")
    print(f"Categories: {library.list_categories()}")
    print(f"Severity levels: {library.list_severities()}")
    
    # Show patterns by category
    print("\n--- Web Server Error Patterns ---")
    web_patterns = library.get_patterns_by_category("web_server")
    for pattern in web_patterns[:3]:  # Show first 3
        print(f"- {pattern.id}: {pattern.description}")
        sample_message = library.generate_error_message(pattern.id)
        print(f"  Sample: {sample_message}")
    
    # Show critical errors
    print("\n--- Critical Error Patterns ---")
    critical_patterns = library.get_patterns_by_severity("critical")
    for pattern in critical_patterns[:2]:  # Show first 2
        print(f"- {pattern.id}: {pattern.description}")
        sample_message = library.generate_error_message(pattern.id)
        print(f"  Sample: {sample_message}")
    
    # Demonstrate weighted random selection
    print("\n--- Weighted Random Selection ---")
    for i in range(5):
        pattern = library.get_weighted_random_pattern(category="application")
        message = library.generate_error_message(pattern.id)
        print(f"{i+1}. [{pattern.severity.upper()}] {message}")
    
    # Generate error scenario
    print("\n--- Error Scenario Generation ---")
    scenario = library.get_error_scenario("database", count=3)
    for i, (pattern_id, message) in enumerate(scenario, 1):
        print(f"{i}. {message}")
    
    # Show library statistics
    print("\n--- Library Statistics ---")
    stats = library.get_statistics()
    print(f"Total patterns: {stats['total_patterns']}")
    print(f"Categories: {stats['categories']}")
    print(f"Severity distribution: {stats['severity_distribution']}")
    print(f"Average weight: {stats['average_weight']:.2f}")


def demo_custom_patterns():
    """Demonstrate adding custom error patterns"""
    print("\n=== Custom Error Patterns Demo ===")
    
    library = ErrorPatternLibrary()
    
    # Create custom error patterns
    custom_patterns = [
        ErrorPattern(
            id="api_gateway_timeout",
            category="infrastructure",
            severity="error",
            message_template="API Gateway timeout: {service} took {duration}ms (limit: {limit}ms) for {endpoint}",
            description="API Gateway request timeout error",
            frequency_weight=2.5,
            context_fields={
                "service": ["user-service", "order-service", "payment-service", "notification-service"],
                "duration": ["5000", "8000", "12000", "15000"],
                "limit": ["3000", "5000", "10000"],
                "endpoint": ["/api/v1/users", "/api/v1/orders", "/api/v1/payments", "/api/v1/notifications"]
            },
            real_world_examples=[
                "API Gateway timeout: user-service took 8000ms (limit: 5000ms) for /api/v1/users",
                "API Gateway timeout: payment-service took 12000ms (limit: 10000ms) for /api/v1/payments"
            ]
        ),
        ErrorPattern(
            id="kubernetes_pod_evicted",
            category="infrastructure",
            severity="warning",
            message_template="Pod {pod_name} evicted from node {node_name}: {reason}",
            description="Kubernetes pod eviction due to resource constraints",
            frequency_weight=1.8,
            context_fields={
                "pod_name": ["web-app-123", "api-server-456", "worker-789", "cache-redis-012"],
                "node_name": ["node-1", "node-2", "node-3", "node-worker-01"],
                "reason": ["OutOfMemory", "DiskPressure", "NodeNotReady", "ResourceQuotaExceeded"]
            }
        ),
        ErrorPattern(
            id="circuit_breaker_open",
            category="application",
            severity="warning",
            message_template="Circuit breaker OPEN for {service}: {failure_count} failures in {time_window}s (threshold: {threshold})",
            description="Circuit breaker pattern activation due to service failures",
            frequency_weight=1.2,
            context_fields={
                "service": ["external-api", "database-connection", "cache-service", "email-service"],
                "failure_count": ["5", "8", "12", "15"],
                "time_window": ["30", "60", "120"],
                "threshold": ["5", "10", "15"]
            }
        )
    ]
    
    # Add custom patterns
    for pattern in custom_patterns:
        success = library.add_custom_pattern(pattern)
        print(f"Added custom pattern '{pattern.id}': {success}")
        
        # Generate sample messages
        for i in range(2):
            message = library.generate_error_message(pattern.id)
            print(f"  Sample {i+1}: {message}")
    
    # Show updated statistics
    print(f"\nLibrary now has {len(library.patterns)} patterns")
    print(f"New categories: {library.list_categories()}")


def demo_error_pattern_manager():
    """Demonstrate advanced error pattern management"""
    print("\n=== Error Pattern Manager Demo ===")
    
    # Initialize manager with custom frequency config
    manager = ErrorPatternManager()
    
    # Configure error frequency
    manager.frequency_config = ErrorFrequencyConfig(
        base_frequency=2.0,  # 2 errors per minute base rate
        peak_hours=[9, 10, 11, 14, 15, 16],  # Business hours
        peak_multiplier=3.0,  # 3x more errors during peak
        burst_probability=0.2,  # 20% chance of error bursts
        burst_multiplier=8.0,  # 8x errors during bursts
        burst_duration_minutes=3
    )
    
    print("Configured error frequency settings:")
    print(f"- Base frequency: {manager.frequency_config.base_frequency} errors/minute")
    print(f"- Peak hours: {manager.frequency_config.peak_hours}")
    print(f"- Peak multiplier: {manager.frequency_config.peak_multiplier}x")
    
    # Create custom error scenario
    custom_scenario = ErrorScenario(
        name="microservice_cascade_failure",
        description="Cascading failure across microservices starting with database issues",
        category="infrastructure",
        patterns=["mysql_connection_lost", "api_gateway_timeout", "kubernetes_pod_evicted"],
        sequence_rules={
            "start_pattern": "mysql_connection_lost",
            "escalation_chain": [
                "mysql_connection_lost",
                "api_gateway_timeout", 
                "kubernetes_pod_evicted"
            ],
            "escalation_delay_minutes": [2, 5, 10]
        },
        duration_minutes=25,
        escalation_probability=0.8
    )
    
    # Add the scenario (first add the custom patterns it references)
    api_timeout_pattern = ErrorPattern(
        id="api_gateway_timeout",
        category="infrastructure", 
        severity="error",
        message_template="API Gateway timeout: {service} took {duration}ms",
        description="API Gateway timeout",
        context_fields={"service": ["user-service"], "duration": ["5000"]}
    )
    
    k8s_eviction_pattern = ErrorPattern(
        id="kubernetes_pod_evicted",
        category="infrastructure",
        severity="warning", 
        message_template="Pod {pod_name} evicted: {reason}",
        description="Pod eviction",
        context_fields={"pod_name": ["web-app-123"], "reason": ["OutOfMemory"]}
    )
    
    manager.add_custom_pattern(api_timeout_pattern)
    manager.add_custom_pattern(k8s_eviction_pattern)
    manager.create_error_scenario(custom_scenario)
    
    print(f"\nCreated custom scenario: {custom_scenario.name}")
    print(f"Duration: {custom_scenario.duration_minutes} minutes")
    print(f"Escalation probability: {custom_scenario.escalation_probability}")
    
    # Start the scenario
    manager.start_error_scenario("microservice_cascade_failure")
    print("\nStarted microservice cascade failure scenario")
    
    # Generate realistic errors
    print("\n--- Realistic Error Generation ---")
    for i in range(10):
        pattern_id, message, metadata = manager.generate_realistic_error()
        
        if pattern_id:
            timestamp = datetime.fromisoformat(metadata['timestamp'])
            is_scenario = metadata.get('is_scenario_error', False)
            scenario_marker = " [SCENARIO]" if is_scenario else ""
            
            print(f"{timestamp.strftime('%H:%M:%S')} [{metadata['severity'].upper()}] {message}{scenario_marker}")
        
        time.sleep(0.1)  # Small delay for demonstration
    
    # Show pattern analytics
    print("\n--- Pattern Analytics ---")
    analytics = manager.get_pattern_analytics("mysql_connection_lost")
    if analytics:
        print(f"Pattern: {analytics['pattern_info']['id']}")
        print(f"Category: {analytics['pattern_info']['category']}")
        print(f"Total usage: {analytics['usage_stats']['total_usage']}")
        print(f"Escalation count: {analytics['usage_stats']['escalation_count']}")
    
    # Show system health indicators
    print("\n--- System Health Indicators ---")
    health = manager.get_system_health_indicators()
    print(f"Health status: {health['health_status'].upper()}")
    print(f"Total errors (last hour): {health['total_errors_last_hour']}")
    print(f"Error rate: {health['error_rate_per_minute']:.2f} errors/minute")
    print(f"Active scenarios: {health['active_scenarios']}")
    
    print("\nRecommendations:")
    for rec in health['recommendations']:
        print(f"- {rec}")
    
    # Stop the scenario
    manager.stop_error_scenario("microservice_cascade_failure")
    print("\nStopped scenario")


def demo_pattern_weight_adjustment():
    """Demonstrate dynamic pattern weight adjustment"""
    print("\n=== Pattern Weight Adjustment Demo ===")
    
    manager = ErrorPatternManager()
    
    pattern_id = "nginx_connection_refused"
    original_pattern = manager.library.get_pattern(pattern_id)
    
    print(f"Original weight for '{pattern_id}': {original_pattern.frequency_weight}")
    
    # Simulate adjusting weights based on "real-world feedback"
    adjustments = [
        (5.0, "Increased due to high occurrence in production"),
        (2.0, "Reduced after infrastructure improvements"),
        (8.0, "Increased during load testing phase"),
        (1.5, "Normalized after testing completion")
    ]
    
    for new_weight, reason in adjustments:
        manager.update_pattern_frequency(pattern_id, new_weight, reason)
        print(f"Updated weight to {new_weight}: {reason}")
    
    # Show weight change history
    analytics = manager.get_pattern_analytics(pattern_id)
    print(f"\nWeight change history for '{pattern_id}':")
    for change in analytics['effectiveness']['weight_changes']:
        timestamp = datetime.fromisoformat(change['timestamp'])
        print(f"- {timestamp.strftime('%H:%M:%S')}: {change['old_weight']} → {change['new_weight']} ({change['reason']})")


def demo_export_import():
    """Demonstrate exporting and importing configurations"""
    print("\n=== Export/Import Demo ===")
    
    library = ErrorPatternLibrary()
    manager = ErrorPatternManager()
    
    # Export patterns
    export_file = "error_patterns_export.json"
    success = library.export_patterns(export_file)
    print(f"Exported patterns to {export_file}: {success}")
    
    # Export manager configuration
    config_file = "error_manager_config.json"
    success = manager.export_configuration(config_file)
    print(f"Exported manager config to {config_file}: {success}")
    
    # Show exported config structure
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"\nExported configuration contains:")
        print(f"- Frequency config: {bool(config.get('frequency_config'))}")
        print(f"- Scenarios: {len(config.get('scenarios', {}))}")
        print(f"- Pattern stats: {len(config.get('pattern_stats', {}))}")
        print(f"- Export timestamp: {config.get('exported_at')}")
        
    except Exception as e:
        print(f"Error reading config: {e}")


def main():
    """Run all demonstrations"""
    print("Error Pattern Library and Management System Demo")
    print("=" * 50)
    
    try:
        demo_error_pattern_library()
        demo_custom_patterns()
        demo_error_pattern_manager()
        demo_pattern_weight_adjustment()
        demo_export_import()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nThe error pattern system provides:")
        print("- Realistic error patterns based on real-world scenarios")
        print("- Weighted random selection for natural error distribution")
        print("- Custom pattern creation and management")
        print("- Error scenario generation with escalation")
        print("- Frequency control with peak hours and burst detection")
        print("- Pattern analytics and system health monitoring")
        print("- Export/import capabilities for configuration management")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()