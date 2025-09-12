"""Verifyo Python SDK for Zero-Knowledge KYC verification.

Official Python SDK for the Verifyo Zero-Knowledge KYC API.
Verify wallet addresses for KYC compliance without exposing user personal data.

Example:
    Basic usage:
    
    >>> from verifyo import VerifyoClient
    >>> client = VerifyoClient("vfy_sk_your_api_key_here")
    >>> response = client.check_address("0x742d35Cc6634C0532925a3b8D89B0E5C9a7c9f35")
    >>> if response.has_results:
    ...     verification = response.first_result
    ...     if verification.meets_basic_requirements:
    ...         print("User is compliant")

For more examples and documentation, visit: https://verifyo.com/docs
"""

from .client import VerifyoClient
from .exceptions import (
    ApiException,
    AuthenticationException,
    NetworkException,
    RateLimitException,
    VerifyoException,
)
from .models import (
    AmlScreening,
    CheckResponse,
    RateLimitInfo,
    VerificationResult,
    WalletInfo,
)

__version__ = "1.0.0"
__author__ = "Verifyo Team"
__email__ = "developers@verifyo.com"

__all__ = [
    # Main client
    "VerifyoClient",
    
    # Exceptions
    "VerifyoException",
    "AuthenticationException",
    "RateLimitException", 
    "ApiException",
    "NetworkException",
    
    # Models
    "CheckResponse",
    "VerificationResult",
    "WalletInfo",
    "AmlScreening",
    "RateLimitInfo",
]