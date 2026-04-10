"""GitHub OAuth authentication and session management."""

import secrets

import httpx
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from .config import Settings
from .models import UserInfo

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

# Session cookie max age: 24 hours
SESSION_MAX_AGE = 86400


class AuthManager:
    def __init__(self, settings: Settings):
        self.client_id = settings.github_client_id
        self.client_secret = settings.github_client_secret
        self.callback_url = f"{settings.base_url}/auth/callback"
        self.serializer = URLSafeTimedSerializer(settings.secret_key)

    def get_login_url(self) -> tuple[str, str]:
        """Generate GitHub OAuth URL. Returns (url, state)."""
        state = secrets.token_urlsafe(32)
        url = (
            f"{GITHUB_AUTHORIZE_URL}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.callback_url}"
            f"&scope=read:user"
            f"&state={state}"
        )
        return url, state

    async def exchange_code(self, code: str) -> str:
        """Exchange OAuth code for access token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise ValueError(f"OAuth error: {data['error_description']}")
            return data["access_token"]

    async def get_github_user(self, token: str) -> UserInfo:
        """Fetch user info from GitHub."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return UserInfo(
                username=data["login"],
                avatar_url=data.get("avatar_url"),
            )

    def create_session_token(self, user: UserInfo) -> str:
        """Create a signed session token."""
        return self.serializer.dumps({"username": user.username, "avatar_url": user.avatar_url})

    def verify_session_token(self, token: str) -> UserInfo | None:
        """Verify and decode a session token. Returns None if invalid/expired."""
        try:
            data = self.serializer.loads(token, max_age=SESSION_MAX_AGE)
            return UserInfo(**data)
        except (BadSignature, SignatureExpired):
            return None
