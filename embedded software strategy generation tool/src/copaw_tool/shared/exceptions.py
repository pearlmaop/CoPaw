class CoPawToolError(Exception):
    """Base exception for CoPaw Tool."""


class ExtractionError(CoPawToolError):
    """Raised when document extraction fails."""


class IRBuildError(CoPawToolError):
    """Raised when strategy IR building fails."""


class PseudocodeRenderError(CoPawToolError):
    """Raised when pseudocode rendering fails."""


class ConfigurationError(CoPawToolError):
    """Raised when configuration is invalid."""
