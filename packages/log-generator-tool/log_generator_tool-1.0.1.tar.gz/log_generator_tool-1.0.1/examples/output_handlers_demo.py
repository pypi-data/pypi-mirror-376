#!/usr/bin/env python3
"""
Demo script showing different output handlers in action.
"""

import tempfile
from pathlib import Path
from datetime import datetime

from log_generator.core.models import LogEntry
from log_generator.outputs import (
    FileOutputHandler,
    ConsoleOutputHandler, 
    JSONOutputHandler,
    ELKJSONOutputHandler,
    NetworkOutputHandler
)


def demo_file_output():
    """Demonstrate file output with rotation."""
    print("=== File Output Handler Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "demo.log"
        
        # Create file handler with small rotation size for demo
        handler = FileOutputHandler(
            log_file,
            rotation_size=200,  # Small size for demo
            max_files=3
        )
        
        # Write some log entries
        for i in range(10):
            handler.write_log(f"Log entry {i+1}: This is a test message")
        
        handler.flush()
        
        print(f"Logs written to: {log_file}")
        if log_file.exists():
            print(f"Current log content:\n{log_file.read_text()}")
        
        # Check for rotated files
        rotated_files = list(log_file.parent.glob(f"{log_file.stem}.*{log_file.suffix}"))
        if rotated_files:
            print(f"Rotated files created: {len(rotated_files)}")
        
        handler.close()


def demo_console_output():
    """Demonstrate console output with colors."""
    print("\n=== Console Output Handler Demo ===")
    
    handler = ConsoleOutputHandler(
        colored=True,
        show_timestamp=True,
        show_log_type=True
    )
    
    # Write different types of log entries
    test_logs = [
        "[INFO] Application started successfully",
        "[WARNING] Configuration file not found, using defaults",
        "[ERROR] Database connection failed",
        "nginx: 192.168.1.100 - GET /index.html 200",
        "fastapi: Request processed in 150ms"
    ]
    
    for log in test_logs:
        handler.write_log(log)
    
    handler.close()


def demo_json_output():
    """Demonstrate JSON output handler."""
    print("\n=== JSON Output Handler Demo ===")
    
    # Create console handler for JSON output
    console_handler = ConsoleOutputHandler(
        colored=False,
        show_timestamp=False,
        show_log_type=False
    )
    
    # Wrap with JSON handler
    json_handler = JSONOutputHandler(
        console_handler,
        pretty_print=True,
        include_raw_message=True
    )
    
    # Create structured log entry
    log_entry = LogEntry(
        timestamp=datetime.now(),
        log_type='nginx',
        level='INFO',
        message='GET /api/users HTTP/1.1',
        source_ip='192.168.1.100',
        status_code=200,
        response_time=0.123,
        custom_fields={'user_id': 'user123', 'endpoint': '/api/users'}
    )
    
    print("Structured LogEntry as JSON:")
    json_handler.write_log(log_entry)
    
    print("\nRaw log string as JSON:")
    json_handler.write_log('nginx: 10.0.0.1 - "GET /health HTTP/1.1" 200 45')
    
    json_handler.close()


def demo_elk_json_output():
    """Demonstrate ELK-compatible JSON output."""
    print("\n=== ELK JSON Output Handler Demo ===")
    
    console_handler = ConsoleOutputHandler(
        colored=False,
        show_timestamp=False,
        show_log_type=False
    )
    
    elk_handler = ELKJSONOutputHandler(
        console_handler,
        pretty_print=True
    )
    
    log_entry = LogEntry(
        timestamp=datetime.now(),
        log_type='nginx',
        level='INFO',
        message='Access log entry',
        source_ip='192.168.1.100',
        status_code=200,
        response_time=0.089
    )
    
    print("ELK-compatible JSON format:")
    elk_handler.write_log(log_entry)
    
    elk_handler.close()


def demo_network_output():
    """Demonstrate network output (mock)."""
    print("\n=== Network Output Handler Demo ===")
    
    try:
        # This will likely fail since we don't have a server running
        # but it demonstrates the API
        handler = NetworkOutputHandler(
            'localhost',
            9999,
            protocol='udp',
            timeout=1.0
        )
        
        handler.write_log("Test network log message")
        print("Network message sent successfully!")
        
        stats = handler.get_statistics()
        print(f"Network stats: {stats}")
        
        handler.close()
        
    except Exception as e:
        print(f"Network demo failed (expected): {e}")
        print("This is normal if no server is running on localhost:9999")


def main():
    """Run all demos."""
    print("Output Handlers Demo")
    print("=" * 50)
    
    demo_file_output()
    demo_console_output()
    demo_json_output()
    demo_elk_json_output()
    demo_network_output()
    
    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    main()