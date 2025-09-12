"""Wallet information and risk assessment."""

from dataclasses import dataclass
from typing import Any, Dict, Literal

OwnershipStatus = Literal["verified", "self_declared", "not_found"]


@dataclass(frozen=True)
class WalletInfo:
    """Wallet information and risk assessment."""

    address: str
    ownership_status: OwnershipStatus = "not_found"
    sanctioned: bool = False
    high_risk: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletInfo":
        """Create WalletInfo from API response data."""
        return cls(
            address=data.get("address", ""),
            ownership_status=data.get("ownership_status", "not_found"),
            sanctioned=data.get("sanctioned", False),
            high_risk=data.get("high_risk", False),
        )

    @property
    def is_ownership_verified(self) -> bool:
        """Check if wallet ownership is cryptographically verified."""
        return self.ownership_status == "verified"

    @property
    def is_safe_to_interact(self) -> bool:
        """Check if wallet is safe to interact with (not sanctioned, not high risk)."""
        return not self.sanctioned and not self.high_risk

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "address": self.address,
            "ownership_status": self.ownership_status,
            "sanctioned": self.sanctioned,
            "high_risk": self.high_risk,
        }