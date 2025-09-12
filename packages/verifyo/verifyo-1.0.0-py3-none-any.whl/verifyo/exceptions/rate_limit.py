"""Rate limiting exception for API quota exceeded."""

from typing import Any, Dict, Optional

from .base import VerifyoException


class RateLimitException(VerifyoException):
    """Exception raised when API rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str,
        limit: int,
        used: int,
        remaining: int,
        tier: str,
        resets_at: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize rate limit exception.
        
        Args:
            message: Error message about rate limiting
            limit: Total API limit for the period
            used: Number of requests used
            remaining: Number of requests remaining
            tier: User's tier (free, pro, etc.)
            resets_at: When the rate limit resets (ISO 8601)
            context: Additional context about the error
        """
        super().__init__(message, context)
        self.status_code = 429
        self.limit = limit
        self.used = used
        self.remaining = remaining
        self.tier = tier
        self.resets_at = resets_at

    def __str__(self) -> str:
        """Return detailed string representation."""
        return f"{super().__str__()} (Usage: {self.used}/{self.limit}, Tier: {self.tier})"