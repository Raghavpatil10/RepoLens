from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List


def run_bandit(repo_path: Path) -> List[Dict]:
    """Shell out to Bandit and normalize its JSON output. Returns [] on any
    failure (Bandit missing, timeout, no Python files) rather than raising —
    a broken security scan shouldn't break the whole report."""
    try:
        proc = subprocess.run(
            [
                "bandit", "-r", str(repo_path), "-f", "json", "-q",
                # Test suites routinely (and correctly) use assert/exec-like
                # patterns that aren't real findings in production code.
                "-x", "*/tests/*,*/test/*,*/venv/*,*/.venv/*,*/node_modules/*",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        data = json.loads(proc.stdout or "{}")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []

    findings = []
    for result in data.get("results", []):
        filename = result.get("filename", "")
        try:
            rel = str(Path(filename).relative_to(repo_path))
        except ValueError:
            rel = filename

        findings.append({
            "severity": result.get("issue_severity", "LOW"),
            "file": rel,
            "line": result.get("line_number"),
            "issue": result.get("issue_text", "").strip(),
            "test_id": result.get("test_id"),
        })
    return findings
