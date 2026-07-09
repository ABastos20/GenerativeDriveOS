import os
import secrets
import hashlib
import base64
import httpx
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from jarvis.config.settings import load_settings
from jarvis.api.security import verify_token

settings = load_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

# Keycloak Configuration
# Internal URL for Backend -> Keycloak communication (Docker network)
INTERNAL_KEYCLOAK_URL = settings.identity.url  # e.g., http://keycloak:8080

# Public URL for Browser -> Keycloak redirection
# We infer this or use a default override for dev.
# In prod, this should be the same as internal or a proper domain.
PUBLIC_KEYCLOAK_URL = os.environ.get("KEYCLOAK_PUBLIC_URL", "http://localhost:8081")

REALM = settings.identity.realm
CLIENT_ID = "jarvis-ui" # Using the public client
# CLIENT_SECRET = ... # Not needed for public client with PKCE

def get_pkce_challenge():
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).replace(b'=', b'').decode()
    return verifier, challenge

# === IN-MEMORY TOKEN STORE (DEV FIX) ===
# Ideally this is Redis, but for immediate fix we use a global dict.
# Structure: { "sub_id": { "access_token": "...", "id_token": "...", ... } }
_TOKEN_STORE: Dict[str, Any] = {}

def get_token_store():
    return _TOKEN_STORE

@router.get("/login")
async def login(request: Request, returnUrl: Optional[str] = "/governance"):
    """Initiates the OIDC Login Flow."""
    verifier, challenge = get_pkce_challenge()
    
    # Store verifier and returnUrl in session
    request.session["code_verifier"] = verifier
    request.session["return_url"] = returnUrl
    
    # Construct Authorization URL
    # note: redirect_uri must match exactly what is registered in Keycloak
    
    # FORCE LOCALHOST: Ensure we don't accidentally use internal Docker IP
    redirect_uri = "http://localhost:8000/auth/callback" 
    # Force http for dev/localhost strict matching if needed, but request.base_url usually works
    
    auth_url = (
        f"{PUBLIC_KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
        f"&scope=openid profile email roles"
    )
    
    return RedirectResponse(auth_url)

@router.get("/callback")
async def callback(request: Request, code: str, state: Optional[str] = None):
    """Handles OIDC Callback and Token Exchange."""
    verifier = request.session.get("code_verifier")
    if not verifier:
        raise HTTPException(status_code=400, detail="Missing code verifier in session. Please try logging in again.")
    
    # redirect_uri = f"{request.base_url}auth/callback"
    # FORCE LOCALHOST: Ensure we don't accidentally use internal Docker IP
    redirect_uri = "http://localhost:8000/auth/callback"
    print(f"[Auth] Callback received. processing code... BaseURL: {request.base_url}", flush=True)
    
    # Exchange code for token (Server-Side)
    token_url = f"{INTERNAL_KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": verifier
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(token_url, data=data)
            resp.raise_for_status()
            tokens = resp.json()
            
        # Verify and get user info
        user_info = await verify_token(tokens["access_token"])
        print(f"[Auth] Token Verified. User: {user_info.get('preferred_username')}")
        
        # === ARCHITECT FIX: STORE TOKENS SERVER-SIDE ===
        user_id = user_info["sub"]
        _TOKEN_STORE[user_id] = {
            "tokens": tokens,
            "user_info": user_info
        }
        
        print(f"[AUTH] Session BEFORE Assignment: {dict(request.session)}", flush=True)
        
        # Store ONLY the pointer in the session cookie
        request.session.clear() # Start fresh
        request.session["user_id"] = user_id
        
        # We also create a "user" object for frontend simplicity, but keep it SMALL
        request.session["user"] = {
            "sub": user_id,
            "preferred_username": user_info.get("preferred_username"),
            "email": user_info.get("email")
        }
        
        print(f"[AUTH] session AFTER Assignment: {dict(request.session)}", flush=True)
        
        print(f"[Auth] Session Established for {user_id}. Redirecting to /governance...", flush=True)
        return RedirectResponse("/governance")
        
    except httpx.HTTPStatusError as e:
        print(f"Token exchange failed: {e.response.text}")
        raise HTTPException(status_code=401, detail="Failed to exchange token with Identity Provider")
    except Exception as e:
        print(f"Callback error: {e}")
        raise HTTPException(status_code=500, detail="Authentication callback failed")

@router.get("/logout")
async def logout(request: Request):
    """Clears session and redirects to Keycloak logout."""
    user_id = request.session.get("user_id")
    if user_id and user_id in _TOKEN_STORE:
        del _TOKEN_STORE[user_id]
        
    request.session.clear()
    logout_url = f"{PUBLIC_KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/logout?redirect_uri={request.base_url}"
    return RedirectResponse(logout_url)

@router.get("/me")
async def me(request: Request):
    """Returns current user session info."""
    # Check Session
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check Store
    if user_id not in _TOKEN_STORE:
        # Session exists but server lost state (restart) -> Force Re-login
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session expired (Server State Lost)")
        
    return _TOKEN_STORE[user_id]["user_info"]
