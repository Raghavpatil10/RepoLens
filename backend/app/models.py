from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class RepoRequest(BaseModel):
    repo_url: str


class LanguageBreakdown(BaseModel):
    language: str
    percentage: float
    files: int


class ProjectOverview(BaseModel):
    project_name: str
    total_files: int
    total_lines: int
    total_functions: int
    total_classes: int
    languages: List[LanguageBreakdown]


class CodeIssue(BaseModel):
    severity: str  # HIGH, MEDIUM, LOW
    category: str  # performance, quality, complexity
    file: str
    line: Optional[int] = None
    message: str
    suggestion: Optional[str] = None


class SecurityFinding(BaseModel):
    severity: str
    file: str
    line: Optional[int] = None
    issue: str
    test_id: Optional[str] = None


class Dependency(BaseModel):
    name: str
    version: Optional[str] = None
    vulnerabilities: List[str] = []


class DependencyReport(BaseModel):
    manifest: str
    total: int
    dependencies: List[Dependency]
    vulnerable_count: int


class HealthScores(BaseModel):
    code_quality: int
    security: int
    performance: int
    maintainability: int
    documentation: int


class AnalysisResult(BaseModel):
    overview: ProjectOverview
    issues: List[CodeIssue]
    security: List[SecurityFinding]
    dependencies: List[DependencyReport]
    health: HealthScores
    ai_summary: Optional[str] = None
