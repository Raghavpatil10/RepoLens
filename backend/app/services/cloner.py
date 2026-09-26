from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from git import Repo


class ClonedRepo:
    """Context manager: shallow-clones a public repo to a temp dir and
    guarantees cleanup afterwards, even if analysis raises an exception.

    Usage:
        with ClonedRepo(url) as path:
            ... do analysis on `path` ...
    """

    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.tmp_dir: str | None = None

    def __enter__(self) -> Path:
        self.tmp_dir = tempfile.mkdtemp(prefix="repolens_")
        Repo.clone_from(self.repo_url, self.tmp_dir, depth=1)
        return Path(self.tmp_dir)

    def __exit__(self, exc_type, exc, tb):
        if self.tmp_dir:
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
        return False
