from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_library_file(library_dir: Path) -> Path:
    library_dir.mkdir(parents=True, exist_ok=True)
    return library_dir / "project_library.json"


def list_saved_projects(library_dir: Path) -> list[dict[str, Any]]:
    """Return a list of all saved project summaries sorted by updated_at descending."""
    file_path = _get_library_file(library_dir)
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        projects = list(data.values())
        return sorted(projects, key=lambda p: p.get("updated_at", ""), reverse=True)
    except Exception as e:
        logger.error(f"Failed to load project library: {e}")
        return []


def save_project_draft(project_data: dict[str, Any], library_dir: Path) -> str:
    """Save or update a project draft in the local library."""
    file_path = _get_library_file(library_dir)
    library: dict[str, Any] = {}
    if file_path.exists():
        try:
            library = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            library = {}

    topic = project_data.get("topic") or project_data.get("niche") or "draft-project"
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:32] or "project"
    project_id = project_data.get("project_id") or f"{slug}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    now_str = datetime.now(timezone.utc).isoformat()
    project_data["project_id"] = project_id
    project_data["updated_at"] = now_str
    if "created_at" not in project_data:
        project_data["created_at"] = now_str

    library[project_id] = project_data
    file_path.write_text(json.dumps(library, indent=2), encoding="utf-8")
    return project_id


def load_project_draft(project_id: str, library_dir: Path) -> dict[str, Any] | None:
    """Retrieve full project state for a given project ID."""
    file_path = _get_library_file(library_dir)
    if not file_path.exists():
        return None
    try:
        library = json.loads(file_path.read_text(encoding="utf-8"))
        return library.get(project_id)
    except Exception as e:
        logger.error(f"Failed to load project '{project_id}': {e}")
        return None


def delete_project_draft(project_id: str, library_dir: Path) -> bool:
    """Remove a project draft from the library."""
    file_path = _get_library_file(library_dir)
    if not file_path.exists():
        return False
    try:
        library = json.loads(file_path.read_text(encoding="utf-8"))
        if project_id in library:
            del library[project_id]
            file_path.write_text(json.dumps(library, indent=2), encoding="utf-8")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete project '{project_id}': {e}")
        return False
