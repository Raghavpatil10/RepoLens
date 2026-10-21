from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import yaml

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__",
    "dist", "build", ".mypy_cache", ".pytest_cache", "site-packages",
}


def validate_config_files(repo_path: Path) -> List[Dict]:
    """Validates syntax of JSON and YAML configuration files across the repository."""
    issues: List[Dict] = []

    for path in repo_path.rglob("*"):
        if path.is_dir() or any(part in IGNORE_DIRS for part in path.parts):
            continue

        try:
            rel = str(path.relative_to(repo_path))
        except ValueError:
            rel = str(path)

        # Validate JSON files
        if path.suffix.lower() == ".json":
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                json.loads(content)
            except json.JSONDecodeError as err:
                issues.append({
                    "severity": "CRITICAL",
                    "category": "syntax",
                    "file": rel,
                    "line": err.lineno,
                    "message": f"Invalid JSON syntax: {err.msg}",
                    "suggestion": f"Check line {err.lineno}, column {err.colno}. Ensure valid JSON without trailing commas.",
                })
            except OSError:
                pass

        # Validate YAML files
        elif path.suffix.lower() in {".yaml", ".yml"}:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                yaml.safe_load(content)
            except yaml.YAMLError as err:
                line = 1
                if hasattr(err, "problem_mark") and err.problem_mark:
                    line = err.problem_mark.line + 1
                issues.append({
                    "severity": "CRITICAL",
                    "category": "syntax",
                    "file": rel,
                    "line": line,
                    "message": f"Invalid YAML syntax: {getattr(err, 'problem', str(err))}",
                    "suggestion": "Fix YAML indentation or syntax error to prevent CI/CD workflow and configuration failures.",
                })
            except OSError:
                pass

    return issues
