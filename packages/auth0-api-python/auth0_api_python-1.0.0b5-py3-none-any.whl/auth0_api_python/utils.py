"""
Utility functions for OIDC discovery and JWKS fetching (asynchronously)
using httpx or a custom fetch approach.
"""

import base64
import hashlib
import json
import re
from typing import Any, Callable, Optional, Union

import httpx
from ada_url import URL


async def fetch_oidc_metadata(
    domain: str,
    custom_fetch: Optional[Callable[..., Any]] = None
) -> dict[str, Any]:
    """
    Asynchronously fetch the OIDC config from https://{domain}/.well-known/openid-configuration.
    Returns a dict with keys like issuer, jwks_uri, authorization_endpoint, etc.
    If custom_fetch is provided, we call it instead of httpx.
    """
    url = f"https://{domain}/.well-known/openid-configuration"
    if custom_fetch:
        response = await custom_fetch(url)
        return response.json() if hasattr(response, "json") else response
    else:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()


async def fetch_jwks(
    jwks_uri: str,
    custom_fetch: Optional[Callable[..., Any]] = None
) -> dict[str, Any]:
    """
    Asynchronously fetch the JSON Web Key Set from jwks_uri.
    Returns the raw JWKS JSON, e.g. {'keys': [...]}

    If custom_fetch is provided, it must be an async callable
    that fetches data from the jwks_uri.
    """
    if custom_fetch:
        response = await custom_fetch(jwks_uri)
        return response.json() if hasattr(response, "json") else response
    else:
        async with httpx.AsyncClient() as client:
            resp = await client.get(jwks_uri)
            resp.raise_for_status()
            return resp.json()


def get_unverified_header(token: Union[str, bytes]) -> dict:
    """
    Parse the first segment (header) of a JWT without verifying signature.
    Ensures correct Base64 padding before decode to avoid garbage bytes.
    """
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid token format: expected 3 segments, got {len(parts)}")

    header_b64 = parts[0]
    header_b64 = remove_bytes_prefix(header_b64)
    header_b64 = fix_base64_padding(header_b64)

    header_data = base64.urlsafe_b64decode(header_b64)
    return json.loads(header_data)



def fix_base64_padding(segment: str) -> str:
    """
    If `segment`'s length is not a multiple of 4, add '=' padding
    so that base64.urlsafe_b64decode won't produce nonsense bytes.
    No extra '=' added if length is already a multiple of 4.
    """
    remainder = len(segment) % 4
    if remainder == 0:
        return segment  # No additional padding needed
    return segment + ("=" * (4 - remainder))

def remove_bytes_prefix(s: str) -> str:
    """If the string looks like b'eyJh...', remove the leading b' and trailing '."""
    if s.startswith("b'"):
        return s[2:]  # cut off the leading b'
    return s

def normalize_url_for_htu(raw_url: str) -> str:
    """
    Normalize URL for DPoP htu comparison .

    Args:
        raw_url: The raw URL string to normalize
    Returns:
        The normalized URL string
    Raises:
        ValueError: If the URL is invalid or cannot be parsed
    """

    try:
        url_obj = URL(raw_url)

        normalized_url = url_obj.origin + url_obj.pathname

        normalized_url = re.sub(
            r'%([0-9a-fA-F]{2})',
            lambda m: f'%{m.group(1).upper()}',
            normalized_url
        )

        return normalized_url
    except Exception as e:
        raise ValueError(f"Invalid URL format: {raw_url}") from e

def sha256_base64url(input_str: Union[str, bytes]) -> str:
    """
    Compute SHA-256 digest of the input string and return a
    Base64URL-encoded string *without* padding.
    """
    if isinstance(input_str, str):
        digest = hashlib.sha256(input_str.encode("utf-8")).digest()
    else:
        digest = hashlib.sha256(input_str).digest()
    b64 = base64.urlsafe_b64encode(digest).decode("utf-8")
    return b64.rstrip("=")

def calculate_jwk_thumbprint(jwk: dict[str, str]) -> str:
    """
    Compute the RFC 7638 JWK thumbprint for a public JWK.

    - For EC keys, includes only: crv, kty, x, y
    - Serializes with no whitespace, keys sorted lexicographically
    - Hashes with SHA-256 and returns base64url-encoded string without padding
    """
    kty = jwk.get("kty")

    if kty == "EC":
        if not all(k in jwk for k in ["crv", "x", "y"]):
            raise ValueError("EC key missing required parameters")
        members = ("crv", "kty", "x", "y")
    else:
        raise ValueError(f"{kty}(Key Type) Parameter missing or unsupported ")

    ordered = {k: jwk[k] for k in members if k in jwk}

    thumbprint_json = json.dumps(ordered, separators=(",", ":"), sort_keys=True)

    digest = hashlib.sha256(thumbprint_json.encode("utf-8")).digest()

    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
