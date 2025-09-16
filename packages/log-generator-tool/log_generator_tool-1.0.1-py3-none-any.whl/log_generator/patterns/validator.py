"""
Pattern validation and testing utilities.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from .pattern_manager import LogPattern
from .template_parser import TemplateParser


class PatternValidator:
    """
    Validates log patterns and provides testing functionality.
    """

    def __init__(self):
        self.parser = TemplateParser()

    def validate_pattern_syntax(self, template: str) -> Dict[str, Any]:
        """
        Validate pattern template syntax.

        Args:
            template: Template string to validate

        Returns:
            Validation results with errors, warnings, and field info
        """
        return self.parser.validate_template(template)

    def test_pattern_generation(self, template: str, count: int = 10) -> Dict[str, Any]:
        """
        Test pattern generation by creating multiple samples.

        Args:
            template: Template to test
            count: Number of samples to generate

        Returns:
            Test results with samples and statistics
        """
        results = {
            "success": True,
            "samples": [],
            "errors": [],
            "statistics": {
                "total_generated": 0,
                "unique_outputs": 0,
                "field_variations": {},
            },
        }

        generated_outputs = set()
        field_values = {}

        for i in range(count):
            try:
                sample = self.parser.generate_log(template)
                results["samples"].append(sample)
                generated_outputs.add(sample)
                results["statistics"]["total_generated"] += 1

                # Extract field values for variation analysis
                self._analyze_field_variations(template, sample, field_values)

            except Exception as e:
                results["errors"].append(f"Generation {i+1}: {str(e)}")
                results["success"] = False

        results["statistics"]["unique_outputs"] = len(generated_outputs)
        results["statistics"]["field_variations"] = {
            field: len(values) for field, values in field_values.items()
        }

        return results

    def _analyze_field_variations(
        self, template: str, generated: str, field_values: Dict[str, set]
    ) -> None:
        """Analyze field variations in generated output"""
        # This is a simplified analysis - in a real implementation,
        # we'd need to reverse-engineer the field values from the output
        # For now, we'll just track that analysis was attempted
        pass

    def validate_regex_pattern(
        self, pattern: str, test_strings: List[str]
    ) -> Dict[str, Any]:
        """
        Validate a regex pattern against test strings.

        Args:
            pattern: Regex pattern to test
            test_strings: List of strings to test against

        Returns:
            Validation results
        """
        results = {"valid_regex": True, "matches": [], "non_matches": [], "errors": []}

        try:
            compiled_pattern = re.compile(pattern)

            for test_string in test_strings:
                try:
                    match = compiled_pattern.search(test_string)
                    if match:
                        results["matches"].append(
                            {
                                "string": test_string,
                                "match": match.group(),
                                "groups": match.groups() if match.groups() else [],
                            }
                        )
                    else:
                        results["non_matches"].append(test_string)
                except Exception as e:
                    results["errors"].append(
                        f"Error matching '{test_string}': {str(e)}"
                    )

        except re.error as e:
            results["valid_regex"] = False
            results["errors"].append(f"Invalid regex pattern: {str(e)}")

        return results

    def compare_patterns(
        self, pattern1: str, pattern2: str, sample_count: int = 20
    ) -> Dict[str, Any]:
        """
        Compare two patterns by generating samples and analyzing differences.

        Args:
            pattern1: First pattern template
            pattern2: Second pattern template
            sample_count: Number of samples to generate for comparison

        Returns:
            Comparison results
        """
        results = {
            "pattern1_samples": [],
            "pattern2_samples": [],
            "similarities": [],
            "differences": [],
            "statistics": {
                "pattern1_unique": 0,
                "pattern2_unique": 0,
                "common_structure": False,
            },
        }

        # Generate samples for both patterns
        for i in range(sample_count):
            try:
                sample1 = self.parser.generate_log(pattern1)
                results["pattern1_samples"].append(sample1)
            except Exception as e:
                results["pattern1_samples"].append(f"Error: {e}")

            try:
                sample2 = self.parser.generate_log(pattern2)
                results["pattern2_samples"].append(sample2)
            except Exception as e:
                results["pattern2_samples"].append(f"Error: {e}")

        # Analyze uniqueness
        results["statistics"]["pattern1_unique"] = len(set(results["pattern1_samples"]))
        results["statistics"]["pattern2_unique"] = len(set(results["pattern2_samples"]))

        # Basic structure comparison
        fields1 = set(self.parser.FIELD_PATTERN.findall(pattern1))
        fields2 = set(self.parser.FIELD_PATTERN.findall(pattern2))

        common_fields = fields1.intersection(fields2)
        unique_fields1 = fields1 - fields2
        unique_fields2 = fields2 - fields1

        if common_fields:
            results["similarities"].append(f"Common fields: {', '.join(common_fields)}")

        if unique_fields1:
            results["differences"].append(
                f"Pattern 1 unique fields: {', '.join(unique_fields1)}"
            )

        if unique_fields2:
            results["differences"].append(
                f"Pattern 2 unique fields: {', '.join(unique_fields2)}"
            )

        results["statistics"]["common_structure"] = len(common_fields) > 0

        return results

    def benchmark_pattern_performance(
        self, template: str, iterations: int = 1000
    ) -> Dict[str, Any]:
        """
        Benchmark pattern generation performance.

        Args:
            template: Template to benchmark
            iterations: Number of iterations to run

        Returns:
            Performance metrics
        """
        import time

        results = {
            "iterations": iterations,
            "total_time": 0,
            "average_time": 0,
            "min_time": float("inf"),
            "max_time": 0,
            "errors": 0,
            "success_rate": 0,
        }

        successful_iterations = 0
        times = []

        for i in range(iterations):
            start_time = time.perf_counter()

            try:
                self.parser.generate_log(template)
                end_time = time.perf_counter()

                iteration_time = end_time - start_time
                times.append(iteration_time)

                results["min_time"] = min(results["min_time"], iteration_time)
                results["max_time"] = max(results["max_time"], iteration_time)

                successful_iterations += 1

            except Exception:
                results["errors"] += 1

        if times:
            results["total_time"] = sum(times)
            results["average_time"] = results["total_time"] / len(times)
            results["success_rate"] = successful_iterations / iterations

        return results

    def suggest_pattern_improvements(self, template: str) -> List[str]:
        """
        Suggest improvements for a pattern template.

        Args:
            template: Template to analyze

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Check for common issues
        validation = self.parser.validate_template(template)

        if validation["warnings"]:
            suggestions.extend(
                [f"Warning: {warning}" for warning in validation["warnings"]]
            )

        # Check for field diversity
        fields = self.parser.FIELD_PATTERN.findall(template)
        if len(set(fields)) < len(fields):
            suggestions.append(
                "Consider using different field names to avoid confusion"
            )

        # Check for timestamp fields
        has_timestamp = any("timestamp" in field for field in fields)
        if not has_timestamp:
            suggestions.append(
                "Consider adding a timestamp field for better log correlation"
            )

        # Check for static content
        static_content = re.sub(self.parser.FIELD_PATTERN, "", template).strip()
        if len(static_content) < 10:
            suggestions.append(
                "Consider adding more static content for better log structure"
            )

        # Check for field complexity
        simple_fields = [field for field in fields if ":" not in field]
        if len(simple_fields) == len(fields):
            suggestions.append(
                "Consider using field options (e.g., {status_code:200,404,500}) for more realistic data"
            )

        return suggestions
