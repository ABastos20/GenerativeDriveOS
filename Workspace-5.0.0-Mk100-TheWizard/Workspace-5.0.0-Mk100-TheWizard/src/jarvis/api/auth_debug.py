from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/api/auth", tags=["auth-debug"])

@router.get("/me-debug")
async def auth_me(request: Request):
    """Debug endpoint to check session state directly."""
    user_id = request.session.get("user_id")
    from jarvis.api.auth import get_token_store
    store = get_token_store()
    
    return {
        "status": "authenticated" if user_id else "unauthenticated",
        "session_user_id": user_id,
        "in_memory_store_has_user": user_id in store if user_id else False,
        "session_dump": dict(request.session)
    }

@router.get("/debug-session")
async def debug_session(request: Request):
    """Raw dump of session and cookies."""
    return {
        "session": dict(request.session),
        "cookies": request.cookies,
        "headers": dict(request.headers)
    }
