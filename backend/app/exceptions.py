class Gap2MaterialError(Exception):
    """Base application exception."""


class ConfigurationError(Gap2MaterialError):
    """Raised when a required configured capability is missing."""


class DependencyUnavailableError(Gap2MaterialError):
    """Raised when an optional scientific dependency is unavailable."""


class NotFoundError(Gap2MaterialError):
    """Raised when an entity cannot be found."""


class ValidationFailure(Gap2MaterialError):
    """Raised when scientific output fails schema or evidence validation."""
