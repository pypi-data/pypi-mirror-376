"""
Exception classes for the log generator system.
"""


class LogGeneratorError(Exception):
    """
    Base exception class for all log generator related errors.

    This serves as the parent class for all custom exceptions in the system,
    making it easier to catch and handle log generator specific errors.
    """

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(LogGeneratorError):
    """
    Exception raised for configuration related errors.

    This includes invalid configuration files, missing required fields,
    or invalid configuration values.
    """

    pass


class GenerationError(LogGeneratorError):
    """
    Exception raised during log generation process.

    This includes errors in log pattern generation, data formatting,
    or any issues during the actual log creation process.
    """

    pass


class OutputError(LogGeneratorError):
    """
    Exception raised during output handling.

    This includes file write errors, network connection failures,
    or any issues related to outputting generated logs.
    """

    pass


class ValidationError(LogGeneratorError):
    """
    Exception raised during log validation.

    This includes pattern matching failures, format validation errors,
    or any issues related to verifying log correctness.
    """

    pass


class FactoryError(LogGeneratorError):
    """
    Exception raised by the log factory.

    This includes errors in generator registration, unknown log types,
    or factory initialization issues.
    """

    pass


class PatternError(LogGeneratorError):
    """
    Exception raised for pattern related errors.

    This includes invalid regex patterns, pattern compilation errors,
    or pattern matching failures.
    """

    pass
