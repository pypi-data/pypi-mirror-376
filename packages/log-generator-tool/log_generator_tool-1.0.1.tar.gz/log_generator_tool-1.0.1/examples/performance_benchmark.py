#!/usr/bin/env python3
"""
Performance benchmark for the log generator tool.

This script measures the actual performance of log generation
and provides detailed statistics.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import log_generator
sys.path.insert(0, str(Path(__file__).parent.parent))

from log_generator.core.engine import LogGeneratorCore
from log_generator.core.factory import LogFactory


def benchmark_performance(total_logs: int = 10000, config_path: str = None):
    """
    Benchmark log generation performance.
    
    Args:
        total_logs: Number of logs to generate for the benchmark
        config_path: Path to configuration file (optional)
    """
    print("=== Log Generator Performance Benchmark ===\n")
    
    # Initialize the core engine
    engine = LogGeneratorCore()
    
    # Set up log factory
    factory = LogFactory()
    engine.set_log_factory(factory)
    
    # Load configuration
    if config_path and Path(config_path).exists():
        engine.load_config(config_path)
        print(f"Configuration loaded from: {config_path}")
    else:
        # Use high-performance configuration
        config = {
            "log_generator": {
                "global": {
                    "output_format": "multi_file",
                    "output_path": "./logs/benchmark",
                    "generation_interval": 0.001,  # 1ms for maximum speed
                    "total_logs": total_logs,
                    "multi_file": {
                        "file_pattern": "bench_{log_type}_{date}.log",
                        "date_format": "%Y%m%d_%H%M%S"
                    }
                },
                "log_types": {
                    "nginx_access": {
                        "enabled": True,
                        "frequency": 0.4,
                        "patterns": ["combined"],
                        "custom_fields": {
                            "status_codes": {200: 0.9, 404: 0.1}
                        }
                    },
                    "fastapi": {
                        "enabled": True,
                        "frequency": 0.35,
                        "log_levels": ["INFO", "DEBUG"],
                        "endpoints": ["/api/users", "/health"]
                    },
                    "syslog": {
                        "enabled": True,
                        "frequency": 0.25,
                        "facilities": ["kern", "daemon"],
                        "severities": ["info", "notice"]
                    }
                }
            }
        }
        engine._config = config
        print("Using optimized benchmark configuration")
    
    print(f"Target logs: {total_logs:,}")
    print(f"Expected log types: nginx_access, fastapi, syslog")
    print()
    
    # Create output directory
    output_dir = Path("./logs/benchmark")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Start benchmark
    print("Starting benchmark...")
    start_time = time.time()
    
    try:
        # Start generation
        engine.start_generation()
        
        # Monitor progress
        last_count = 0
        last_time = start_time
        
        while engine.is_running():
            time.sleep(0.5)  # Check every 500ms
            
            stats = engine.get_statistics()
            current_count = stats['total_logs_generated']
            current_time = time.time()
            
            # Calculate current rate
            if current_time > last_time:
                current_rate = (current_count - last_count) / (current_time - last_time)
                elapsed = current_time - start_time
                
                print(f"\rProgress: {current_count:,}/{total_logs:,} "
                      f"({current_count/total_logs*100:.1f}%) | "
                      f"Rate: {current_rate:.0f} logs/sec | "
                      f"Elapsed: {elapsed:.1f}s", end="")
                
                last_count = current_count
                last_time = current_time
            
            # Check if completed
            if current_count >= total_logs:
                break
    
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
    
    finally:
        # Stop generation
        engine.stop_generation()
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Get final statistics
        final_stats = engine.get_statistics()
        
        print("\n\n=== Benchmark Results ===")
        print(f"Total logs generated: {final_stats['total_logs_generated']:,}")
        print(f"Total duration: {total_duration:.2f} seconds")
        print(f"Average rate: {final_stats['total_logs_generated']/total_duration:.2f} logs/sec")
        print(f"Errors: {final_stats.get('errors_count', 0)}")
        
        # Show distribution by log type
        logs_by_type = final_stats.get('logs_by_type', {})
        if logs_by_type:
            print("\nDistribution by log type:")
            for log_type, count in logs_by_type.items():
                percentage = (count / final_stats['total_logs_generated']) * 100
                print(f"  {log_type}: {count:,} ({percentage:.1f}%)")
        
        # Show generated files
        print(f"\nGenerated files in {output_dir}:")
        for log_file in sorted(output_dir.glob("bench_*.log")):
            file_size = log_file.stat().st_size
            line_count = sum(1 for _ in open(log_file, 'r'))
            print(f"  {log_file.name}: {line_count:,} lines, {file_size:,} bytes")
        
        # Performance rating
        rate = final_stats['total_logs_generated'] / total_duration
        if rate > 1000:
            rating = "🚀 Excellent"
        elif rate > 500:
            rating = "✅ Good"
        elif rate > 100:
            rating = "⚠️ Fair"
        else:
            rating = "❌ Poor"
        
        print(f"\nPerformance Rating: {rating} ({rate:.0f} logs/sec)")


def main():
    """Main benchmark function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Log Generator Performance Benchmark")
    parser.add_argument("--total", "-t", type=int, default=10000,
                       help="Total number of logs to generate (default: 10000)")
    parser.add_argument("--config", "-c", type=str,
                       help="Configuration file path")
    
    args = parser.parse_args()
    
    benchmark_performance(args.total, args.config)


if __name__ == "__main__":
    main()