#!/usr/bin/env python3
"""
Demo script showing how to use the LogGeneratorCore and LogFactory.

This example demonstrates the core engine and factory pattern implementation
for orchestrating log generation.
"""

import time
import tempfile
import os
from pathlib import Path

from log_generator.core import LogGeneratorCore, LogFactoryImpl, ConfigManager
from log_generator.outputs.file_handler import FileOutputHandler
from log_generator.outputs.console_handler import ConsoleOutputHandler


def create_demo_config():
    """Create a demo configuration for testing."""
    return {
        "log_generator": {
            "global": {
                "output_format": "file",
                "output_path": "./logs",
                "generation_interval": 0.5,
                "total_logs": 20
            },
            "log_types": {
                "nginx_access": {
                    "enabled": True,
                    "frequency": 0.6,
                    "patterns": ["combined"],
                    "custom_fields": {
                        "ip_ranges": ["192.168.1.0/24"],
                        "status_codes": {200: 0.8, 404: 0.15, 500: 0.05}
                    }
                },
                "fastapi": {
                    "enabled": True,
                    "frequency": 0.4,
                    "log_levels": ["INFO", "WARNING", "ERROR"],
                    "endpoints": ["/api/users", "/health"]
                }
            }
        }
    }


def main():
    """Main demo function."""
    print("=== LogGeneratorCore and LogFactory Demo ===\n")
    
    # Create temporary directory for logs
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "demo.log"
        
        # Initialize core components
        print("1. Initializing core components...")
        core = LogGeneratorCore()
        factory = LogFactoryImpl()
        
        # Create configuration
        config = create_demo_config()
        
        # Set up core with configuration
        print("2. Setting up configuration...")
        core._config = config  # Direct assignment for demo
        core.set_log_factory(factory)
        
        # Add output handlers
        print("3. Adding output handlers...")
        file_handler = FileOutputHandler(str(log_file))
        console_handler = ConsoleOutputHandler(colored=True)
        
        core.add_output_handler(file_handler)
        core.add_output_handler(console_handler)
        
        # Add error handler
        def error_handler(error):
            print(f"Error occurred: {error}")
        
        core.add_error_handler(error_handler)
        
        # Start generation
        print("4. Starting log generation...")
        print(f"   - Generation interval: {config['log_generator']['global']['generation_interval']}s")
        print(f"   - Total logs to generate: {config['log_generator']['global']['total_logs']}")
        print(f"   - Output file: {log_file}")
        print()
        
        try:
            core.start_generation()
            
            # Monitor progress
            print("5. Monitoring generation progress...")
            while core.is_running():
                stats = core.get_statistics()
                print(f"   Generated: {stats['total_logs_generated']} logs, "
                      f"Rate: {stats['generation_rate']:.2f} logs/sec", end='\r')
                time.sleep(0.5)
            
            print()  # New line after progress
            
        except KeyboardInterrupt:
            print("\n   Interrupted by user")
        
        finally:
            # Stop generation
            print("6. Stopping generation...")
            core.stop_generation()
        
        # Show final statistics
        print("\n7. Final Statistics:")
        stats = core.get_statistics()
        print(f"   Total logs generated: {stats['total_logs_generated']}")
        print(f"   Generation rate: {stats['generation_rate']:.2f} logs/sec")
        print(f"   Errors: {stats['errors_count']}")
        print(f"   Duration: {stats['start_time']} to {stats['end_time']}")
        
        if stats['logs_by_type']:
            print("   Logs by type:")
            for log_type, count in stats['logs_by_type'].items():
                print(f"     {log_type}: {count}")
        
        # Show log file contents
        print(f"\n8. Generated log file contents ({log_file}):")
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                print(f"   File contains {len(lines)} lines")
                if lines:
                    print("   First few lines:")
                    for i, line in enumerate(lines[:5]):
                        print(f"     {i+1}: {line.strip()}")
                    if len(lines) > 5:
                        print(f"     ... and {len(lines) - 5} more lines")
        else:
            print("   Log file was not created")
        
        # Demonstrate factory capabilities
        print("\n9. Factory Information:")
        print(f"   Available generator types: {factory.get_available_types()}")
        print(f"   Active instances: {factory.get_instance_count()}")
        
        # Clean up
        factory.cleanup_instances()
        print(f"   Instances after cleanup: {factory.get_instance_count()}")
    
    print("\n=== Demo completed ===")


if __name__ == "__main__":
    main()