#!/usr/bin/env python3
"""
Basic usage example for the log generator tool.

This example demonstrates basic log generation with the default multi-file output.
Each log type will be saved to a separate file for better organization.
"""

from datetime import datetime
from log_generator.core import LogGenerator, OutputHandler, LogEntry


class SimpleLogGenerator(LogGenerator):
    """Simple example log generator."""
    
    def __init__(self, log_type: str = "example"):
        self.log_type = log_type
        self.counter = 0
    
    def generate_log(self) -> str:
        self.counter += 1
        timestamp = datetime.now()
        entry = LogEntry(
            timestamp=timestamp,
            log_type=self.log_type,
            level="INFO",
            message=f"Example log message #{self.counter}",
            source_ip="192.168.1.100"
        )
        return entry.to_string()
    
    def get_log_pattern(self) -> str:
        return r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*\[INFO\].*Example log message.*"
    
    def validate_log(self, log_entry: str) -> bool:
        return "Example log message" in log_entry and "[INFO]" in log_entry


class ConsoleOutputHandler(OutputHandler):
    """Simple console output handler."""
    
    def __init__(self, prefix: str = "[LOG]"):
        self.prefix = prefix
        self.closed = False
    
    def write_log(self, log_entry: str) -> None:
        if not self.closed:
            print(f"{self.prefix} {log_entry}")
    
    def close(self) -> None:
        self.closed = True
        print(f"{self.prefix} Output handler closed.")


def main():
    """Demonstrate basic usage of the log generator system."""
    print("=== Log Generator Tool - Basic Usage Example ===\n")
    
    # Create generator and output handler
    generator = SimpleLogGenerator("example")
    output_handler = ConsoleOutputHandler()
    
    print("1. Generating sample logs:")
    # Generate some sample logs
    for i in range(5):
        log_entry = generator.generate_log()
        output_handler.write_log(log_entry)
    
    print("\n2. Testing log validation:")
    # Test log validation
    test_log = generator.generate_log()
    is_valid = generator.validate_log(test_log)
    print(f"Generated log: {test_log}")
    print(f"Is valid: {is_valid}")
    
    print(f"\n3. Log pattern: {generator.get_log_pattern()}")
    
    print("\n4. Testing LogEntry model:")
    # Demonstrate LogEntry model
    entry = LogEntry(
        timestamp=datetime.now(),
        log_type="nginx",
        level="ERROR",
        message="Connection timeout",
        source_ip="10.0.0.50",
        status_code=504,
        response_time=30.0,
        custom_fields={"user_id": 12345, "endpoint": "/api/data"}
    )
    
    print("String format:", entry.to_string())
    print("JSON format:", entry.to_json())
    
    # Clean up
    output_handler.close()
    print("\n=== Example completed successfully! ===")


if __name__ == "__main__":
    main()