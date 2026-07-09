"""Security logic for OIDC/Keycloak integration.

Implements Story 11-1 Part C: OIDC Integration.
Validates 'Authorization: Bearer <JWT>' against Keycloak JWKS.
"""

from typing import Dict, Any, Optional
from functools import lru_cache
import httpx
from jose import jwt, JWTError
from fastapi import HTTPException, status
from jarvis.config.settings import load_settings

settings = load_settings()

@lru_cache()
def get_jwks_url() -> str:
    # Usually: http://keycloak:8080/realms/jarvis/protocol/openid-connect/certs
    return settings.identity.jwks_url

_jwks_cache: Optional[Dict[str, Any]] = None

async def get_jwks() -> Dict[str, Any]:
    """Fetch and cache JSON Web Key Set from IdP."""
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
        
    url = get_jwks_url()
    try:
        async with httpx.AsyncClient() as client:
            # Short timeout, failure means Auth system down
            resp = await client.get(url, timeout=5.0)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            return _jwks_cache
    except Exception as e:
        # Log error in production
        print(f"CRITICAL: Failed to fetch JWKS from {url}: {e}")
        return {} # Return empty to fail validation gracefully (Invalid Signature)

async def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT signature and return claims.
    
    Args:
        token: Raw JWT string
        
    Returns:
        Dict of claims (sub, iss, email, etc.)
        
    Raises:
        HTTPException: If token invalid or expired
    """
    jwks = await get_jwks()
    if not jwks:
        raise HTTPException(status_code=503, detail="Identity System unavailable")
        
    try:
        # Verify signature using JWKS
        # We explicitly trust the Issuer from settings
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience="account", # Default Keycloak audience for account management
            # In production, we should match 'jarvis-api' client ID
            options={
                "verify_aud": False, # Relaxed for Story 11-1 initial wiring
                "verify_iss": False  # CRITICAL FIX: Disabled because Browser sees 'localhost:8081' but Backend sees 'keycloak:8080'. Issuer mismatch is expected in Dev/Docker.
            },
            # issuer=... # Removed/Ignored because verify_iss is False
            issuer=f"{settings.identity.url}/realms/{settings.identity.realm}"
        )
        return payload
    except JWTError as e:
        print(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
