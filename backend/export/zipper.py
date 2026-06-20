"""cloud run zip assembly and serving"""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

EXPORT_ROOT = Path(__file__).resolve().parents[1] / "generated_exports"


def create_export_zip(workspace_id: str, files: dict[str, str]) -> tuple[str, Path]:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    export_id = f"{_safe(workspace_id)}-{uuid4().hex[:8]}"
    path = EXPORT_ROOT / f"{export_id}.zip"
    with ZipFile(path, "w", ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return export_id, path


def get_export_path(export_id: str) -> Path:
    path = EXPORT_ROOT / f"{_safe(export_id)}.zip"
    if not path.exists():
        raise FileNotFoundError(export_id)
    return path


def _safe(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "-", value)
