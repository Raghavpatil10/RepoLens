from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Tuple

from radon.complexity import cc_visit
from radon.metrics import mi_visit

LONG_FUNCTION_THRESHOLD = 50
MAX_NESTED_LOOP_DEPTH = 3
DB_CALL_HINTS = {"query", "get", "find", "select", "fetch", "filter", "execute"}


def _nested_loop_depth(node: ast.AST, depth: int = 0) -> int:
    max_depth = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While)):
            max_depth = max(max_depth, _nested_loop_depth(child, depth + 1))
        else:
            max_depth = max(max_depth, _nested_loop_depth(child, depth))
    return max_depth


def _calls_in_loop(loop_node: ast.AST) -> List[str]:
    hits = []
    for child in ast.walk(loop_node):
        if isinstance(child, ast.Call):
            name = getattr(child.func, "attr", None) or getattr(child.func, "id", None)
            if name and any(hint in name.lower() for hint in DB_CALL_HINTS):
                hits.append(name)
    return hits


def analyze_python_file(path: Path, rel_path: str) -> Tuple[List[Dict], Dict]:
    """Returns (issues, counts) for a single Python file. Never raises —
    a file that fails to parse just contributes zero issues/counts."""
    issues: List[Dict] = []
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, OSError):
        return issues, {"functions": 0, "classes": 0}

    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    for fn in functions:
        end_line = fn.end_lineno or fn.lineno
        length = end_line - fn.lineno
        if length > LONG_FUNCTION_THRESHOLD:
            issues.append({
                "severity": "MEDIUM",
                "category": "quality",
                "file": rel_path,
                "line": fn.lineno,
                "func_start_line": fn.lineno,
                "func_end_line": end_line,
                "message": f"Function '{fn.name}' is {length} lines long.",
                "suggestion": "Split into smaller functions with single responsibilities.",
            })

        depth = _nested_loop_depth(fn)
        if depth >= MAX_NESTED_LOOP_DEPTH:
            issues.append({
                "severity": "MEDIUM",
                "category": "performance",
                "file": rel_path,
                "line": fn.lineno,
                "func_start_line": fn.lineno,
                "func_end_line": end_line,
                "message": f"Function '{fn.name}' has {depth} levels of nested loops.",
                "suggestion": "Consider a hash-map based lookup to flatten the nesting.",
            })

    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            hits = _calls_in_loop(node)
            if hits:
                unique_hits = ", ".join(sorted(set(hits)))
                issues.append({
                    "severity": "HIGH",
                    "category": "performance",
                    "file": rel_path,
                    "line": node.lineno,
                    "message": f"Possible query-in-loop pattern ({unique_hits}) at line {node.lineno}.",
                    "suggestion": "Batch the calls before iterating instead of one call per item.",
                })

    try:
        for block in cc_visit(source):
            if block.complexity >= 10:
                issues.append({
                    "severity": "HIGH" if block.complexity >= 15 else "MEDIUM",
                    "category": "complexity",
                    "file": rel_path,
                    "line": block.lineno,
                    "func_start_line": block.lineno,
                    "func_end_line": getattr(block, "endline", None) or block.lineno,
                    "message": f"'{block.name}' has cyclomatic complexity {block.complexity}.",
                    "suggestion": "Break the branching logic into smaller helper functions.",
                })
    except Exception:
        pass  # radon failing on odd syntax shouldn't take down the whole scan

    return issues, {"functions": len(functions), "classes": len(classes)}


def maintainability_index(source: str) -> float:
    try:
        return mi_visit(source, multi=True)
    except Exception:
        return 60.0
