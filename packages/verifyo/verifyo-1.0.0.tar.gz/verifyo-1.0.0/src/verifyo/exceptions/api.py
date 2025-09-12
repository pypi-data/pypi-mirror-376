"""General API exception for HTTP errors."""

from typing import Any, Dict, Optional

from .base import VerifyoException


class ApiException(VerifyoException):
    """Exception raised for general API errors."""

    def __init__(
        self,
        message: str,
        status_code: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize API exception.
        
        Args:
            message: Error message about the API error
            status_code: HTTP status code from the API
            context: Additional context about the error
        """
        super().__init__(message, context)
        self.status_code = status_code

    def __str__(self) -> str:
        """Return string representation with status code."""
        return f"{super().__str__()} (Status: {self.status_code})"