"""Authentication exception for invalid API keys."""

from typing import Any, Dict, Optional

from .base import VerifyoException


class AuthenticationException(VerifyoException):
    """Exception raised when API authentication fails (401)."""

    def __init__(
        self,
        message: str = "Invalid API key or authentication failed",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize authentication exception.
        
        Args:
            message: Error message about authentication failure
            context: Additional context about the error
        """
        super().__init__(message, context)
        self.status_code = 401