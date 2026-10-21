import tempfile
from pathlib import Path

from backend.app.services.evidence import build_evidence


def test_build_evidence_full_pipeline():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir)

        # 1. Create a Python file with a real syntax error
        broken_py = repo_path / "broken.py"
        broken_py.write_text("def broken_syntax(\n    return 10\n", encoding="utf-8")

        # 2. Create a Python file with a mutable default argument
        valid_py = repo_path / "app.py"
        valid_py.write_text(
            "def handler(req, cache={}):\n"
            "    return cache.get(req)\n",
            encoding="utf-8",
        )

        # 3. Create a broken JSON config
        bad_json = repo_path / "config.json"
        bad_json.write_text('{"env": "prod", }', encoding="utf-8")

        # 4. Create a JS file with an anti-pattern
        bad_js = repo_path / "client.js"
        bad_js.write_text("if (val === NaN) { debugger; }\n", encoding="utf-8")

        # 5. Create a file with a secret
        secret_file = repo_path / ".env"
        secret_file.write_text("AWS_KEY=AKIA1234567890ABCDEF\n", encoding="utf-8")

        # Run the complete evidence pipeline
        result = build_evidence(repo_path, "test_repo")

        # Verify findings
        assert "overview" in result
        assert "issues" in result
        assert "security" in result
        assert "health" in result

        issues = result["issues"]
        security = result["security"]

        # Verify SyntaxError is caught
        assert any(i["category"] == "syntax" for i in issues)

        # Verify JSON syntax error is caught
        assert any("Invalid JSON syntax" in i["message"] for i in issues)

        # Verify JS issues are caught
        assert any("NaN" in i["message"] or "debugger" in i["message"] for i in issues)

        # Verify secret leak is caught
        assert any("AWS Access Key" in s["issue"] for s in security)

        # Verify health scores calculated
        assert result["health"]["code_quality"] <= 95
        assert result["health"]["security"] <= 95
