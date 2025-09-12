"""Rate limiting information from API response headers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitInfo:
    """Rate limiting information from API response headers."""

    limit: int
    used: int
    remaining: int
    tier: str

    @property
    def is_near_limit(self) -> bool:
        """Check if approaching rate limit (within 10% of limit)."""
        return self.remaining <= (self.limit * 0.1)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "limit": self.limit,
            "used": self.used, 
            "remaining": self.remaining,
            "tier": self.tier,
        }