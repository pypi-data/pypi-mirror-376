"""AML (Anti-Money Laundering) screening results."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class AmlScreening:
    """AML (Anti-Money Laundering) screening results."""

    sanctioned: bool = False
    pep: bool = False
    criminal: bool = False
    barred: bool = False
    military: bool = False
    adverse_media: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AmlScreening":
        """Create AmlScreening from API response data."""
        return cls(
            sanctioned=data.get("sanctioned", False),
            pep=data.get("pep", False),
            criminal=data.get("criminal", False),
            barred=data.get("barred", False),
            military=data.get("military", False),
            adverse_media=data.get("adverse_media", False),
        )

    @property
    def passes_aml_screening(self) -> bool:
        """Check if user passes all AML screening (no flags)."""
        return not any([
            self.sanctioned,
            self.pep,
            self.criminal,
            self.barred,
            self.military,
            self.adverse_media,
        ])

    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary representation."""
        return {
            "sanctioned": self.sanctioned,
            "pep": self.pep,
            "criminal": self.criminal,
            "barred": self.barred,
            "military": self.military,
            "adverse_media": self.adverse_media,
        }