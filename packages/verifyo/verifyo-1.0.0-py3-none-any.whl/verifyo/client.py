"""Main Verifyo SDK client for KYC verification checks."""

import json
from typing import Optional
from urllib.parse import urljoin

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from .exceptions import (
    ApiException,
    AuthenticationException,
    NetworkException,
    RateLimitException,
)
from .models import CheckResponse, RateLimitInfo


class VerifyoClient:
    """Main Verifyo SDK client for KYC verification checks."""

    DEFAULT_BASE_URL = "https://api.verifyo.com"
    DEFAULT_TIMEOUT = 30
    SDK_VERSION = "1.0.0"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        debug: bool = False,
    ) -> None:
        """Initialize the Verifyo client.

        Args:
            api_key: Your Verifyo secret API key (must start with 'vfy_sk_')
            base_url: API base URL (defaults to https://api.verifyo.com)
            timeout: Request timeout in seconds (defaults to 30)
            debug: Enable debug logging for development

        Raises:
            ValueError: If API key is empty or invalid format
        """
        if not api_key:
            raise ValueError("API key is required")

        if not api_key.startswith("vfy_sk_"):
            raise ValueError(
                "Invalid API key format. API key must start with 'vfy_sk_'"
            )

        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.debug = debug

        # Configure requests session
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"verifyo-python-sdk/{self.SDK_VERSION} (Python {__import__('sys').version.split()[0]})",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        })

    def check_address(
        self, 
        address: str, 
        network: Optional[str] = None
    ) -> CheckResponse:
        """Check KYC verification status for a wallet address.

        Args:
            address: Wallet address to check (required)
            network: Blockchain network identifier (optional, e.g., 'ethereum', 'bitcoin')

        Returns:
            CheckResponse containing verification results and rate limit information

        Raises:
            ValueError: If address is empty
            AuthenticationException: Invalid API key (401)
            RateLimitException: Rate limit exceeded (429)
            ApiException: General API errors
            NetworkException: Network connectivity issues
        """
        if not address:
            raise ValueError("Address is required")

        # Build query parameters
        params = {"address": address}
        if network:
            params["network"] = network

        url = urljoin(self.base_url, "/v1/check")

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
            )

            if self.debug:
                print(f"Verifyo API Response: {response.text}")

            # Extract rate limit information from headers
            rate_limit_info = self._extract_rate_limit_info(response)

            # Handle HTTP errors
            if not response.ok:
                self._handle_http_error(response)

            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise ApiException(
                    "Invalid JSON response from API",
                    response.status_code,
                    {"json_error": str(e), "response_text": response.text}
                )

            return CheckResponse.from_dict(data, rate_limit_info)

        except (ConnectionError, Timeout) as e:
            raise NetworkException(
                f"Network error: {str(e)}",
                {"original_exception": e}
            )
        except RequestException as e:
            raise NetworkException(
                f"Request error: {str(e)}",
                {"original_exception": e}
            )

    def _extract_rate_limit_info(self, response: requests.Response) -> Optional[RateLimitInfo]:
        """Extract rate limit information from response headers."""
        headers = response.headers
        
        if "X-RateLimit-Limit" in headers:
            return RateLimitInfo(
                limit=int(headers.get("X-RateLimit-Limit", "0")),
                used=int(headers.get("X-RateLimit-Used", "0")),
                remaining=int(headers.get("X-RateLimit-Remaining", "0")),
                tier=headers.get("X-RateLimit-Tier", "unknown"),
            )

        return None

    def _handle_http_error(self, response: requests.Response) -> None:
        """Handle HTTP errors and convert to appropriate SDK exceptions."""
        status_code = response.status_code
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"error": {"message": response.text}}

        if self.debug:
            print(f"Verifyo API Error Response: {response.text}")

        error_message = data.get("error", {}).get("message", "API error occurred")
        context = {"response_data": data, "status_code": status_code}

        if status_code == 401:
            raise AuthenticationException(error_message, context)
        elif status_code == 429:
            # Rate limit error with detailed information
            limit = data.get("limit", 0)
            used = data.get("used", 0)
            remaining = data.get("remaining", 0)
            tier = data.get("tier", "unknown")
            resets_at = data.get("resets_at")
            
            raise RateLimitException(
                error_message,
                limit,
                used,
                remaining,
                tier,
                resets_at,
                context
            )
        else:
            raise ApiException(error_message, status_code, context)

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self) -> "VerifyoClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()