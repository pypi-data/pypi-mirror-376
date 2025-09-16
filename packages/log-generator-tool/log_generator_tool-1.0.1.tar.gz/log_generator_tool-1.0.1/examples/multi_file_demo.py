#!/usr/bin/env python3
"""
Multi-file output demonstration.

This example shows how to generate logs with separate files for each log type.
"""

import sys
import time
from pathlib import Path

# Add the parent directory to the path so we can import log_generator
sys.path.insert(0, str(Path(__file__).parent.parent))

from log_generator.core.engine import LogGeneratorCore
from log_generator.core.factory import LogFactory
from log_generator.outputs.multi_file_handler import MultiFileOutputHandler


def main():
    """Demonstrate multi-file log generation."""
    print("=== Multi-File Log Generation Demo ===\n")
    
    # Create output directory
    output_dir = Path("./logs/multi_file_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize the core engine
    engine = LogGeneratorCore()
    
    # Set up log factory
    factory = LogFactory()
    engine.set_log_factory(factory)
    
    # Create multi-file output handler
    multi_handler = MultiFileOutputHandler(
        base_path=output_dir,
        file_pattern="{log_type}_{date}.log",
        date_format="%Y%m%d_%H%M%S"
    )
    engine.add_output_handler(multi_handler)
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "default_config.yaml"
    engine.load_config(str(config_path))
    
    print(f"Output directory: {output_dir}")
    print("Starting log generation...")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Start generation
        engine.start_generation()
        
        # Let it run for a while and show progress
        start_time = time.time()
        while engine.is_running():
            time.sleep(2)
            
            # Get statistics
            stats = engine.get_statistics()
            elapsed = time.time() - start_time
            
            print(f"\rElapsed: {elapsed:.1f}s | "
                  f"Total logs: {stats['total_logs_generated']} | "
                  f"Rate: {stats.get('generation_rate', 0):.1f} logs/sec | "
                  f"Types: {len(stats.get('logs_by_type', {}))}", end="")
            
            # Show active log files
            active_types = multi_handler.get_active_log_types()
            if active_types:
                print(f" | Active files: {', '.join(active_types)}", end="")
            
            # Stop after generating some logs for demo
            if stats['total_logs_generated'] >= 50:
                break
    
    except KeyboardInterrupt:
        print("\n\nStopping log generation...")
    
    finally:
        # Stop generation
        engine.stop_generation()
        
        # Show final statistics
        print("\n\n=== Final Statistics ===")
        stats = engine.get_statistics()
        
        print(f"Total logs generated: {stats['total_logs_generated']}")
        print(f"Generation rate: {stats.get('generation_rate', 0):.2f} logs/sec")
        print(f"Errors: {stats.get('errors_count', 0)}")
        
        # Show logs by type
        logs_by_type = stats.get('logs_by_type', {})
        if logs_by_type:
            print("\nLogs by type:")
            for log_type, count in logs_by_type.items():
                print(f"  {log_type}: {count}")
        
        # Show generated files
        print(f"\n=== Generated Files ===")
        file_stats = multi_handler.get_statistics()
        
        for log_type, file_info in file_stats.items():
            file_path = Path(file_info['file_path'])
            file_size = file_info['file_size']
            
            print(f"{log_type}:")
            print(f"  File: {file_path.name}")
            print(f"  Size: {file_size} bytes")
            
            # Show first few lines of each file
            if file_path.exists() and file_size > 0:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:3]  # First 3 lines
                    
                    print(f"  Preview:")
                    for i, line in enumerate(lines, 1):
                        print(f"    {i}: {line.strip()}")
                    
                    if len(lines) >= 3:
                        print(f"    ... (total {len(f.readlines()) + 3} lines)")
                
                except Exception as e:
                    print(f"  Error reading file: {e}")
            
            print()
        
        print(f"All files saved to: {output_dir}")


if __name__ == "__main__":
    main()