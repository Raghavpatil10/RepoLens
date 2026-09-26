from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


def run_pip_audit(req_file: Path) -> Dict[str, List[str]]:
    """Returns {package_name_lower: [vuln_id, ...]}. Empty dict on any failure —
    pip-audit needs network access to PyPI's advisory DB, which may be slow
    or unavailable; the rest of the report should still work without it."""
    try:
        proc = subprocess.run(
            ["pip-audit", "-r", str(req_file), "-f", "json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        data = json.loads(proc.stdout or "[]")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return {}

    entries = data if isinstance(data, list) else data.get("dependencies", [])
    result: Dict[str, List[str]] = {}
    for entry in entries:
        name = entry.get("name", "").lower()
        vulns = [v.get("id", "unknown") for v in entry.get("vulns", [])]
        if vulns:
            result[name] = vulns
    return result


def parse_requirements(repo_path: Path) -> Optional[Dict]:
    """Parses requirements.txt (the pip-only path for v1 — package.json,
    pom.xml, go.mod are the same shape and can be added the same way later)."""
    req_file = repo_path / "requirements.txt"
    if not req_file.exists():
        return None

    deps = []
    for line in req_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
        version = line.split("==")[1].strip() if "==" in line else None
        if name:
            deps.append({"name": name, "version": version, "vulnerabilities": []})

    vulnerable_by_name = run_pip_audit(req_file)
    for dep in deps:
        dep["vulnerabilities"] = vulnerable_by_name.get(dep["name"].lower(), [])

    return {
        "manifest": "requirements.txt",
        "total": len(deps),
        "dependencies": deps,
        "vulnerable_count": sum(1 for d in deps if d["vulnerabilities"]),
    }
