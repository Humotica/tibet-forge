"""
Transparency Mirror client for tibet-forge.

Best-effort: network errors produce warnings, never hard failures.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

import httpx

DEFAULT_MIRROR_URL = "https://brein.jaspervandemeent.nl"
TIMEOUT_SECS = 5


def hash_directory(project_path: Path, ignore: list[str] | None = None) -> str:
    """
    Compute a stable SHA-256 hash of a project directory.

    Hashes all non-ignored files sorted by relative path for determinism.
    """
    ignore = ignore or ["__pycache__", ".git", ".venv", "venv",
                        "node_modules", "dist", "build", ".egg-info"]
    hasher = hashlib.sha256()
    file_count = 0

    for file_path in sorted(project_path.rglob("*")):
        if not file_path.is_file():
            continue
        rel = str(file_path.relative_to(project_path))
        if any(ign in rel for ign in ignore):
            continue
        try:
            data = file_path.read_bytes()
            hasher.update(rel.encode("utf-8"))
            hasher.update(data)
            file_count += 1
        except (OSError, PermissionError):
            continue

    return f"sha256:{hasher.hexdigest()}"


def register_certification(
    mirror_url: str,
    content_hash: str,
    score: int,
    grade: str,
    project_name: str = "",
    signing_key: str = "",
    jis_id: str = "",
    source_repo: str = "",
) -> Dict[str, Any]:
    """
    Register a certification result with the Transparency Mirror.

    Returns dict with 'status' key ('registered' or 'already_registered').
    Raises on network error.
    """
    url = f"{mirror_url.rstrip('/')}/api/tbz-mirror/register"
    payload = {
        "content_hash": content_hash,
        "signing_key": signing_key,
        "jis_id": jis_id or "",
        "source_repo": source_repo or project_name,
        "block_count": 0,
        "total_size": 0,
        "forge_score": score,
        "forge_grade": grade,
    }

    resp = httpx.post(url, json=payload, timeout=TIMEOUT_SECS)
    resp.raise_for_status()
    return resp.json()


def lookup(
    mirror_url: str,
    content_hash: str,
) -> Optional[Dict[str, Any]]:
    """
    Look up a hash in the Transparency Mirror.

    Returns entry dict if found, None if not found (404).
    Raises on network error.
    """
    url = f"{mirror_url.rstrip('/')}/api/tbz-mirror/lookup/{content_hash}"
    resp = httpx.get(url, timeout=TIMEOUT_SECS)

    if resp.status_code == 404:
        return None

    resp.raise_for_status()
    return resp.json()
