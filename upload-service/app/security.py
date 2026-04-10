import re
import zipfile
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

ALLOWED_EXTENSIONS = {".yaml", ".yml", ".json"}
PACK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5MB per file
MAX_TOTAL_BYTES = 10 * 1024 * 1024  # 10MB total
MAX_FILE_COUNT = 20


def safe_extract_zip(zip_bytes: bytes, max_total: int = MAX_TOTAL_BYTES) -> tuple[TemporaryDirectory, Path, list[str]]:
    """Extract a zip safely, returning (tmpdir_handle, pack_root_path, errors).

    The caller must keep tmpdir_handle alive — when it goes out of scope
    the temporary directory is cleaned up.
    """
    errors: list[str] = []

    if len(zip_bytes) > max_total:
        errors.append(f"Upload exceeds {max_total // (1024*1024)}MB limit")
        return TemporaryDirectory(), Path(), errors

    try:
        zf = zipfile.ZipFile(__import__("io").BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        errors.append("File is not a valid zip archive")
        return TemporaryDirectory(), Path(), errors

    # Check member count
    members = zf.infolist()
    if len(members) > MAX_FILE_COUNT:
        errors.append(f"Zip contains {len(members)} files (max {MAX_FILE_COUNT})")
        return TemporaryDirectory(), Path(), errors

    # Check total uncompressed size
    total_size = sum(m.file_size for m in members)
    if total_size > max_total:
        errors.append(f"Uncompressed size ({total_size // 1024}KB) exceeds {max_total // (1024*1024)}MB limit")
        return TemporaryDirectory(), Path(), errors

    # Validate each member before extraction
    for member in members:
        name = member.filename

        # Skip directories
        if member.is_dir():
            continue

        # Path traversal checks
        parts = PurePosixPath(name).parts
        if ".." in parts:
            errors.append(f"Path traversal detected: {name}")
            continue
        if PurePosixPath(name).is_absolute():
            errors.append(f"Absolute path detected: {name}")
            continue

        # No symlinks
        if member.external_attr >> 28 == 0xA:
            errors.append(f"Symlink detected: {name}")
            continue

        # No dotfiles/hidden files
        basename = PurePosixPath(name).name
        if basename.startswith("."):
            errors.append(f"Hidden file not allowed: {name}")
            continue

        # Extension whitelist (skip directory entries)
        ext = PurePosixPath(name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"File type not allowed ({ext}): {name}")
            continue

        # Per-file size
        if member.file_size > MAX_FILE_BYTES:
            errors.append(f"File too large ({member.file_size // 1024}KB): {name}")

    if errors:
        return TemporaryDirectory(), Path(), errors

    # Safe to extract — do it member by member
    tmpdir = TemporaryDirectory()
    tmpdir_path = Path(tmpdir.name)

    for member in members:
        if member.is_dir():
            (tmpdir_path / member.filename).mkdir(parents=True, exist_ok=True)
            continue
        target = tmpdir_path / member.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member) as src, open(target, "wb") as dst:
            dst.write(src.read())

    zf.close()

    # Detect pack root: if zip has a single top-level directory, use that
    top_items = list(tmpdir_path.iterdir())
    if len(top_items) == 1 and top_items[0].is_dir():
        pack_root = top_items[0]
    else:
        pack_root = tmpdir_path

    return tmpdir, pack_root, errors


def validate_pack_name(name: str) -> str | None:
    """Return error message if pack name is invalid, None if OK."""
    if not PACK_NAME_RE.match(name):
        return (
            f"Invalid pack name '{name}'. "
            "Must be 3-64 chars, lowercase alphanumeric and hyphens, "
            "starting with a letter or digit."
        )
    return None
