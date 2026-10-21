from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List


def run_ruff_linter(repo_path: Path) -> List[Dict]:
    """Run Ruff across the repository to detect real syntax errors, undefined
    variables, and common runtime bugs. Falls back to [] if ruff is not installed."""
    ruff_bin = shutil.which("ruff") or str(Path(__file__).resolve().parents[2] / "env" / "bin" / "ruff")
    if not Path(ruff_bin).exists() and not shutil.which(ruff_bin):
        return []

    try:
        proc = subprocess.run(
            [
                ruff_bin,
                "check",
                str(repo_path),
                "--output-format=json",
                # Select errors (E), pyflakes bugs/undefined names (F), flake8-bugbear (B), warnings (W)
                "--select=E,F,B,W",
                # Ignore noise directories
                "--exclude",
                ".git,node_modules,venv,.venv,__pycache__,dist,build",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        raw_output = proc.stdout.strip()
        if not raw_output:
            return []
        data = json.loads(raw_output)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError, OSError):
        return []

    issues: List[Dict] = []
    for item in data:
        code = item.get("code", "")
        message = item.get("message", "")
        filename = item.get("filename", "")
        location = item.get("location", {})
        line = location.get("row", 1)

        try:
            rel = str(Path(filename).relative_to(repo_path))
        except ValueError:
            rel = filename

        # Classify severity and category based on rule prefix
        if code.startswith("E9") or code in {"F821", "F822", "F823", "F701", "F702", "F704", "F706"}:
            severity = "CRITICAL"
            category = "syntax" if code.startswith("E9") else "bug"
            suggestion = f"Fix {code}: Fix the broken syntax or undefined variable before executing this code."
        elif code.startswith("B") or code.startswith("F6"):
            severity = "HIGH"
            category = "bug"
            suggestion = f"Fix {code}: Resolve bug pattern ({message})."
        elif code.startswith("F401") or code.startswith("F841"):
            severity = "LOW"
            category = "quality"
            suggestion = f"Clean up {code}: Remove unused import or variable to improve code cleanliness."
        else:
            severity = "MEDIUM"
            category = "quality"
            suggestion = f"Rule {code}: {message}"

        issues.append({
            "severity": severity,
            "category": category,
            "file": rel,
            "line": line,
            "message": f"[{code}] {message}",
            "suggestion": suggestion,
        })

    return issues
