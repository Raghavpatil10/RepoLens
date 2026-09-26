from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .dependency_scan import parse_requirements
from .discovery import discover_files, language_breakdown
from .security_scan import run_bandit
from .static_analysis import analyze_python_file, maintainability_index


def build_evidence(repo_path: Path, project_name: str) -> Dict:
    """The single function the API route calls. Runs every analysis pass and
    returns one dict matching the AnalysisResult schema (minus ai_summary,
    which the route adds separately since it's an optional, slower step)."""
    files = discover_files(repo_path)
    languages = language_breakdown(files)

    all_issues: List[Dict] = []
    total_functions = 0
    total_classes = 0
    mi_scores: List[float] = []

    for f in files:
        if f["language"] != "Python":
            continue
        rel_path = str(f["path"].relative_to(repo_path))
        issues, counts = analyze_python_file(f["path"], rel_path)
        all_issues.extend(issues)
        total_functions += counts["functions"]
        total_classes += counts["classes"]
        try:
            source = f["path"].read_text(encoding="utf-8", errors="ignore")
            mi_scores.append(maintainability_index(source))
        except OSError:
            pass

    security_findings = run_bandit(repo_path)
    dependency_report = parse_requirements(repo_path)

    overview = {
        "project_name": project_name,
        "total_files": len(files),
        "total_lines": sum(f["loc"] for f in files),
        "total_functions": total_functions,
        "total_classes": total_classes,
        "languages": languages,
    }

    health = _score_health(
        all_issues, security_findings, dependency_report, mi_scores,
        total_lines=overview["total_lines"],
    )

    return {
        "overview": overview,
        "issues": all_issues,
        "security": security_findings,
        "dependencies": [dependency_report] if dependency_report else [],
        "health": health,
    }


def _score_health(
    issues: List[Dict],
    security_findings: List[Dict],
    dependency_report: Optional[Dict],
    mi_scores: List[float],
    total_lines: int,
) -> Dict:
    """Deliberately simple, explainable scoring — penalty points subtracted
    from 100, not a black-box 'AI score'. Tune the weights as you learn more
    about what actually correlates with real-world quality.

    Penalties are normalized per 1,000 lines of code so that a bigger repo
    doesn't automatically score worse just for having more surface area —
    without this, raw issue counts crush the score to 0 on any real project."""

    def clamp(v: float) -> int:
        return max(0, min(100, round(v)))

    kloc = max(total_lines / 1000, 1.0)

    quality_weight = sum(
        3 if i["severity"] == "HIGH" else 1
        for i in issues if i["category"] in ("quality", "complexity")
    )
    perf_weight = sum(
        4 if i["severity"] == "HIGH" else 1.5
        for i in issues if i["category"] == "performance"
    )
    sec_weight = sum(
        4 if s["severity"] == "HIGH" else (2 if s["severity"] == "MEDIUM" else 0.5)
        for s in security_findings
    )
    dep_weight = dependency_report["vulnerable_count"] * 6 if dependency_report else 0

    quality_penalty = min(60, (quality_weight / kloc) * 8)
    perf_penalty = min(60, (perf_weight / kloc) * 8)
    sec_penalty = min(70, (sec_weight / kloc) * 8 + dep_weight)

    maintainability = clamp(sum(mi_scores) / len(mi_scores)) if mi_scores else 60

    return {
        "code_quality": clamp(95 - quality_penalty),
        "security": clamp(95 - sec_penalty),
        "performance": clamp(95 - perf_penalty),
        "maintainability": maintainability,
        # Placeholder until a docstring/README-coverage pass is added (see README "Next steps").
        "documentation": 50,
    }
