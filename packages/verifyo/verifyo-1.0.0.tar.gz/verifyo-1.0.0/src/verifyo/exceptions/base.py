"""Base exception class for all Verifyo SDK exceptions."""

from typing import Any, Dict, Optional


class VerifyoException(Exception):
    """Base exception class for all Verifyo SDK exceptions."""

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message describing what went wrong
            context: Additional context about the exception
        """
        super().__init__(message)
        self.context = context or {}

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return super().__str__()

    def __repr__(self) -> str:
        """Return detailed representation of the exception."""
        return f"{self.__class__.__name__}('{self}', context={self.context})"