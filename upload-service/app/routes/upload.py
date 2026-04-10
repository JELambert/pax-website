"""Upload route: accept zip, validate, create PR."""

import time

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import get_settings
from ..github_api import GitHubClient
from ..models import UploadResponse
from ..security import safe_extract_zip
from ..validation import validate_pack
from .auth_routes import require_user

router = APIRouter(prefix="/api", tags=["upload"])

limiter = Limiter(key_func=get_remote_address)


@router.post("/upload", response_model=UploadResponse)
@limiter.limit("5/hour")
async def upload_pack(request: Request, file: UploadFile = File(...)):
    """Accept a zip file, validate the pack, and create a GitHub PR."""
    user = require_user(request)
    settings = get_settings()

    # Check file type
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload must be a .zip file")

    # Read file bytes (with size limit)
    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_bytes // (1024*1024)}MB limit",
        )

    # Extract safely
    tmpdir, pack_root, security_errors = safe_extract_zip(contents, settings.max_upload_bytes)

    if security_errors:
        return UploadResponse(success=False, errors=security_errors)

    # Validate pack
    try:
        result = validate_pack(pack_root)
    finally:
        # Don't clean up yet — we need files for the commit
        pass

    if not result.valid:
        tmpdir.cleanup()
        return UploadResponse(
            success=False,
            errors=result.errors,
            warnings=result.warnings,
            pack_name=result.pack_name,
        )

    pack_name = result.pack_name
    if not pack_name:
        tmpdir.cleanup()
        return UploadResponse(success=False, errors=["Pack name could not be determined from pax.yaml"])

    # Collect files for commit
    files: dict[str, bytes] = {}
    for file_path in pack_root.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(pack_root))
            files[rel_path] = file_path.read_bytes()

    tmpdir.cleanup()

    # Create PR via GitHub API
    github = GitHubClient(settings)
    try:
        is_update = await github.check_pack_exists(pack_name)
        branch_name = f"community/{pack_name}-{int(time.time())}"

        await github.commit_pack_files(branch_name, pack_name, files)

        pr_data = await github.create_pull_request(
            branch_name, pack_name, user.username, is_update
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to create PR: {e}")
    finally:
        await github.close()

    return UploadResponse(
        success=True,
        pr_url=pr_data["html_url"],
        pr_number=pr_data["number"],
        pack_name=pack_name,
        warnings=result.warnings if result.warnings else None,
    )
