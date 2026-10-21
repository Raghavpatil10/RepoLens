from __future__ import annotations

import json
import os
from typing import Dict, Optional

import anthropic

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "You are a principal software engineer reviewing an automated repository audit report. "
    "You will receive structured JSON findings containing syntax errors, linter bugs, secret leaks, "
    "Bandit security vulnerabilities, and dependency CVEs. "
    "Write a concise executive summary (3-5 bullet points) covering: "
    "1. Critical blocking errors (syntax errors, undefined variables, leaked credentials) that break execution or compromise security. "
    "2. High-priority logic bugs and security vulnerabilities. "
    "3. Key actionable recommendations to fix immediately. "
    "Be direct, specific, and reference exact filenames and line numbers when present."
)


def _generate_fallback_summary(evidence: Dict) -> str:
    """Generates a concise deterministic summary when ANTHROPIC_API_KEY is not configured."""
    issues = evidence.get("issues", [])
    security = evidence.get("security", [])
    health = evidence.get("health", {})

    critical_syntax = [i for i in issues if i.get("category") == "syntax" or i.get("severity") == "CRITICAL"]
    critical_bugs = [i for i in issues if i.get("category") == "bug" and i.get("severity") in {"CRITICAL", "HIGH"}]
    secret_leaks = [s for s in security if s.get("test_id") == "SECRET_LEAK" or s.get("severity") == "CRITICAL"]

    bullets = []
    if critical_syntax:
        bullets.append(f"CRITICAL SYNTAX: Found {len(critical_syntax)} syntax error(s) preventing files from executing (e.g. {critical_syntax[0]['file']}: line {critical_syntax[0].get('line', '?')}).")
    if secret_leaks:
        bullets.append(f"SECURITY ALERT: Detected {len(secret_leaks)} exposed secret(s) or high-severity security vulnerabilities.")
    if critical_bugs:
        bullets.append(f"RUNTIME BUGS: Identified {len(critical_bugs)} high-confidence bug(s) such as undefined variables or dangerous patterns.")

    if not bullets:
        bullets.append(f"REPOSITORY HEALTH: Overall health is strong with quality score {health.get('code_quality', 100)}/100 and no blocking syntax errors.")

    bullets.append(f"AUDIT SUMMARY: Scanned {evidence.get('overview', {}).get('total_files', 0)} files ({evidence.get('overview', {}).get('total_lines', 0)} lines of code). Review detailed cards below.")
    return "\n• " + "\n• ".join(bullets)


def explain_findings(evidence: Dict) -> Optional[str]:
    """Returns an executive technical summary. Calls Claude if ANTHROPIC_API_KEY
    is set, or produces a deterministic report summary based on detected findings."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _generate_fallback_summary(evidence)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(evidence, default=str)}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
    except Exception:
        return _generate_fallback_summary(evidence)

