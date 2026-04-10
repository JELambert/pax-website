"""Status route: list user's submitted PRs."""

from fastapi import APIRouter, Request

from ..config import get_settings
from ..github_api import GitHubClient
from ..models import SubmissionInfo
from .auth_routes import require_user

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/submissions", response_model=list[SubmissionInfo])
async def list_submissions(request: Request):
    """List the current user's submitted PRs and their CI status."""
    user = require_user(request)
    settings = get_settings()

    github = GitHubClient(settings)
    try:
        submissions = await github.get_user_submissions(user.username)
    finally:
        await github.close()

    return [SubmissionInfo(**s) for s in submissions]
