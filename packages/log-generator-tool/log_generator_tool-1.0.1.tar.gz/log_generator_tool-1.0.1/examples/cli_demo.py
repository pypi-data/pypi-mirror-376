#!/usr/bin/env python3
"""
CLI Demo Script

This script demonstrates the CLI functionality of the log generator tool.
It shows how to use various CLI commands programmatically.
"""

import subprocess
import sys
import time
import tempfile
import os
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run a CLI command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=10
        )
        if capture_output:
            print(f"Exit code: {result.returncode}")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
        return result
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return None
    except Exception as e:
        print(f"Error running command: {e}")
        return None


def main():
    """Demonstrate CLI functionality."""
    print("=== Log Generator CLI Demo ===\n")
    
    # Base command
    base_cmd = [sys.executable, "-m", "log_generator.cli"]
    
    # 1. Show help
    print("1. Showing CLI help:")
    run_command(base_cmd + ["--help"])
    print("\n" + "="*50 + "\n")
    
    # 2. List available log types
    print("2. Listing available log types:")
    run_command(base_cmd + ["list-types"])
    print("\n" + "="*50 + "\n")
    
    # 3. Create a configuration file
    print("3. Creating configuration file:")
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = os.path.join(temp_dir, "demo_config.yaml")
        
        run_command(base_cmd + ["config", "create", "--file", config_file])
        print("\n" + "="*50 + "\n")
        
        # 4. Show configuration
        print("4. Showing configuration:")
        run_command(base_cmd + ["config", "show", "--file", config_file])
        print("\n" + "="*50 + "\n")
        
        # 5. Validate configuration
        print("5. Validating configuration:")
        run_command(base_cmd + ["config", "validate", "--file", config_file])
        print("\n" + "="*50 + "\n")
    
    # 6. Check status (no generation running)
    print("6. Checking status (no generation running):")
    run_command(base_cmd + ["status"])
    print("\n" + "="*50 + "\n")
    
    # 7. Try to stop (no generation running)
    print("7. Trying to stop (no generation running):")
    run_command(base_cmd + ["stop"])
    print("\n" + "="*50 + "\n")
    
    # 8. Try to monitor (no generation running)
    print("8. Trying to monitor (no generation running):")
    run_command(base_cmd + ["monitor"])
    print("\n" + "="*50 + "\n")
    
    # 9. Show pause/resume commands (not implemented)
    print("9. Testing pause/resume commands:")
    run_command(base_cmd + ["pause"])
    run_command(base_cmd + ["resume"])
    print("\n" + "="*50 + "\n")
    
    print("CLI Demo completed!")
    print("\nTo start actual log generation, use:")
    print("  python -m log_generator.cli start --total 100 --interval 0.5")
    print("\nNote: Some commands require a running log generation process.")


if __name__ == "__main__":
    main()