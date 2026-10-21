from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

JS_TS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

JS_PATTERNS = [
    {
        "pattern": re.compile(r"\bdebugger\s*;?"),
        "severity": "HIGH",
        "category": "bug",
        "message": "Leftover 'debugger' statement.",
        "suggestion": "Remove debugger statement before deploying to avoid freezing execution in production.",
    },
    {
        "pattern": re.compile(r"(?:===|==|!==|!=)\s*NaN\b|\bNaN\s*(?:===|==|!==|!=)"),
        "severity": "HIGH",
        "category": "bug",
        "message": "Comparison with NaN is always false/true in JavaScript.",
        "suggestion": "Use 'Number.isNaN(val)' instead of direct equality comparison with NaN.",
    },
    {
        "pattern": re.compile(r"\beval\s*\("),
        "severity": "HIGH",
        "category": "security",
        "message": "Use of 'eval()' allows arbitrary code execution.",
        "suggestion": "Avoid eval(). Use JSON.parse() or structured parsing instead.",
    },
    {
        "pattern": re.compile(r"\bdocument\.write\s*\("),
        "severity": "MEDIUM",
        "category": "performance",
        "message": "Use of 'document.write()' can block page rendering.",
        "suggestion": "Use modern DOM manipulation APIs or virtual DOM rendering instead.",
    },
]


def analyze_js_ts_file(path: Path, rel_path: str) -> List[Dict]:
    """Scans a JavaScript or TypeScript file for common bugs and security issues."""
    issues: List[Dict] = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                clean_line = line.strip()
                if clean_line.startswith("//") or clean_line.startswith("/*") or clean_line.startswith("*"):
                    continue

                for rule in JS_PATTERNS:
                    if rule["pattern"].search(line):
                        issues.append({
                            "severity": rule["severity"],
                            "category": rule["category"],
                            "file": rel_path,
                            "line": line_num,
                            "message": rule["message"],
                            "suggestion": rule["suggestion"],
                        })
    except OSError:
        pass

    return issues
