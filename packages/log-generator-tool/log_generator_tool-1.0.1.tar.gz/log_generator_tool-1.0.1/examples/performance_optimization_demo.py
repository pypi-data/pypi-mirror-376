"""
Performance optimization demonstration for the log generator.

This example shows how to use performance monitoring and optimization
features to improve log generation throughput and efficiency.
"""

import os
import tempfile
import time
from pathlib import Path

from log_generator.core.engine import LogGeneratorCore
from log_generator.core.factory import LogFactory
from log_generator.core.performance import (
    PerformanceMonitor, 
    BatchProcessor, 
    MemoryOptimizer,
    PerformanceProfiler
)
from log_generator.outputs.file_handler import FileOutputHandler


def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring capabilities."""
    print("=== Performance Monitoring Demo ===")
    
    # Create temporary directory for output
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Configuration for high-volume generation
        config = {
            "log_generator": {
                "global": {
                    "generation_interval": 0.01,  # Fast generation
                    "total_logs": 2000
                },
                "log_types": {
                    "nginx_access": {"enabled": True, "frequency": 0.5},
                    "syslog": {"enabled": True, "frequency": 0.3},
                    "fastapi": {"enabled": True, "frequency": 0.2}
                }
            }
        }
        
        # Initialize engine
        engine = LogGeneratorCore()
        engine._config = config
        
        factory = LogFactory()
        engine.set_log_factory(factory)
        
        output_path = os.path.join(temp_dir, "performance_demo.log")
        handler = FileOutputHandler(output_path)
        engine.add_output_handler(handler)
        
        # Set up performance monitoring
        monitor = PerformanceMonitor(max_history=500)
        
        # Add callback to print periodic updates
        def print_metrics(metrics):
            if metrics.logs_generated > 0 and metrics.logs_generated % 500 == 0:
                print(f"Generated: {metrics.logs_generated}, "
                      f"Rate: {metrics.generation_rate:.1f} logs/sec, "
                      f"Memory: {metrics.memory_usage_mb:.1f}MB")
        
        monitor.add_callback(print_metrics)
        
        # Start monitoring
        monitor.start_monitoring(0.5)
        
        print("Starting high-volume log generation with monitoring...")
        
        # Start generation
        start_time = time.time()
        engine.start_generation()
        
        # Update monitor with engine statistics
        while engine.is_running():
            stats = engine.get_statistics()
            monitor.record_metrics(
                logs_generated=stats["total_logs_generated"],
                generation_rate=stats.get("generation_rate", 0),
                error_count=stats.get("error_count", 0)
            )
            time.sleep(0.2)
        
        duration = time.time() - start_time
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        # Get final statistics
        final_stats = engine.get_statistics()
        perf_summary = monitor.get_performance_summary()
        
        print(f"\nGeneration completed in {duration:.2f} seconds")
        print(f"Total logs generated: {final_stats['total_logs_generated']}")
        print(f"Average rate: {final_stats['total_logs_generated']/duration:.1f} logs/sec")
        
        print("\nPerformance Summary:")
        print(f"  Memory - Avg: {perf_summary['memory']['average_mb']:.1f}MB, "
              f"Peak: {perf_summary['memory']['peak_mb']:.1f}MB")
        print(f"  CPU - Avg: {perf_summary['cpu']['average_percent']:.1f}%, "
              f"Peak: {perf_summary['cpu']['peak_percent']:.1f}%")
        print(f"  Rate - Avg: {perf_summary['generation_rate']['average_logs_per_sec']:.1f} logs/sec, "
              f"Peak: {perf_summary['generation_rate']['peak_logs_per_sec']:.1f} logs/sec")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def demonstrate_batch_processing():
    """Demonstrate batch processing optimization."""
    print("\n=== Batch Processing Demo ===")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create batch processor
        batch_processor = BatchProcessor(batch_size=50, flush_interval=2.0)
        
        # Output file for batched writes
        batch_output_file = os.path.join(temp_dir, "batched_output.log")
        
        def batch_writer(batch_items):
            """Write batch of items to file."""
            with open(batch_output_file, 'a') as f:
                for item in batch_items:
                    f.write(f"{item}\n")
            print(f"Wrote batch of {len(batch_items)} items")
        
        batch_processor.add_processor(batch_writer)
        
        # Simulate log generation with batching
        print("Generating logs with batch processing...")
        
        factory = LogFactory()
        nginx_generator = factory.create_generator("nginx_access", {"enabled": True, "frequency": 1.0})
        
        start_time = time.time()
        
        # Generate logs and add to batch
        for i in range(200):
            log_entry = nginx_generator.generate_log()
            batch_processor.add_item(log_entry)
            
            if i % 50 == 0:
                print(f"Generated {i} logs...")
            
            time.sleep(0.01)  # Simulate generation interval
        
        # Flush remaining items
        batch_processor.flush()
        
        duration = time.time() - start_time
        
        # Verify output
        output_file = Path(batch_output_file)
        if output_file.exists():
            with open(output_file, 'r') as f:
                lines = f.readlines()
            
            print(f"Batch processing completed in {duration:.2f} seconds")
            print(f"Total lines written: {len(lines)}")
            print(f"Average rate: {len(lines)/duration:.1f} logs/sec")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def demonstrate_memory_optimization():
    """Demonstrate memory optimization features."""
    print("\n=== Memory Optimization Demo ===")
    
    # Create memory optimizer
    memory_optimizer = MemoryOptimizer(gc_threshold=50.0, gc_interval=10.0)
    
    print("Initial memory stats:")
    initial_stats = memory_optimizer.get_memory_stats()
    print(f"  Current: {initial_stats['current_mb']:.1f}MB")
    print(f"  Baseline: {initial_stats['baseline_mb']:.1f}MB")
    
    # Simulate memory-intensive operations
    print("\nSimulating memory-intensive log generation...")
    
    factory = LogFactory()
    generators = {}
    
    # Create multiple generators
    log_types = ["nginx_access", "syslog", "fastapi", "mysql_query"]
    for log_type in log_types:
        try:
            generators[log_type] = factory.create_generator(
                log_type, {"enabled": True, "frequency": 1.0}
            )
        except Exception:
            pass  # Skip if generator not available
    
    # Generate lots of logs to increase memory usage
    all_logs = []
    
    for i in range(1000):
        for log_type, generator in generators.items():
            log_entry = generator.generate_log()
            all_logs.append(log_entry)
        
        # Check memory periodically
        if i % 200 == 0:
            current_stats = memory_optimizer.get_memory_stats()
            print(f"  Iteration {i}: Memory = {current_stats['current_mb']:.1f}MB "
                  f"(+{current_stats['growth_mb']:.1f}MB)")
            
            # Check if optimization is needed
            if memory_optimizer.check_memory():
                print("    Performed garbage collection")
                optimized_stats = memory_optimizer.get_memory_stats()
                print(f"    After GC: {optimized_stats['current_mb']:.1f}MB")
    
    # Final memory stats
    final_stats = memory_optimizer.get_memory_stats()
    print(f"\nFinal memory stats:")
    print(f"  Current: {final_stats['current_mb']:.1f}MB")
    print(f"  Growth: {final_stats['growth_mb']:.1f}MB")
    print(f"  Total logs generated: {len(all_logs)}")


def demonstrate_performance_profiling():
    """Demonstrate performance profiling capabilities."""
    print("\n=== Performance Profiling Demo ===")
    
    profiler = PerformanceProfiler()
    factory = LogFactory()
    
    # Profile different log generator types
    log_types = ["nginx_access", "syslog", "fastapi"]
    
    for log_type in log_types:
        try:
            print(f"\nProfiling {log_type} generator...")
            
            # Profile generator creation
            with profiler.profile(f"{log_type}_creation"):
                generator = factory.create_generator(
                    log_type, {"enabled": True, "frequency": 1.0}
                )
            
            # Profile log generation
            for i in range(100):
                with profiler.profile(f"{log_type}_generation"):
                    log_entry = generator.generate_log()
                
                # Profile log validation
                with profiler.profile(f"{log_type}_validation"):
                    generator.validate_log(log_entry)
        
        except Exception as e:
            print(f"  Skipped {log_type}: {e}")
    
    # Display profiling results
    print("\nProfiling Results:")
    all_profiles = profiler.get_all_profiles()
    
    for profile_name, stats in all_profiles.items():
        if stats:
            print(f"  {profile_name}:")
            print(f"    Count: {stats['count']}")
            print(f"    Average: {stats['average']*1000:.2f}ms")
            print(f"    Min: {stats['min']*1000:.2f}ms")
            print(f"    Max: {stats['max']*1000:.2f}ms")
            print(f"    Total: {stats['total']:.3f}s")


def demonstrate_optimized_generation():
    """Demonstrate optimized log generation with all features."""
    print("\n=== Optimized Generation Demo ===")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Configuration for optimized generation
        config = {
            "log_generator": {
                "global": {
                    "generation_interval": 0.005,  # Very fast
                    "total_logs": 3000
                },
                "log_types": {
                    "nginx_access": {"enabled": True, "frequency": 0.4},
                    "syslog": {"enabled": True, "frequency": 0.3},
                    "fastapi": {"enabled": True, "frequency": 0.3}
                }
            }
        }
        
        # Initialize all optimization components
        monitor = PerformanceMonitor()
        memory_optimizer = MemoryOptimizer(gc_threshold=30.0)
        profiler = PerformanceProfiler()
        
        # Initialize engine
        engine = LogGeneratorCore()
        engine._config = config
        
        factory = LogFactory()
        engine.set_log_factory(factory)
        
        output_path = os.path.join(temp_dir, "optimized_output.log")
        handler = FileOutputHandler(output_path)
        engine.add_output_handler(handler)
        
        print("Starting optimized log generation...")
        
        # Start monitoring
        monitor.start_monitoring(0.3)
        
        # Profile the entire generation process
        with profiler.profile("total_generation"):
            start_time = time.time()
            engine.start_generation()
            
            # Monitor and optimize during generation
            while engine.is_running():
                stats = engine.get_statistics()
                
                # Update performance monitor
                monitor.record_metrics(
                    logs_generated=stats["total_logs_generated"],
                    generation_rate=stats.get("generation_rate", 0),
                    error_count=stats.get("error_count", 0)
                )
                
                # Check memory optimization
                if memory_optimizer.check_memory():
                    print("  Performed memory optimization")
                
                time.sleep(0.1)
            
            duration = time.time() - start_time
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        # Get final results
        final_stats = engine.get_statistics()
        perf_summary = monitor.get_performance_summary()
        generation_profile = profiler.get_profile_stats("total_generation")
        
        print(f"\nOptimized generation completed!")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Logs generated: {final_stats['total_logs_generated']}")
        print(f"Throughput: {final_stats['total_logs_generated']/duration:.1f} logs/sec")
        print(f"Errors: {final_stats.get('error_count', 0)}")
        
        print(f"\nPerformance metrics:")
        print(f"  Peak memory: {perf_summary['memory']['peak_mb']:.1f}MB")
        print(f"  Memory growth: {perf_summary['memory']['growth_mb']:.1f}MB")
        print(f"  Peak CPU: {perf_summary['cpu']['peak_percent']:.1f}%")
        print(f"  Peak rate: {perf_summary['generation_rate']['peak_logs_per_sec']:.1f} logs/sec")
        
        # Verify output
        output_file = Path(output_path)
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"  Output file size: {file_size/1024:.1f}KB")
    
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all performance optimization demonstrations."""
    print("LOG GENERATOR PERFORMANCE OPTIMIZATION DEMO")
    print("=" * 50)
    
    try:
        demonstrate_performance_monitoring()
        demonstrate_batch_processing()
        demonstrate_memory_optimization()
        demonstrate_performance_profiling()
        demonstrate_optimized_generation()
        
        print("\n" + "=" * 50)
        print("All performance optimization demos completed successfully!")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()