from __future__ import annotations

import json
import os
from typing import Dict, Optional

import anthropic

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "You are a senior software engineer reviewing a static-analysis report for "
    "another developer. You will be given structured JSON evidence produced by "
    "deterministic tools (AST analysis, Bandit, pip-audit) — not raw source code. "
    "Write a plain-language summary, 4-6 sentences, covering: overall health, the "
    "2-3 most important issues to fix first, and why they matter. Only use facts "
    "present in the JSON — never invent file names, line numbers, or issues that "
    "aren't there."
)


def explain_findings(evidence: Dict) -> Optional[str]:
    """Returns a short natural-language summary, or None if no API key is set
    or the call fails — the rest of the report works fine without this."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(evidence, default=str)}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
    except Exception:
        # Network issues, rate limits, bad key, etc. — degrade gracefully.
        return None
