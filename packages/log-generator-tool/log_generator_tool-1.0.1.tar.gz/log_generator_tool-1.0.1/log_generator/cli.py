"""
Command Line Interface for the Log Generator Tool.

This module provides a comprehensive CLI using Typer for managing log generation,
configuration, and monitoring with rich formatting and real-time updates.
"""

import json
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
import yaml
from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.status import Status
from rich.table import Table
from rich.text import Text

from .core.config import ConfigurationManager
from .core.engine import LogGeneratorCore
from .core.exceptions import ConfigurationError, GenerationError
from .core.factory import LogFactory
from .outputs.console_handler import ConsoleOutputHandler
from .outputs.file_handler import FileOutputHandler
from .outputs.json_handler import JSONOutputHandler
from .outputs.multi_file_handler import MultiFileOutputHandler
from .outputs.network_handler import NetworkOutputHandler

# Initialize Typer app and Rich console
app = typer.Typer(
    name="log-generator",
    help="Automatic log generation tool for testing and development",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()

# Global variables for monitoring
_engine: Optional[LogGeneratorCore] = None
_monitoring_active = False
_monitoring_thread: Optional[threading.Thread] = None


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    global _engine, _monitoring_active

    console.print(
        "\n[yellow]Received interrupt signal. Stopping log generation...[/yellow]"
    )

    if _engine and _engine.is_running():
        _engine.stop_generation()

    _monitoring_active = False

    console.print("[green]Log generation stopped successfully.[/green]")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@app.command("start")
def start_generation(
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to configuration file (YAML or JSON)"
    ),
    output_format: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: multi_file (default), file, console, network, json",
    ),
    output_path: Optional[str] = typer.Option(
        None, "--path", "-p", help="Output file path (for file output)"
    ),
    total_logs: Optional[int] = typer.Option(
        None, "--total", "-t", help="Total number of logs to generate (0 for unlimited)"
    ),
    interval: Optional[float] = typer.Option(
        None,
        "--interval",
        "-i",
        help="Generation interval in seconds (0.01 for high performance, 0.1 default)",
    ),
    random_interval: bool = typer.Option(
        False,
        "--random-interval/--fixed-interval",
        help="Use random interval (0 to interval) instead of fixed interval",
    ),
    log_types: Optional[List[str]] = typer.Option(
        None,
        "--types",
        help="Log types to enable (comma-separated or multiple --types options)",
    ),
    monitor: bool = typer.Option(
        True, "--monitor/--no-monitor", help="Enable real-time monitoring display"
    ),
    progress: bool = typer.Option(
        True,
        "--progress/--no-progress",
        help="Show progress bar for limited log generation",
    ),
    virtual_time: bool = typer.Option(
        True,
        "--virtual-time/--real-time",
        help="Use virtual time for maximum performance (default: virtual-time)",
    ),
    start_time: Optional[str] = typer.Option(
        None,
        "--start-time",
        help="Start time for log generation (format: YYYY-MM-DD HH:MM:SS or YYYY-MM-DD)",
    ),
):
    """
    Start log generation with specified configuration.

    By default, logs are generated with multi-file output where each log type
    is saved to a separate file (e.g., nginx_access_20241215.log, syslog_20241215.log).
    This provides better organization and easier log analysis.

    This command initializes the log generation engine, loads configuration,
    and starts generating logs according to the specified parameters.
    """
    global _engine, _monitoring_active

    try:
        # Initialize configuration manager
        config_manager = ConfigurationManager()

        # Load configuration
        if config:
            if not Path(config).exists():
                console.print(f"[red]Configuration file not found: {config}[/red]")
                raise typer.Exit(1)

            config_data = config_manager.load_config(config)
            console.print(f"[green]Configuration loaded from: {config}[/green]")
        else:
            # Use default configuration
            config_data = config_manager.DEFAULT_CONFIG.copy()
            console.print("[yellow]Using default configuration[/yellow]")

        # Override configuration with command line arguments
        if output_format:
            config_data["log_generator"]["global"]["output_format"] = output_format

        if output_path:
            config_data["log_generator"]["global"]["output_path"] = output_path

        if total_logs is not None:
            config_data["log_generator"]["global"]["total_logs"] = total_logs

        if interval is not None:
            config_data["log_generator"]["global"]["generation_interval"] = interval

        if random_interval:
            config_data["log_generator"]["global"]["random_interval"] = random_interval

        # Set virtual time option
        config_data["log_generator"]["global"]["virtual_time"] = virtual_time

        # Set start time if provided
        if start_time:
            try:
                from datetime import datetime

                # Try to parse the start time
                if len(start_time) == 10:  # YYYY-MM-DD format
                    parsed_time = datetime.strptime(start_time, "%Y-%m-%d")
                elif len(start_time) == 19:  # YYYY-MM-DD HH:MM:SS format
                    parsed_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                else:
                    raise ValueError("Invalid time format")

                config_data["log_generator"]["global"]["start_time"] = start_time
                console.print(f"[green]Start time set to: {parsed_time}[/green]")
            except ValueError as e:
                console.print(f"[red]Invalid start time format: {start_time}[/red]")
                console.print(
                    "[yellow]Use format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS[/yellow]"
                )
                raise typer.Exit(1)

        # Enable specific log types if specified
        if log_types:
            # Parse comma-separated log types
            parsed_log_types = []
            for log_type_item in log_types:
                # Split by comma and strip whitespace
                if "," in log_type_item:
                    parsed_log_types.extend(
                        [t.strip() for t in log_type_item.split(",")]
                    )
                else:
                    parsed_log_types.append(log_type_item.strip())

            # Remove empty strings
            parsed_log_types = [t for t in parsed_log_types if t]

            # Disable all log types first
            for log_type in config_data["log_generator"]["log_types"]:
                config_data["log_generator"]["log_types"][log_type]["enabled"] = False

            # Enable specified log types
            for log_type in parsed_log_types:
                if log_type in config_data["log_generator"]["log_types"]:
                    config_data["log_generator"]["log_types"][log_type][
                        "enabled"
                    ] = True
                else:
                    console.print(
                        f"[yellow]Warning: Unknown log type '{log_type}' ignored[/yellow]"
                    )

        # Validate configuration
        config_manager.validate_config(config_data)

        # Initialize engine
        _engine = LogGeneratorCore()
        _engine._config = config_data

        # Set up log factory
        factory = LogFactory()
        _engine.set_log_factory(factory)

        # Set up output handlers
        _setup_output_handlers(_engine, config_data)

        # Display configuration summary
        _display_config_summary(config_data)

        # Start generation
        console.print("\n[green]Starting log generation...[/green]")
        _engine.start_generation()

        if monitor:
            # Start monitoring with progress tracking
            _start_monitoring(_engine, show_progress=progress)
        else:
            # Simple status display
            console.print("[green]Log generation started successfully.[/green]")
            console.print("Press Ctrl+C to stop generation.")

            # Wait for completion or interruption
            try:
                while _engine.is_running():
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                if _engine.is_running():
                    _engine.stop_generation()

    except (ConfigurationError, GenerationError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command("stop")
def stop_generation():
    """
    Stop currently running log generation.

    This command gracefully stops any running log generation process.
    """
    global _engine, _monitoring_active

    if _engine is None:
        console.print("[yellow]No log generation engine initialized.[/yellow]")
        return

    if not _engine.is_running():
        console.print("[yellow]No log generation is currently running.[/yellow]")
        return

    console.print("[yellow]Stopping log generation...[/yellow]")
    _engine.stop_generation()
    _monitoring_active = False

    console.print("[green]Log generation stopped successfully.[/green]")


@app.command("status")
def show_status():
    """
    Show current generation status and statistics.

    This command displays detailed information about the current
    log generation process including statistics and configuration.
    """
    global _engine

    if _engine is None:
        console.print("[yellow]No log generation engine initialized.[/yellow]")
        return

    # Get statistics
    stats = _engine.get_statistics()
    is_running = _engine.is_running()

    # Create status table
    table = Table(title="Log Generation Status", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row(
        "Status", "[green]Running[/green]" if is_running else "[red]Stopped[/red]"
    )
    table.add_row("Total Logs Generated", str(stats.get("total_logs_generated", 0)))
    table.add_row("Generation Rate", f"{stats.get('generation_rate', 0):.2f} logs/sec")
    table.add_row("Errors", str(stats.get("error_count", 0)))

    if stats.get("start_time"):
        table.add_row("Start Time", str(stats["start_time"]))

    if stats.get("end_time"):
        table.add_row("End Time", str(stats["end_time"]))

    # Log type breakdown
    log_type_stats = stats.get("log_type_counts", {})
    if log_type_stats:
        table.add_row("", "")  # Separator
        for log_type, count in log_type_stats.items():
            table.add_row(f"  {log_type}", str(count))

    console.print(table)


@app.command("monitor")
def monitor_generation(
    refresh_rate: float = typer.Option(
        2.0, "--refresh", "-r", help="Refresh rate in seconds"
    ),
    show_logs: bool = typer.Option(
        False, "--show-logs", help="Show recent log entries in monitoring view"
    ),
):
    """
    Monitor currently running log generation with real-time updates.

    This command provides an interactive monitoring interface with
    real-time statistics, progress tracking, and log preview.
    """
    global _engine

    if _engine is None:
        console.print("[yellow]No log generation engine initialized.[/yellow]")
        console.print("Use 'log-generator start' to begin log generation.")
        return

    if not _engine.is_running():
        console.print("[yellow]No log generation is currently running.[/yellow]")
        console.print("Use 'log-generator start' to begin log generation.")
        return

    console.print("[green]Starting interactive monitoring...[/green]")
    console.print(
        "[dim]Press Ctrl+C to exit monitoring (generation will continue)[/dim]"
    )

    try:
        _interactive_monitoring(_engine, refresh_rate, show_logs)
    except KeyboardInterrupt:
        console.print(
            "\n[yellow]Monitoring stopped. Log generation continues in background.[/yellow]"
        )


@app.command("config")
def config_command(
    action: str = typer.Argument(..., help="Action: create, show, validate, or edit"),
    file_path: Optional[str] = typer.Option(
        None, "--file", "-f", help="Configuration file path"
    ),
    format_type: str = typer.Option(
        "yaml", "--format", help="Configuration format: yaml or json"
    ),
):
    """
    Manage configuration files.

    This command provides utilities for creating, viewing, validating,
    and editing configuration files.

    Actions:
    - create: Create a new configuration file with default values
    - show: Display current configuration
    - validate: Validate configuration file
    - edit: Open configuration file in default editor
    """
    config_manager = ConfigurationManager()

    if action == "create":
        if not file_path:
            file_path = f"log_generator_config.{format_type}"

        try:
            config_manager.save_config(config_manager.DEFAULT_CONFIG, file_path)
            console.print(f"[green]Configuration file created: {file_path}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to create configuration file: {e}[/red]")
            raise typer.Exit(1)

    elif action == "show":
        if file_path:
            try:
                config_data = config_manager.load_config(file_path)
            except Exception as e:
                console.print(f"[red]Failed to load configuration: {e}[/red]")
                raise typer.Exit(1)
        else:
            config_data = config_manager.DEFAULT_CONFIG

        # Display configuration
        if format_type == "json":
            config_str = json.dumps(config_data, indent=2)
            console.print(
                Panel(config_str, title="Configuration (JSON)", border_style="blue")
            )
        else:
            config_str = yaml.dump(config_data, default_flow_style=False, indent=2)
            console.print(
                Panel(config_str, title="Configuration (YAML)", border_style="blue")
            )

    elif action == "validate":
        if not file_path:
            console.print(
                "[red]Configuration file path is required for validation.[/red]"
            )
            raise typer.Exit(1)

        try:
            config_data = config_manager.load_config(file_path)
            config_manager.validate_config(config_data)
            console.print(f"[green]Configuration file is valid: {file_path}[/green]")
        except Exception as e:
            console.print(f"[red]Configuration validation failed: {e}[/red]")
            raise typer.Exit(1)

    elif action == "edit":
        if not file_path:
            console.print("[red]Configuration file path is required for editing.[/red]")
            raise typer.Exit(1)

        if not Path(file_path).exists():
            console.print(f"[red]Configuration file not found: {file_path}[/red]")
            raise typer.Exit(1)

        # Open in default editor
        import subprocess

        editor = os.environ.get("EDITOR", "nano")
        try:
            subprocess.run([editor, file_path])
        except Exception as e:
            console.print(f"[red]Failed to open editor: {e}[/red]")
            raise typer.Exit(1)

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: create, show, validate, edit")
        raise typer.Exit(1)


@app.command("pause")
def pause_generation():
    """
    Pause currently running log generation.

    This command temporarily pauses log generation without stopping it completely.
    Use 'resume' command to continue generation.
    """
    global _engine

    if _engine is None or not _engine.is_running():
        console.print("[yellow]No log generation is currently running.[/yellow]")
        return

    # Note: This would require implementing pause/resume in the engine
    console.print("[yellow]Pause functionality not yet implemented in engine.[/yellow]")
    console.print("[dim]Use 'log-generator stop' to stop generation completely.[/dim]")


@app.command("resume")
def resume_generation():
    """
    Resume paused log generation.

    This command resumes previously paused log generation.
    """
    global _engine

    console.print(
        "[yellow]Resume functionality not yet implemented in engine.[/yellow]"
    )
    console.print("[dim]Use 'log-generator start' to begin new generation.[/dim]")


@app.command("list-types")
def list_log_types():
    """
    List all available log generator types.

    This command displays all registered log generator types
    and their current status in the configuration.
    """
    try:
        # Create a factory to get available types
        factory = LogFactory()
        available_types = factory.get_available_types()

        if not available_types:
            console.print("[yellow]No log generator types are available.[/yellow]")
            return

        # Create table of available types
        table = Table(title="Available Log Generator Types", box=box.ROUNDED)
        table.add_column("Log Type", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")

        # Load current configuration to show status
        config_manager = ConfigurationManager()
        try:
            config = config_manager.DEFAULT_CONFIG
            log_types_config = config.get("log_generator", {}).get("log_types", {})
        except Exception:
            log_types_config = {}

        # Descriptions for known log types
        descriptions = {
            "nginx_access": "Nginx web server access logs",
            "nginx_error": "Nginx web server error logs",
            "apache_access": "Apache web server access logs",
            "apache_error": "Apache web server error logs",
            "syslog": "System log messages (RFC 3164/5424)",
            "fastapi": "FastAPI application logs",
            "django_request": "Django web framework request logs",
            "django_sql": "Django SQL query logs",
            "docker": "Docker container logs",
            "kubernetes_pod": "Kubernetes pod logs",
            "kubernetes_event": "Kubernetes event logs",
            "mysql_query": "MySQL database query logs",
            "mysql_error": "MySQL database error logs",
            "mysql_slow": "MySQL slow query logs",
            "postgresql": "PostgreSQL database logs",
            "postgresql_slow": "PostgreSQL slow query logs",
        }

        for log_type in sorted(available_types):
            description = descriptions.get(log_type, "Custom log generator")

            # Check if enabled in default config
            type_config = log_types_config.get(log_type, {})
            enabled = type_config.get("enabled", False)
            status = "[green]Enabled[/green]" if enabled else "[red]Disabled[/red]"

            table.add_row(log_type, description, status)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing log types: {e}[/red]")
        raise typer.Exit(1)


def _setup_output_handlers(engine: LogGeneratorCore, config: Dict[str, Any]) -> None:
    """
    Set up output handlers based on configuration.

    Args:
        engine: Log generator engine instance
        config: Configuration dictionary
    """
    global_config = config["log_generator"]["global"]
    output_format = global_config.get("output_format", "file")

    if output_format == "file":
        output_path = global_config.get("output_path", "./logs")

        # If output_path is a directory, add a default filename
        if Path(output_path).is_dir():
            output_path = Path(output_path) / "generated_logs.log"

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        handler = FileOutputHandler(
            file_path=output_path,
            rotation_size=global_config.get("rotation_size"),
            rotation_time=global_config.get("rotation_time"),
        )
        engine.add_output_handler(handler)

    elif output_format == "console":
        handler = ConsoleOutputHandler(colored=True)
        engine.add_output_handler(handler)

    elif output_format == "network":
        host = global_config.get("network_host", "localhost")
        port = global_config.get("network_port", 514)
        protocol = global_config.get("network_protocol", "tcp")

        handler = NetworkOutputHandler(host=host, port=port, protocol=protocol)
        engine.add_output_handler(handler)

    elif output_format == "json":
        output_path = global_config.get("output_path", "./logs/output.json")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        handler = JSONOutputHandler(file_path=output_path)
        engine.add_output_handler(handler)

    elif output_format == "multi_file":
        output_path = global_config.get("output_path", "./logs")
        multi_file_config = global_config.get("multi_file", {})

        # Ensure output directory exists
        Path(output_path).mkdir(parents=True, exist_ok=True)

        handler = MultiFileOutputHandler(
            base_path=output_path,
            file_pattern=multi_file_config.get("file_pattern", "{log_type}_{date}.log"),
            date_format=multi_file_config.get("date_format", "%Y%m%d"),
            rotation_size=global_config.get("rotation_size"),
            rotation_time=global_config.get("rotation_time"),
        )
        engine.add_output_handler(handler)


def _display_config_summary(config: Dict[str, Any]) -> None:
    """
    Display a summary of the current configuration.

    Args:
        config: Configuration dictionary
    """
    global_config = config["log_generator"]["global"]
    log_types_config = config["log_generator"]["log_types"]

    # Create configuration summary table
    table = Table(title="Configuration Summary", box=box.ROUNDED)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Output Format", global_config.get("output_format", "file"))
    table.add_row("Output Path", str(global_config.get("output_path", "./logs")))
    interval_text = f"{global_config.get('generation_interval', 1.0)}s"
    if global_config.get("random_interval", False):
        interval_text += " (random 0-interval)"
    table.add_row("Generation Interval", interval_text)
    table.add_row("Total Logs", str(global_config.get("total_logs", 10000)))

    # Enabled log types
    enabled_types = [
        log_type
        for log_type, config in log_types_config.items()
        if config.get("enabled", False)
    ]
    table.add_row("Enabled Log Types", ", ".join(enabled_types))

    console.print(table)


def _start_monitoring(engine: LogGeneratorCore, show_progress: bool = True) -> None:
    """
    Start real-time monitoring display.

    Args:
        engine: Log generator engine instance
        show_progress: Whether to show progress bar for limited generation
    """
    global _monitoring_active, _monitoring_thread

    _monitoring_active = True
    _monitoring_thread = threading.Thread(
        target=_monitoring_loop, args=(engine, show_progress), daemon=True
    )
    _monitoring_thread.start()

    try:
        # Wait for monitoring to finish
        _monitoring_thread.join()
    except KeyboardInterrupt:
        _monitoring_active = False


def _monitoring_loop(engine: LogGeneratorCore, show_progress: bool = True) -> None:
    """
    Real-time monitoring loop with rich display.

    Args:
        engine: Log generator engine instance
        show_progress: Whether to show progress bar
    """
    global _monitoring_active

    # Get total logs target for progress calculation
    config = getattr(engine, "_config", {})
    total_target = (
        config.get("log_generator", {}).get("global", {}).get("total_logs", 0)
    )

    with Live(console=console, refresh_per_second=2) as live:
        while _monitoring_active and engine.is_running():
            # Create monitoring layout
            layout = _create_monitoring_layout(engine, show_progress, total_target)
            live.update(layout)
            time.sleep(0.5)

        # Final update when stopped
        if not engine.is_running():
            layout = _create_monitoring_layout(engine, show_progress, total_target)
            live.update(layout)


def _interactive_monitoring(
    engine: LogGeneratorCore, refresh_rate: float, show_logs: bool
) -> None:
    """
    Interactive monitoring with enhanced features.

    Args:
        engine: Log generator engine instance
        refresh_rate: Refresh rate in seconds
        show_logs: Whether to show recent log entries
    """
    config = getattr(engine, "_config", {})
    total_target = (
        config.get("log_generator", {}).get("global", {}).get("total_logs", 0)
    )

    with Live(console=console, refresh_per_second=refresh_rate) as live:
        while engine.is_running():
            # Create enhanced monitoring layout
            layout = _create_enhanced_monitoring_layout(engine, total_target, show_logs)
            live.update(layout)
            time.sleep(1.0 / refresh_rate)

        # Final update when stopped
        layout = _create_enhanced_monitoring_layout(engine, total_target, show_logs)
        live.update(layout)


def _create_monitoring_layout(
    engine: LogGeneratorCore, show_progress: bool = True, total_target: int = 0
) -> Layout:
    """
    Create the monitoring layout with statistics and progress.

    Args:
        engine: Log generator engine instance
        show_progress: Whether to show progress bar
        total_target: Total target logs for progress calculation

    Returns:
        Rich Layout object
    """
    layout = Layout()

    # Get current statistics
    stats = engine.get_statistics()
    is_running = engine.is_running()

    # Status panel
    status_text = "[green]RUNNING[/green]" if is_running else "[red]STOPPED[/red]"
    status_panel = Panel(
        Align.center(status_text),
        title="Status",
        border_style="green" if is_running else "red",
    )

    # Progress panel (if applicable)
    progress_panel = None
    if show_progress and total_target > 0:
        current_logs = stats.get("total_logs_generated", 0)
        progress_percentage = min((current_logs / total_target) * 100, 100)

        progress_bar = f"[{'█' * int(progress_percentage // 5)}{'░' * (20 - int(progress_percentage // 5))}]"
        progress_text = (
            f"{progress_bar} {progress_percentage:.1f}% ({current_logs}/{total_target})"
        )

        progress_panel = Panel(
            Align.center(progress_text), title="Progress", border_style="cyan"
        )

    # Statistics table
    stats_table = Table(box=box.SIMPLE)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="white")

    stats_table.add_row("Total Logs", str(stats.get("total_logs_generated", 0)))
    stats_table.add_row("Rate", f"{stats.get('generation_rate', 0):.2f} logs/sec")
    stats_table.add_row("Errors", str(stats.get("error_count", 0)))

    if stats.get("start_time"):
        start_time = stats["start_time"]
        if isinstance(start_time, str):
            # If start_time is a string, try to parse it or use current time as fallback
            try:
                from datetime import datetime

                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                duration = time.time() - start_time.timestamp()
            except (ValueError, AttributeError):
                # Fallback: assume generation just started
                duration = 0
        else:
            # Assume it's already a datetime object
            duration = time.time() - start_time.timestamp()
        stats_table.add_row("Duration", f"{duration:.1f}s")

        # Estimate completion time if target is set
        if total_target > 0 and stats.get("generation_rate", 0) > 0:
            remaining_logs = total_target - stats.get("total_logs_generated", 0)
            if remaining_logs > 0:
                eta_seconds = remaining_logs / stats["generation_rate"]
                eta_text = f"{eta_seconds:.0f}s"
                stats_table.add_row("ETA", eta_text)

    stats_panel = Panel(stats_table, title="Statistics", border_style="blue")

    # Log type breakdown
    log_type_stats = stats.get("log_type_counts", {})
    if log_type_stats:
        log_types_table = Table(box=box.SIMPLE)
        log_types_table.add_column("Log Type", style="yellow")
        log_types_table.add_column("Count", style="white")
        log_types_table.add_column("Rate", style="green")

        total_logs = stats.get("total_logs_generated", 1)  # Avoid division by zero
        for log_type, count in log_type_stats.items():
            percentage = (count / total_logs) * 100 if total_logs > 0 else 0
            log_types_table.add_row(log_type, str(count), f"{percentage:.1f}%")

        log_types_panel = Panel(
            log_types_table, title="Log Types", border_style="yellow"
        )
    else:
        log_types_panel = Panel(
            "No data available", title="Log Types", border_style="yellow"
        )

    # Recent logs panel (실시간 로그 스트림)
    recent_logs_panel = _create_recent_logs_panel(engine)

    # File info panel (파일 정보)
    file_info_panel = _create_file_info_panel(engine)

    # Create row layouts properly
    stats_row = Layout()
    stats_row.split_row(Layout(stats_panel), Layout(log_types_panel))

    info_row = Layout()
    info_row.split_row(Layout(recent_logs_panel), Layout(file_info_panel))

    # Arrange layout
    if progress_panel:
        layout.split_column(
            Layout(status_panel, size=3),
            Layout(progress_panel, size=3),
            stats_row,
            info_row,
        )
    else:
        layout.split_column(Layout(status_panel, size=3), stats_row, info_row)

    return layout


def _create_recent_logs_panel(engine: LogGeneratorCore) -> Panel:
    """
    Create a panel showing recent log entries or multi-file information.

    Args:
        engine: Log generator engine instance

    Returns:
        Rich Panel with recent logs or file information
    """
    try:
        config = getattr(engine, "_config", {})
        global_config = config.get("log_generator", {}).get("global", {})
        output_format = global_config.get("output_format", "file")

        if output_format == "multi_file":
            return _create_multi_file_info_panel(engine)
        else:
            return _create_single_file_logs_panel(engine, global_config)

    except Exception as e:
        return Panel(
            f"[red]Error reading logs: {e}[/red]",
            title="Recent Logs",
            border_style="red",
            height=8,
        )


def _create_multi_file_info_panel(engine: LogGeneratorCore) -> Panel:
    """
    Create a panel showing multi-file information.

    Args:
        engine: LogGeneratorCore instance

    Returns:
        Rich Panel with multi-file information
    """
    try:
        # Get multi-file handler statistics
        multi_file_stats = None
        for handler in engine._output_handlers:
            if hasattr(handler, "get_statistics") and hasattr(handler, "_handlers"):
                multi_file_stats = handler.get_statistics()
                break

        if not multi_file_stats:
            return Panel(
                "[dim]No multi-file information available[/dim]",
                title="File Information",
                border_style="yellow",
                height=8,
            )

        # Create file information display
        file_info_lines = []
        for log_type, stats in multi_file_stats.items():
            file_name = Path(stats["file_path"]).name
            file_size_kb = stats["file_size"] / 1024 if stats["file_size"] > 0 else 0
            line_count = stats.get("line_count", 0)

            # File header
            file_info_lines.append(f"[bold cyan]{log_type}[/bold cyan]: {file_name}")
            file_info_lines.append(f"  📊 {line_count:,} lines, {file_size_kb:.1f}KB")

            # Recent logs for this file
            recent_logs = stats.get("recent_logs", [])
            if recent_logs:
                latest_log = recent_logs[-1]
                if len(latest_log) > 60:
                    latest_log = latest_log[:60] + "..."
                file_info_lines.append(f"  📝 {latest_log}")
            else:
                file_info_lines.append(f"  📝 [dim]No logs yet[/dim]")

            file_info_lines.append("")  # Empty line for spacing

        # Remove last empty line
        if file_info_lines and file_info_lines[-1] == "":
            file_info_lines.pop()

        content = (
            "\n".join(file_info_lines)
            if file_info_lines
            else "[dim]No files created yet[/dim]"
        )

        return Panel(
            content,
            title="Multi-File Information",
            border_style="cyan",
            height=12,  # Increased height to show more files
        )

    except Exception as e:
        return Panel(
            f"[red]Error reading multi-file info: {e}[/red]",
            title="File Information",
            border_style="red",
            height=8,
        )


def _create_single_file_logs_panel(
    engine: LogGeneratorCore, global_config: dict
) -> Panel:
    """
    Create a panel showing recent logs from a single file.

    Args:
        engine: LogGeneratorCore instance
        global_config: Global configuration dictionary

    Returns:
        Rich Panel with recent logs
    """
    try:
        # Get recent logs from engine (if available)
        recent_logs = getattr(engine, "_recent_logs", [])

        if not recent_logs:
            # Try to read from output file if available
            output_path = global_config.get("output_path", "./logs")

            if Path(output_path).is_dir():
                output_path = Path(output_path) / "generated_logs.log"

            if Path(output_path).exists():
                try:
                    with open(output_path, "r") as f:
                        lines = f.readlines()
                        recent_logs = [
                            line.strip() for line in lines[-5:]
                        ]  # Last 5 lines
                except Exception:
                    recent_logs = ["Unable to read log file"]
            else:
                recent_logs = ["No logs generated yet"]

        # Format recent logs
        if recent_logs:
            log_text = "\n".join(
                [
                    (
                        f"[dim]{log[:80]}...[/dim]"
                        if len(log) > 80
                        else f"[dim]{log}[/dim]"
                    )
                    for log in recent_logs[-5:]
                ]
            )
        else:
            log_text = "[dim]No recent logs available[/dim]"

        return Panel(log_text, title="Recent Logs", border_style="green", height=8)

    except Exception as e:
        return Panel(
            f"[red]Error reading logs: {e}[/red]",
            title="Recent Logs",
            border_style="red",
            height=8,
        )


def _create_file_info_panel(engine: LogGeneratorCore) -> Panel:
    """
    Create a panel showing file information and system stats.

    Args:
        engine: Log generator engine instance

    Returns:
        Rich Panel with file info
    """
    try:
        config = getattr(engine, "_config", {})
        global_config = config.get("log_generator", {}).get("global", {})
        output_format = global_config.get("output_format", "file")
        output_path = global_config.get("output_path", "./logs")

        info_table = Table(box=box.SIMPLE)
        info_table.add_column("Info", style="cyan")
        info_table.add_column("Value", style="white")

        # File information based on output format
        if output_format == "multi_file":
            # Multi-file statistics
            total_size = 0
            file_count = 0

            # Get multi-file handler statistics
            for handler in engine._output_handlers:
                if hasattr(handler, "get_statistics") and hasattr(handler, "_handlers"):
                    multi_file_stats = handler.get_statistics()
                    if multi_file_stats:
                        file_count = len(multi_file_stats)
                        total_size = sum(
                            stats["file_size"] for stats in multi_file_stats.values()
                        )
                    break

            # Format total size
            if total_size < 1024:
                size_str = f"{total_size} B"
            elif total_size < 1024 * 1024:
                size_str = f"{total_size / 1024:.1f} KB"
            else:
                size_str = f"{total_size / (1024 * 1024):.1f} MB"

            info_table.add_row("Total Size", size_str)
            info_table.add_row("File Count", str(file_count))
            info_table.add_row("Output Dir", str(output_path))
        else:
            # Single file statistics
            if Path(output_path).is_dir():
                output_path = Path(output_path) / "generated_logs.log"

            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"

                info_table.add_row("File Size", size_str)
                info_table.add_row("Output Path", str(output_path))
            else:
                info_table.add_row("File Size", "0 B")
                info_table.add_row("Output Path", str(output_path))

        # Memory usage (if available)
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            info_table.add_row("Memory Usage", f"{memory_mb:.1f} MB")
        except ImportError:
            info_table.add_row("Memory Usage", "N/A")

        # CPU usage (if available)
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=None)
            info_table.add_row("CPU Usage", f"{cpu_percent:.1f}%")
        except ImportError:
            info_table.add_row("CPU Usage", "N/A")

        return Panel(info_table, title="System Info", border_style="magenta", height=8)

    except Exception as e:
        return Panel(
            f"[red]Error getting file info: {e}[/red]",
            title="System Info",
            border_style="red",
            height=8,
        )


def _create_enhanced_monitoring_layout(
    engine: LogGeneratorCore, total_target: int, show_logs: bool
) -> Layout:
    """
    Create enhanced monitoring layout with additional features.

    Args:
        engine: Log generator engine instance
        total_target: Total target logs
        show_logs: Whether to show recent log entries

    Returns:
        Rich Layout object
    """
    layout = Layout()

    # Get current statistics
    stats = engine.get_statistics()
    is_running = engine.is_running()

    # Header with status and key metrics
    header_table = Table.grid(padding=1)
    header_table.add_column(style="green", justify="center")
    header_table.add_column(style="blue", justify="center")
    header_table.add_column(style="magenta", justify="center")
    header_table.add_column(style="yellow", justify="center")

    status_text = "RUNNING" if is_running else "STOPPED"
    total_logs = stats.get("total_logs_generated", 0)
    rate = stats.get("generation_rate", 0)
    errors = stats.get("error_count", 0)

    header_table.add_row(
        f"Status: {status_text}",
        f"Total: {total_logs}",
        f"Rate: {rate:.1f}/sec",
        f"Errors: {errors}",
    )

    header_panel = Panel(
        header_table, title="Log Generation Monitor", border_style="bright_blue"
    )

    # Progress bar for limited generation
    progress_content = ""
    if total_target > 0:
        progress_percentage = min((total_logs / total_target) * 100, 100)
        filled_blocks = int(progress_percentage // 2)  # 50 blocks total
        progress_bar = "█" * filled_blocks + "░" * (50 - filled_blocks)
        progress_content = f"[cyan]{progress_bar}[/cyan] {progress_percentage:.1f}% ({total_logs}/{total_target})"

        if stats.get("generation_rate", 0) > 0 and total_logs < total_target:
            remaining = total_target - total_logs
            eta = remaining / stats["generation_rate"]
            progress_content += f" | ETA: {eta:.0f}s"
    else:
        progress_content = (
            f"[cyan]Unlimited generation[/cyan] | Generated: {total_logs}"
        )

    progress_panel = Panel(progress_content, title="Progress", border_style="cyan")

    # Detailed statistics
    detailed_stats = Table(box=box.ROUNDED)
    detailed_stats.add_column("Metric", style="cyan", no_wrap=True)
    detailed_stats.add_column("Current", style="white")
    detailed_stats.add_column("Average", style="green")

    if stats.get("start_time"):
        start_time = stats["start_time"]
        if isinstance(start_time, str):
            # If start_time is a string, try to parse it or use current time as fallback
            try:
                from datetime import datetime

                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                duration = time.time() - start_time.timestamp()
            except (ValueError, AttributeError):
                # Fallback: assume generation just started
                duration = 1  # Avoid division by zero
        else:
            # Assume it's already a datetime object
            duration = time.time() - start_time.timestamp()
        avg_rate = total_logs / duration if duration > 0 else 0

        detailed_stats.add_row(
            "Generation Rate", f"{rate:.2f} logs/sec", f"{avg_rate:.2f} logs/sec"
        )
        detailed_stats.add_row("Runtime", f"{duration:.1f}s", "-")
        detailed_stats.add_row(
            "Error Rate",
            f"{errors}",
            f"{(errors / total_logs * 100):.2f}%" if total_logs > 0 else "0%",
        )

    stats_panel = Panel(
        detailed_stats, title="Detailed Statistics", border_style="blue"
    )

    # Log type distribution with visual bars
    log_type_stats = stats.get("log_type_counts", {})
    if log_type_stats:
        log_types_table = Table(box=box.ROUNDED)
        log_types_table.add_column("Log Type", style="yellow")
        log_types_table.add_column("Count", style="white", justify="right")
        log_types_table.add_column("Distribution", style="green")
        log_types_table.add_column("%", style="cyan", justify="right")

        max_count = max(log_type_stats.values()) if log_type_stats else 1

        for log_type, count in sorted(
            log_type_stats.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total_logs) * 100 if total_logs > 0 else 0
            bar_length = int((count / max_count) * 20) if max_count > 0 else 0
            bar = "█" * bar_length + "░" * (20 - bar_length)

            log_types_table.add_row(
                log_type, str(count), f"[green]{bar}[/green]", f"{percentage:.1f}%"
            )

        log_types_panel = Panel(
            log_types_table, title="Log Type Distribution", border_style="yellow"
        )
    else:
        log_types_panel = Panel(
            "No log type data available",
            title="Log Type Distribution",
            border_style="yellow",
        )

    # Recent logs panel (if enabled)
    if show_logs:
        # This would require implementing log capture in the engine
        # For now, show a placeholder
        recent_logs_content = "[dim]Recent log capture not implemented[/dim]"
        recent_logs_panel = Panel(
            recent_logs_content, title="Recent Logs", border_style="magenta"
        )

        # Arrange layout with logs
        layout.split_column(
            Layout(header_panel, size=5),
            Layout(progress_panel, size=3),
            Layout().split_row(Layout(stats_panel), Layout(log_types_panel)),
            Layout(recent_logs_panel, size=8),
        )
    else:
        # Arrange layout without logs
        layout.split_column(
            Layout(header_panel, size=5),
            Layout(progress_panel, size=3),
            Layout().split_row(Layout(stats_panel), Layout(log_types_panel)),
        )

    return layout


def main():
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
