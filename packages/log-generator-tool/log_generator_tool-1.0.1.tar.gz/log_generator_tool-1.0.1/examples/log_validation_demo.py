#!/usr/bin/env python3
"""
Demonstration of log validation and analysis functionality.

This script shows how to use the comprehensive log validation and analysis
system to validate log formats, generate samples, analyze statistics,
and create quality reports.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from log_generator.core.log_validator import LogValidator
from log_generator.core.log_analyzer import LogAnalyzer
import json


def main():
    """Demonstrate log validation and analysis capabilities."""

    print("=== Log Validation and Analysis Demo ===\n")

    # Initialize validator and analyzer
    validator = LogValidator()
    analyzer = LogAnalyzer()

    # Sample log entries for demonstration
    sample_logs = {
        "nginx_access": [
            '192.168.1.100 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 1234 "http://example.com" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"',
            '192.168.1.101 - - [25/Dec/2023:10:00:01 +0000] "POST /api/login HTTP/1.1" 401 567 "-" "curl/7.68.0"',
            '192.168.1.102 - - [25/Dec/2023:10:00:02 +0000] "GET /favicon.ico HTTP/1.1" 404 0 "http://example.com" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"',
            '10.0.0.50 - - [25/Dec/2023:10:00:03 +0000] "GET /api/users HTTP/1.1" 500 2048 "-" "Python-requests/2.25.1"',
            "invalid log format without proper structure",
            '999.999.999.999 - - [25/Dec/2023:10:00:04 +0000] "GET /test HTTP/1.1" 700 1234',  # Invalid IP and status code
        ],
        "syslog": [
            "Dec 25 10:00:00 server01 kernel: Out of memory: Kill process 1234",
            "Dec 25 10:00:01 server01 sshd[5678]: Failed password for root from 192.168.1.100",
            "Dec 25 10:00:02 server02 httpd: Server started successfully",
            "Dec 25 10:00:03 server01 kernel: ERROR: Connection timeout",
            "invalid syslog entry",
        ],
    }

    # 1. Demonstrate individual log validation
    print("1. Individual Log Validation")
    print("-" * 40)

    for log_type, logs in sample_logs.items():
        print(f"\n{log_type.upper()} Logs:")
        for i, log_entry in enumerate(logs[:3], 1):  # Show first 3 logs
            result = validator.validate_log_entry(log_entry, log_type)
            status = "✓ VALID" if result.is_valid else "✗ INVALID"
            print(f"  {i}. {status} (Score: {result.quality_score:.1f})")
            print(f"     Log: {log_entry[:60]}{'...' if len(log_entry) > 60 else ''}")
            if result.errors:
                print(f"     Errors: {', '.join(result.errors)}")
            if result.warnings:
                print(f"     Warnings: {', '.join(result.warnings[:2])}")
            print()

    # 2. Demonstrate batch validation
    print("\n2. Batch Validation Statistics")
    print("-" * 40)

    for log_type, logs in sample_logs.items():
        results = validator.validate_log_batch(logs, log_type)
        valid_count = sum(1 for r in results if r.is_valid)
        avg_quality = sum(r.quality_score for r in results) / len(results)

        print(f"\n{log_type.upper()}:")
        print(f"  Total logs: {len(logs)}")
        print(f"  Valid logs: {valid_count}")
        print(f"  Success rate: {valid_count / len(logs) * 100:.1f}%")
        print(f"  Average quality score: {avg_quality:.1f}")

    # 3. Demonstrate log sampling
    print("\n\n3. Log Sampling Strategies")
    print("-" * 40)

    nginx_logs = sample_logs["nginx_access"]
    strategies = ["random", "systematic", "stratified", "quality_based"]

    for strategy in strategies:
        sample = analyzer.generate_samples(
            nginx_logs, "nginx_access", sample_size=3, strategy=strategy
        )
        print(f"\n{strategy.upper()} Sampling:")
        print(f"  Sample size: {sample.sample_size}")
        print(f"  Strategy: {sample.metadata['strategy']}")
        print(f"  Sampling ratio: {sample.metadata['sampling_ratio']:.2f}")
        print("  Sample logs:")
        for i, log in enumerate(sample.logs, 1):
            print(f"    {i}. {log[:50]}...")

    # 4. Demonstrate log analysis
    print("\n\n4. Log Analysis and Statistics")
    print("-" * 40)

    for log_type, logs in sample_logs.items():
        stats = analyzer.analyze_logs(logs, log_type)

        print(f"\n{log_type.upper()} Analysis:")
        print(f"  Total logs: {stats.total_logs}")
        print(f"  Average log length: {stats.average_log_length:.1f} characters")

        if stats.status_codes:
            print(f"  Status codes: {dict(list(stats.status_codes.items())[:3])}")

        if stats.ip_addresses:
            print(f"  Top IPs: {dict(list(stats.ip_addresses.items())[:3])}")

        if stats.log_levels:
            print(f"  Log levels: {stats.log_levels}")

        print(
            f"  Field completeness: {dict(list(stats.field_completeness.items())[:3])}"
        )

        if stats.quality_metrics:
            print(f"  Quality metrics:")
            for metric, value in stats.quality_metrics.items():
                print(f"    {metric}: {value:.3f}")

    # 5. Demonstrate quality report generation
    print("\n\n5. Quality Report Generation")
    print("-" * 40)

    for log_type, logs in sample_logs.items():
        report = analyzer.generate_quality_report(logs, log_type)

        print(f"\n{log_type.upper()} Quality Report:")
        print(f"  Overall Score: {report.overall_score:.1f}/100")
        print(f"  Logs Analyzed: {report.total_logs_analyzed}")

        # Show validation summary
        valid_logs = sum(1 for r in report.validation_results if r.is_valid)
        print(f"  Valid Logs: {valid_logs}/{len(report.validation_results)}")

        if report.recommendations:
            print(f"  Recommendations:")
            for rec in report.recommendations[:2]:
                print(f"    • {rec}")

        if report.issues_found:
            print(f"  Issues Found:")
            for issue in report.issues_found[:2]:
                print(f"    • {issue}")

    # 6. Demonstrate log set comparison
    print("\n\n6. Log Set Comparison")
    print("-" * 40)

    nginx_logs = sample_logs["nginx_access"]
    good_logs = [
        log for log in nginx_logs if "invalid" not in log and "999.999" not in log
    ]
    bad_logs = [log for log in nginx_logs if "invalid" in log or "999.999" in log]

    if good_logs and bad_logs:
        comparison = analyzer.compare_log_sets(good_logs, bad_logs, "nginx_access")

        print("Comparing Good vs Bad Logs:")
        print(f"  Good logs count: {comparison['set1_stats']['total_logs']}")
        print(f"  Bad logs count: {comparison['set2_stats']['total_logs']}")

        # Show quality differences
        good_quality = comparison["set1_stats"]["quality_metrics"][
            "average_quality_score"
        ]
        bad_quality = comparison["set2_stats"]["quality_metrics"][
            "average_quality_score"
        ]

        print(f"  Good logs avg quality: {good_quality:.1f}")
        print(f"  Bad logs avg quality: {bad_quality:.1f}")
        print(f"  Quality difference: {good_quality - bad_quality:.1f}")

    # 7. Demonstrate custom patterns and fields
    print("\n\n7. Custom Patterns and Fields")
    print("-" * 40)

    # Add custom pattern
    custom_pattern = r"^CUSTOM: (\d{4}-\d{2}-\d{2}) \[(\w+)\] (.+)$"
    validator.add_custom_pattern("custom_app", "main_pattern", custom_pattern)
    validator.add_required_fields("custom_app", ["timestamp", "level", "message"])

    custom_logs = [
        "CUSTOM: 2023-12-25 [INFO] Application started successfully",
        "CUSTOM: 2023-12-25 [ERROR] Database connection failed",
        "invalid custom log format",
    ]

    print("Custom Application Logs:")
    for i, log_entry in enumerate(custom_logs, 1):
        result = validator.validate_log_entry(log_entry, "custom_app")
        status = "✓ VALID" if result.is_valid else "✗ INVALID"
        print(f"  {i}. {status} (Score: {result.quality_score:.1f})")
        print(f"     {log_entry}")
        if result.pattern_matches:
            print(f"     Pattern match: {result.pattern_matches}")

    # 8. Show validation statistics
    print("\n\n8. Overall Validation Statistics")
    print("-" * 40)

    overall_stats = validator.get_validation_statistics()
    print(f"Total logs validated: {overall_stats['total_validated']}")
    print(f"Overall success rate: {overall_stats['success_rate']:.1%}")
    print(f"Average quality score: {overall_stats['average_quality_score']:.1f}")

    if overall_stats["validation_by_type"]:
        print("\nValidation by log type:")
        for log_type, type_stats in overall_stats["validation_by_type"].items():
            total = type_stats["valid"] + type_stats["invalid"]
            success_rate = type_stats["valid"] / total if total > 0 else 0
            print(f"  {log_type}: {success_rate:.1%} ({type_stats['valid']}/{total})")

    if overall_stats["common_errors"]:
        print(f"\nMost common errors:")
        for error, count in list(overall_stats["common_errors"].items())[:3]:
            print(f"  • {error}: {count} occurrences")

    print(f"\nQuality distribution:")
    for category, count in overall_stats["quality_distribution"].items():
        print(f"  {category}: {count} logs")

    print("\n=== Demo Complete ===")
    print("\nThis demonstration showed:")
    print("• Individual and batch log validation")
    print("• Multiple sampling strategies")
    print("• Comprehensive log analysis and statistics")
    print("• Quality report generation")
    print("• Log set comparison")
    print("• Custom pattern and field validation")
    print("• Overall validation statistics")


if __name__ == "__main__":
    main()
