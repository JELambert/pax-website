"""Authentication routes: GitHub OAuth login/callback/logout."""

from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import RedirectResponse

from ..auth import AuthManager
from ..config import get_settings
from ..models import UserInfo

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_COOKIE = "pax_session"


def get_auth_manager() -> AuthManager:
    return AuthManager(get_settings())


def get_current_user(request: Request) -> UserInfo | None:
    """Extract user from session cookie. Returns None if not authenticated."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    return get_auth_manager().verify_session_token(token)


def require_user(request: Request) -> UserInfo:
    """Extract user from session cookie. Raises 401 if not authenticated."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/login")
async def login(request: Request):
    """Redirect to GitHub OAuth."""
    auth = get_auth_manager()
    url, state = auth.get_login_url()
    response = RedirectResponse(url=url, status_code=302)
    response.set_cookie(
        "oauth_state", state, httponly=True, secure=True, samesite="lax", max_age=600
    )
    return response


@router.get("/callback")
async def callback(request: Request, code: str, state: str):
    """Handle GitHub OAuth callback."""
    # Verify state
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    auth = get_auth_manager()
    settings = get_settings()

    try:
        token = await auth.exchange_code(code)
        user = await auth.get_github_user(token)
    except Exception:
        raise HTTPException(status_code=400, detail="OAuth authentication failed")

    session_token = auth.create_session_token(user)

    response = RedirectResponse(url=settings.base_url, status_code=302)
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,
    )
    response.delete_cookie("oauth_state")
    return response


@router.post("/logout")
async def logout():
    """Clear session cookie."""
    response = Response(status_code=200)
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get("/me")
async def me(request: Request):
    """Return current user info."""
    user = require_user(request)
    return user.model_dump()
