"""Network exception for connectivity issues."""

from typing import Any, Dict, Optional

from .base import VerifyoException


class NetworkException(VerifyoException):
    """Exception raised for network-related errors (timeouts, DNS issues, etc.)."""

    def __init__(
        self,
        message: str = "Network error occurred",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize network exception.
        
        Args:
            message: Error message about the network issue
            context: Additional context about the error (e.g., original exception)
        """
        super().__init__(message, context)