"""
Performance optimization utilities for the log generator system.

This module provides tools for monitoring, profiling, and optimizing
the performance of log generation operations.
"""

import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import psutil


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    timestamp: float
    logs_generated: int = 0
    generation_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    thread_count: int = 0
    queue_size: int = 0
    error_count: int = 0


class PerformanceMonitor:
    """Monitor and track performance metrics during log generation."""

    def __init__(self, max_history: int = 1000):
        """
        Initialize performance monitor.

        Args:
            max_history: Maximum number of metrics to keep in history
        """
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.process = psutil.Process()

        # Callbacks for performance events
        self.callbacks: List[Callable[[PerformanceMetrics], None]] = []

    def add_callback(self, callback: Callable[[PerformanceMetrics], None]) -> None:
        """Add a callback to be called when metrics are collected."""
        self.callbacks.append(callback)

    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        Start performance monitoring.

        Args:
            interval: Monitoring interval in seconds
        """
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,), daemon=True
        )
        self.monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def record_metrics(
        self,
        logs_generated: int,
        generation_rate: float,
        error_count: int = 0,
        queue_size: int = 0,
    ) -> None:
        """
        Record performance metrics manually.

        Args:
            logs_generated: Total logs generated
            generation_rate: Current generation rate
            error_count: Number of errors
            queue_size: Current queue size
        """
        try:
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            thread_count = self.process.num_threads()

            metrics = PerformanceMetrics(
                timestamp=time.time(),
                logs_generated=logs_generated,
                generation_rate=generation_rate,
                memory_usage_mb=memory_info.rss / 1024 / 1024,
                cpu_percent=cpu_percent,
                thread_count=thread_count,
                queue_size=queue_size,
                error_count=error_count,
            )

            self.metrics_history.append(metrics)

            # Call registered callbacks
            for callback in self.callbacks:
                try:
                    callback(metrics)
                except Exception:
                    pass  # Ignore callback errors

        except Exception:
            pass  # Ignore monitoring errors

    def _monitor_loop(self, interval: float) -> None:
        """Internal monitoring loop."""
        while self.is_monitoring:
            self.record_metrics(0, 0.0)  # Record system metrics only
            time.sleep(interval)

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent performance metrics."""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_history(self) -> List[PerformanceMetrics]:
        """Get all recorded performance metrics."""
        return list(self.metrics_history)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        if not self.metrics_history:
            return {}

        metrics_list = list(self.metrics_history)

        # Calculate averages and peaks
        avg_memory = sum(m.memory_usage_mb for m in metrics_list) / len(metrics_list)
        peak_memory = max(m.memory_usage_mb for m in metrics_list)
        avg_cpu = sum(m.cpu_percent for m in metrics_list) / len(metrics_list)
        peak_cpu = max(m.cpu_percent for m in metrics_list)

        # Calculate rates
        rates = [m.generation_rate for m in metrics_list if m.generation_rate > 0]
        avg_rate = sum(rates) / len(rates) if rates else 0
        peak_rate = max(rates) if rates else 0

        # Memory growth
        memory_growth = 0
        if len(metrics_list) > 1:
            memory_growth = (
                metrics_list[-1].memory_usage_mb - metrics_list[0].memory_usage_mb
            )

        return {
            "monitoring_duration": metrics_list[-1].timestamp
            - metrics_list[0].timestamp,
            "total_measurements": len(metrics_list),
            "memory": {
                "average_mb": avg_memory,
                "peak_mb": peak_memory,
                "growth_mb": memory_growth,
            },
            "cpu": {"average_percent": avg_cpu, "peak_percent": peak_cpu},
            "generation_rate": {
                "average_logs_per_sec": avg_rate,
                "peak_logs_per_sec": peak_rate,
            },
            "latest_metrics": metrics_list[-1],
        }


class BatchProcessor:
    """Batch processor for optimizing output operations."""

    def __init__(self, batch_size: int = 100, flush_interval: float = 1.0):
        """
        Initialize batch processor.

        Args:
            batch_size: Number of items to batch before processing
            flush_interval: Maximum time to wait before flushing batch
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch: List[str] = []
        self.last_flush = time.time()
        self.lock = threading.Lock()
        self.processors: List[Callable[[List[str]], None]] = []

    def add_processor(self, processor: Callable[[List[str]], None]) -> None:
        """Add a batch processor function."""
        self.processors.append(processor)

    def add_item(self, item: str) -> None:
        """
        Add an item to the batch.

        Args:
            item: Item to add to batch
        """
        with self.lock:
            self.batch.append(item)

            # Check if we should flush
            should_flush = (
                len(self.batch) >= self.batch_size
                or time.time() - self.last_flush >= self.flush_interval
            )

            if should_flush:
                self._flush_batch()

    def flush(self) -> None:
        """Force flush the current batch."""
        with self.lock:
            self._flush_batch()

    def _flush_batch(self) -> None:
        """Internal method to flush the batch."""
        if not self.batch:
            return

        batch_to_process = self.batch.copy()
        self.batch.clear()
        self.last_flush = time.time()

        # Process batch with all registered processors
        for processor in self.processors:
            try:
                processor(batch_to_process)
            except Exception:
                pass  # Ignore processor errors


class ThreadPoolOptimizer:
    """Optimize thread pool usage for log generation."""

    def __init__(self, max_workers: int | None = None):
        """
        Initialize thread pool optimizer.

        Args:
            max_workers: Maximum number of worker threads
        """
        if max_workers is None:
            max_workers = min(32, (psutil.cpu_count() or 1) + 4)

        self.max_workers = max_workers
        self.work_queue: queue.Queue = queue.Queue()
        self.workers: List[threading.Thread] = []
        self.is_running = False

    def start(self) -> None:
        """Start the thread pool."""
        if self.is_running:
            return

        self.is_running = True

        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop, name=f"LogGenWorker-{i}", daemon=True
            )
            worker.start()
            self.workers.append(worker)

    def stop(self) -> None:
        """Stop the thread pool."""
        self.is_running = False

        # Add stop signals for all workers
        for _ in self.workers:
            self.work_queue.put(None)

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=1.0)

        self.workers.clear()

    def submit_work(self, func: Callable, *args, **kwargs) -> None:
        """
        Submit work to the thread pool.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        if not self.is_running:
            self.start()

        self.work_queue.put((func, args, kwargs))

    def _worker_loop(self) -> None:
        """Worker thread loop."""
        while self.is_running:
            try:
                work_item = self.work_queue.get(timeout=1.0)

                if work_item is None:  # Stop signal
                    break

                func, args, kwargs = work_item
                func(*args, **kwargs)

            except queue.Empty:
                continue
            except Exception:
                pass  # Ignore work execution errors


class MemoryOptimizer:
    """Optimize memory usage during log generation."""

    def __init__(self, gc_threshold: float = 100.0, gc_interval: float = 30.0):
        """
        Initialize memory optimizer.

        Args:
            gc_threshold: Memory threshold in MB to trigger garbage collection
            gc_interval: Minimum interval between garbage collections
        """
        self.gc_threshold = gc_threshold
        self.gc_interval = gc_interval
        self.last_gc = time.time()
        self.process = psutil.Process()
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024

    def check_memory(self) -> bool:
        """
        Check memory usage and perform optimization if needed.

        Returns:
            True if garbage collection was performed
        """
        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_growth = current_memory - self.baseline_memory
        time_since_gc = time.time() - self.last_gc

        should_gc = (
            memory_growth > self.gc_threshold and time_since_gc > self.gc_interval
        )

        if should_gc:
            import gc

            gc.collect()
            self.last_gc = time.time()
            return True

        return False

    def get_memory_stats(self) -> Dict[str, float]:
        """Get current memory statistics."""
        current_memory = self.process.memory_info().rss / 1024 / 1024

        return {
            "current_mb": current_memory,
            "baseline_mb": self.baseline_memory,
            "growth_mb": current_memory - self.baseline_memory,
            "percent": self.process.memory_percent(),
        }


class PerformanceProfiler:
    """Profile performance of specific operations."""

    def __init__(self):
        """Initialize performance profiler."""
        self.profiles: Dict[str, List[float]] = {}
        self.active_profiles: Dict[str, float] = {}

    def start_profile(self, name: str) -> None:
        """Start profiling an operation."""
        self.active_profiles[name] = time.time()

    def end_profile(self, name: str) -> float:
        """
        End profiling an operation.

        Args:
            name: Profile name

        Returns:
            Duration of the operation
        """
        if name not in self.active_profiles:
            return 0.0

        duration = time.time() - self.active_profiles[name]
        del self.active_profiles[name]

        if name not in self.profiles:
            self.profiles[name] = []

        self.profiles[name].append(duration)
        return duration

    def get_profile_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a specific profile."""
        if name not in self.profiles or not self.profiles[name]:
            return {}

        durations = self.profiles[name]

        return {
            "count": len(durations),
            "total": sum(durations),
            "average": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
        }

    def get_all_profiles(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all profiles."""
        return {name: self.get_profile_stats(name) for name in self.profiles}

    def profile(self, name: str):
        """Context manager for profiling operations."""
        return ProfileContext(self, name)


class ProfileContext:
    """Context manager for profiling operations."""

    def __init__(self, profiler: PerformanceProfiler, name: str):
        """Initialize profile context."""
        self.profiler = profiler
        self.name = name

    def __enter__(self):
        """Enter profile context."""
        self.profiler.start_profile(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit profile context."""
        self.profiler.end_profile(self.name)
