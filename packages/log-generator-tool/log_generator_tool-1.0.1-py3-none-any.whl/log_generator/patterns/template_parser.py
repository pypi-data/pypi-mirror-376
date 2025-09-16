"""
Template parser for custom log patterns.
Supports dynamic field generation and template parsing.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .faker_integration import FakerDataGenerator


@dataclass
class FieldDefinition:
    """Definition of a template field"""

    name: str
    field_type: str
    options: Dict[str, Any]
    generator: Optional[Callable] = None


class TemplateParser:
    """
    Parses custom log templates and generates dynamic fields.

    Supports template syntax like:
    - {timestamp} - Current timestamp
    - {ip_address} - Random IP address
    - {status_code:200,404,500} - Random choice from options
    - {user_agent:file:user_agents.txt} - Random line from file
    """

    FIELD_PATTERN = re.compile(r"\{([^}]+)\}")

    def __init__(self, faker_locale: str = "en_US", faker_seed: Optional[int] = None):
        self.field_definitions: Dict[str, FieldDefinition] = {}
        self.built_in_generators = self._setup_builtin_generators()
        self.faker_generator = FakerDataGenerator(locale=faker_locale, seed=faker_seed)

        # Add Faker generators to built-in generators
        for field_type in self.faker_generator.get_available_generators():
            self.built_in_generators[field_type] = (
                lambda ft=field_type: self.faker_generator.generate(ft)
            )

    def _setup_builtin_generators(self) -> Dict[str, Callable]:
        """Setup built-in field generators"""
        return {
            "timestamp": lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "iso_timestamp": lambda: datetime.now().isoformat(),
            "epoch_timestamp": lambda: str(int(datetime.now().timestamp())),
            "random_int": lambda min_val=1, max_val=100: str(
                __import__("random").randint(int(min_val), int(max_val))
            ),
            "random_float": lambda min_val=0.0, max_val=1.0: str(
                round(__import__("random").uniform(float(min_val), float(max_val)), 3)
            ),
            "uuid": lambda: str(__import__("uuid").uuid4()),
            "counter": self._create_counter_generator(),
        }

    def _create_counter_generator(self) -> Callable:
        """Create a counter generator that increments each call"""
        counter = {"value": 0}

        def increment(start=1, step=1):
            if counter["value"] == 0:
                counter["value"] = int(start)
            else:
                counter["value"] += int(step)
            return str(counter["value"])

        return increment

    def parse_template(self, template: str) -> List[FieldDefinition]:
        """
        Parse a template string and extract field definitions.

        Args:
            template: Template string with field placeholders

        Returns:
            List of field definitions found in template
        """
        fields = []
        matches = self.FIELD_PATTERN.findall(template)

        for match in matches:
            field_def = self._parse_field_definition(match)
            fields.append(field_def)
            self.field_definitions[field_def.name] = field_def

        return fields

    def _parse_field_definition(self, field_spec: str) -> FieldDefinition:
        """
        Parse individual field specification.

        Examples:
        - 'timestamp' -> FieldDefinition(name='timestamp', field_type='timestamp', options={})
        - 'status_code:200,404,500' -> FieldDefinition(name='status_code', field_type='choice', options={'choices': ['200', '404', '500']})
        - 'response_time:min:0.1,max:5.0' -> FieldDefinition(name='response_time', field_type='response_time', options={'min': '0.1', 'max': '5.0'})
        """
        parts = field_spec.split(":", 1)
        field_name = parts[0].strip()

        if len(parts) == 1:
            # Simple field without options
            field_type = field_name
            options = {}
        else:
            # Field with options
            options_str = parts[1]

            if options_str.startswith("file:"):
                # File-based field: user_agent:file:user_agents.txt
                field_type = "file"
                options = {"file_path": options_str[5:]}  # Remove 'file:' prefix
            elif ":" in options_str:
                # Key-value options: response_time:min:0.1,max:5.0 or counter:start:100,step:5
                field_type = field_name
                options = {}
                for option in options_str.split(","):
                    if ":" in option:
                        key, value = option.split(":", 1)
                        options[key.strip()] = value.strip()
                    else:
                        options[option.strip()] = True
            elif "," in options_str:
                # Choice field: status_code:200,404,500
                field_type = "choice"
                options = {
                    "choices": [choice.strip() for choice in options_str.split(",")]
                }
            else:
                # Single option
                field_type = field_name
                options = {"value": options_str}

        # Set up generator
        generator = self._create_field_generator(field_type, options)

        return FieldDefinition(
            name=field_name, field_type=field_type, options=options, generator=generator
        )

    def _create_field_generator(
        self, field_type: str, options: Dict[str, Any]
    ) -> Callable:
        """Create a generator function for the field"""
        if field_type == "choice":
            choices = options.get("choices", [])
            return lambda: __import__("random").choice(choices) if choices else ""

        elif field_type == "file":
            file_path = options.get("file_path", "")
            lines = self._load_file_lines(file_path)
            return lambda: __import__("random").choice(lines) if lines else ""

        elif field_type in self.built_in_generators:
            generator = self.built_in_generators[field_type]
            # Pass options as keyword arguments if generator supports them
            if options and "value" not in options:
                try:
                    return lambda: generator(**options)
                except TypeError:
                    # Generator doesn't accept these parameters, call without them
                    return generator
            else:
                return generator

        else:
            # Unknown field type, return empty string
            return lambda: ""

    def _load_file_lines(self, file_path: str) -> List[str]:
        """Load lines from a file for file-based generators"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except (FileNotFoundError, IOError):
            return []

    def generate_log(
        self, template: str, custom_values: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate a log entry from template.

        Args:
            template: Template string with field placeholders
            custom_values: Optional custom values to override generated ones

        Returns:
            Generated log string with fields replaced
        """
        custom_values = custom_values or {}
        result = template

        # Find all field placeholders
        matches = self.FIELD_PATTERN.finditer(template)

        for match in matches:
            field_spec = match.group(1)
            placeholder = match.group(0)
            field_name = field_spec.split(":")[0]  # Get field name without options

            # Parse field if not already parsed
            field_key = (
                f"{field_name}_{field_spec}"  # Use unique key for different field specs
            )
            if field_key not in self.field_definitions:
                field_def = self._parse_field_definition(field_spec)
                self.field_definitions[field_key] = field_def
            else:
                field_def = self.field_definitions[field_key]

            # Generate value
            if field_name in custom_values:
                value = custom_values[field_name]
            elif field_def.generator:
                try:
                    value = field_def.generator()
                except Exception:
                    value = ""
            else:
                value = ""

            # Replace placeholder with generated value
            result = result.replace(placeholder, str(value))

        return result

    def validate_template(self, template: str) -> Dict[str, Any]:
        """
        Validate a template and return validation results.

        Args:
            template: Template string to validate

        Returns:
            Dictionary with validation results
        """
        result = {"valid": True, "errors": [], "warnings": [], "fields": []}

        try:
            fields = self.parse_template(template)
            result["fields"] = [
                {"name": field.name, "type": field.field_type, "options": field.options}
                for field in fields
            ]

            # Check for unknown field types
            for field in fields:
                if (
                    field.field_type not in self.built_in_generators
                    and field.field_type not in ["choice", "file"]
                ):
                    result["warnings"].append(f"Unknown field type: {field.field_type}")

            # Try to generate a sample log to test generators
            try:
                sample = self.generate_log(template)
                if not sample or sample == template:
                    result["warnings"].append(
                        "Template generated empty or unchanged result"
                    )
            except Exception as e:
                result["errors"].append(f"Error generating sample log: {str(e)}")
                result["valid"] = False

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Template parsing error: {str(e)}")

        return result

    def get_available_field_types(self) -> List[str]:
        """Get list of available field types"""
        return list(self.built_in_generators.keys()) + ["choice", "file"]

    def add_custom_generator(self, field_type: str, generator: Callable) -> None:
        """Add a custom field generator"""
        self.built_in_generators[field_type] = generator
