from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import AnalysisResult, RepoRequest
from ..services.ai_explainer import explain_findings
from ..services.cloner import ClonedRepo
from ..services.evidence import build_evidence

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult)
def analyze_repo(request: RepoRequest) -> dict:
    project_name = request.repo_url.rstrip("/").split("/")[-1].removesuffix(".git")

    try:
        with ClonedRepo(request.repo_url) as repo_path:
            evidence = build_evidence(repo_path, project_name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not analyze repository: {exc}")

    evidence["ai_summary"] = explain_findings(evidence)
    return evidence
