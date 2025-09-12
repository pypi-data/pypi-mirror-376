"""Individual KYC verification result for a wallet address."""

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

from .aml_screening import AmlScreening
from .wallet_info import WalletInfo

KycStatus = Literal["verified", "not_verified"]


@dataclass(frozen=True)
class VerificationResult:
    """Individual KYC verification result for a wallet address."""

    zk_kyc_token: str
    identity: str
    kyc_level: int
    kyc_status: KycStatus
    document_country: Optional[str]
    residence_country: Optional[str]
    age_over_18: bool
    age_over_21: bool
    wallet: WalletInfo
    aml: AmlScreening

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationResult":
        """Create VerificationResult from API response data."""
        return cls(
            zk_kyc_token=data.get("zk_kyc_token", ""),
            identity=data.get("identity", ""),
            kyc_level=data.get("kyc_level", 0),
            kyc_status=data.get("kyc_status", "not_verified"),
            document_country=data.get("document_country"),
            residence_country=data.get("residence_country"),
            age_over_18=data.get("age_over_18", False),
            age_over_21=data.get("age_over_21", False),
            wallet=WalletInfo.from_dict(data.get("wallet", {})),
            aml=AmlScreening.from_dict(data.get("aml", {})),
        )

    @property
    def is_verified(self) -> bool:
        """Check if user is KYC verified."""
        return self.kyc_status == "verified"

    @property
    def meets_basic_requirements(self) -> bool:
        """Check if user meets minimum requirements for most platforms.
        
        Returns True if user is:
        - KYC verified
        - Over 18 years old  
        - Passes AML screening
        - Has safe wallet (not sanctioned, not high risk)
        """
        return (
            self.is_verified
            and self.age_over_18
            and self.aml.passes_aml_screening
            and self.wallet.is_safe_to_interact
        )

    @property
    def is_suitable_for_age_restricted_services(self) -> bool:
        """Check if user is suitable for age-restricted services (21+)."""
        return self.meets_basic_requirements and self.age_over_21

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "zk_kyc_token": self.zk_kyc_token,
            "identity": self.identity,
            "kyc_level": self.kyc_level,
            "kyc_status": self.kyc_status,
            "document_country": self.document_country,
            "residence_country": self.residence_country,
            "age_over_18": self.age_over_18,
            "age_over_21": self.age_over_21,
            "wallet": self.wallet.to_dict(),
            "aml": self.aml.to_dict(),
        }