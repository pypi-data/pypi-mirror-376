"""Main response wrapper for KYC verification check."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .rate_limit_info import RateLimitInfo
from .verification_result import VerificationResult


@dataclass(frozen=True)
class CheckResponse:
    """Main response wrapper for KYC verification check."""

    results: List[VerificationResult]
    rate_limit_info: Optional[RateLimitInfo] = None

    @classmethod
    def from_dict(
        cls, 
        data: Dict[str, Any], 
        rate_limit_info: Optional[RateLimitInfo] = None
    ) -> "CheckResponse":
        """Create CheckResponse from API response data."""
        results = []
        
        # Parse results array
        if "results" in data and isinstance(data["results"], list):
            results = [
                VerificationResult.from_dict(result_data) 
                for result_data in data["results"]
            ]

        return cls(results=results, rate_limit_info=rate_limit_info)

    @property
    def has_results(self) -> bool:
        """Check if any verification results were found."""
        return len(self.results) > 0

    @property
    def first_result(self) -> Optional[VerificationResult]:
        """Get the first verification result (most common use case)."""
        return self.results[0] if self.results else None

    @property
    def result_count(self) -> int:
        """Get the number of verification results."""
        return len(self.results)

    @property
    def has_verified_result(self) -> bool:
        """Check if any result is verified."""
        return any(result.is_verified for result in self.results)

    @property
    def verified_results(self) -> List[VerificationResult]:
        """Get all verified results only."""
        return [result for result in self.results if result.is_verified]

    @property
    def is_approaching_rate_limit(self) -> bool:
        """Check if approaching rate limit (within 10%)."""
        return self.rate_limit_info.is_near_limit if self.rate_limit_info else False

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        data = {
            "results": [result.to_dict() for result in self.results],
        }

        if self.rate_limit_info:
            data["rate_limit"] = self.rate_limit_info.to_dict()

        return data