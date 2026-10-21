from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__",
    "dist", "build", ".mypy_cache", ".pytest_cache", "site-packages",
}

SECRET_RULES = [
    {
        "name": "AWS Access Key",
        "pattern": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "severity": "CRITICAL",
        "suggestion": "Revoke this AWS Access Key immediately and store credentials in environment variables or a secrets manager.",
    },
    {
        "name": "GitHub Token",
        "pattern": re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{36,255})\b"),
        "severity": "CRITICAL",
        "suggestion": "Revoke this GitHub personal access token and remove it from git history.",
    },
    {
        "name": "OpenAI API Key",
        "pattern": re.compile(r"\b(sk-[A-Za-z0-9_-]{20,64})\b"),
        "severity": "CRITICAL",
        "suggestion": "Revoke this OpenAI API key immediately and load it via environment variables.",
    },
    {
        "name": "Private Key",
        "pattern": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        "severity": "CRITICAL",
        "suggestion": "Remove private key file from repository and rotate affected SSH/encryption credentials.",
    },
    {
        "name": "Slack Webhook / Token",
        "pattern": re.compile(r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+|xox[baprs]-[0-9a-zA-Z]{10,48}"),
        "severity": "HIGH",
        "suggestion": "Revoke exposed Slack credentials and configure webhooks via environment variables.",
    },
    {
        "name": "Stripe Live API Key",
        "pattern": re.compile(r"\b(sk_live_[0-9a-zA-Z]{24,32})\b"),
        "severity": "CRITICAL",
        "suggestion": "Revoke live Stripe key immediately in the Stripe dashboard to prevent unauthorized transactions.",
    },
]


def _mask_secret(val: str) -> str:
    if len(val) <= 8:
        return "********"
    return val[:4] + "*" * (len(val) - 8) + val[-4:]


def scan_secrets(repo_path: Path) -> List[Dict]:
    """Scans repository files for committed credentials, API keys, and private keys."""
    findings: List[Dict] = []

    for path in repo_path.rglob("*"):
        if path.is_dir() or any(part in IGNORE_DIRS for part in path.parts):
            continue

        # Skip binary files, lockfiles, minified files, images
        if path.suffix in {".png", ".jpg", ".jpeg", ".ico", ".svg", ".lock", ".min.js", ".bin", ".pyc"}:
            continue

        try:
            rel = str(path.relative_to(repo_path))
        except ValueError:
            rel = str(path)

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    # Skip common test/example dummy keys
                    if "example" in line.lower() or "your_key" in line.lower() or "placeholder" in line.lower():
                        continue

                    for rule in SECRET_RULES:
                        match = rule["pattern"].search(line)
                        if match:
                            raw_val = match.group(0)
                            masked = _mask_secret(raw_val)
                            findings.append({
                                "severity": rule["severity"],
                                "file": rel,
                                "line": line_num,
                                "issue": f"Exposed {rule['name']}: {masked}",
                                "test_id": "SECRET_LEAK",
                                "suggestion": rule["suggestion"],
                            })
                            break
        except OSError:
            continue

    return findings
