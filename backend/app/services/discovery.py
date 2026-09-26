from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__",
    "dist", "build", ".mypy_cache", ".pytest_cache", "site-packages",
}

EXTENSION_LANGUAGE = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rb": "Ruby",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
}


def discover_files(root: Path) -> List[Dict]:
    """Walk the repo (skipping noise directories) and return per-file metadata."""
    results = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        lang = EXTENSION_LANGUAGE.get(path.suffix)
        if not lang:
            continue
        try:
            loc = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore"))
        except OSError:
            loc = 0
        results.append({"path": path, "language": lang, "loc": loc})
    return results


def language_breakdown(files: List[Dict]) -> List[Dict]:
    loc_by_lang: Counter = Counter()
    files_by_lang: Counter = Counter()
    for f in files:
        loc_by_lang[f["language"]] += f["loc"]
        files_by_lang[f["language"]] += 1

    total = sum(loc_by_lang.values()) or 1
    return [
        {
            "language": lang,
            "percentage": round(loc / total * 100, 1),
            "files": files_by_lang[lang],
        }
        for lang, loc in loc_by_lang.most_common()
    ]
