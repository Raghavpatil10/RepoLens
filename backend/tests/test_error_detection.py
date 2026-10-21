import ast
import tempfile
from pathlib import Path

from backend.app.services.config_validator import validate_config_files
from backend.app.services.js_ts_analysis import analyze_js_ts_file
from backend.app.services.secret_scan import scan_secrets
from backend.app.services.static_analysis import analyze_python_file


def test_syntax_error_reported_as_critical():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        broken_file = tmp_path / "broken.py"
        broken_file.write_text("def invalid_syntax(\n    return 42\n", encoding="utf-8")

        issues, counts = analyze_python_file(broken_file, "broken.py")
        assert len(issues) >= 1
        assert any(i["severity"] == "CRITICAL" and i["category"] == "syntax" for i in issues)
        assert any("SyntaxError" in i["message"] for i in issues)


def test_mutable_default_argument_detected():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        py_file = tmp_path / "mutable_test.py"
        py_file.write_text("def add_item(item, items=[]):\n    items.append(item)\n    return items\n", encoding="utf-8")

        issues, _ = analyze_python_file(py_file, "mutable_test.py")
        assert any(i["category"] == "bug" and "Mutable default argument" in i["message"] for i in issues)


def test_unreachable_code_detected():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        py_file = tmp_path / "unreachable.py"
        py_file.write_text("def calc(a):\n    return a * 2\n    print('never reached')\n", encoding="utf-8")

        issues, _ = analyze_python_file(py_file, "unreachable.py")
        assert any(i["category"] == "bug" and "Unreachable statement" in i["message"] for i in issues)


def test_duplicate_dict_keys_detected():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        py_file = tmp_path / "dup_keys.py"
        py_file.write_text("config = {'host': 'localhost', 'port': 8000, 'host': '127.0.0.1'}\n", encoding="utf-8")

        issues, _ = analyze_python_file(py_file, "dup_keys.py")
        assert any(i["category"] == "bug" and "Duplicate dictionary key" in i["message"] for i in issues)


def test_bare_except_detected():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        py_file = tmp_path / "bare_except.py"
        py_file.write_text("try:\n    x = 1 / 0\nexcept:\n    pass\n", encoding="utf-8")

        issues, _ = analyze_python_file(py_file, "bare_except.py")
        assert any(i["category"] == "bug" and "Dangerous bare 'except:'" in i["message"] for i in issues)


def test_secret_scanner_detects_keys():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_KEY=sk-abcdef1234567890abcdef1234567890\n", encoding="utf-8")

        findings = scan_secrets(tmp_path)
        assert len(findings) >= 1
        assert any("OpenAI API Key" in f["issue"] for f in findings)


def test_config_validator_detects_invalid_json():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        bad_json = tmp_path / "package.json"
        bad_json.write_text('{"name": "test", "version": "1.0.0", }', encoding="utf-8")  # trailing comma

        issues = validate_config_files(tmp_path)
        assert len(issues) >= 1
        assert any("Invalid JSON syntax" in i["message"] for i in issues)


def test_js_analysis_detects_nan_comparison():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        js_file = tmp_path / "app.js"
        js_file.write_text("if (val === NaN) { console.log('bad'); }\n", encoding="utf-8")

        issues = analyze_js_ts_file(js_file, "app.js")
        assert len(issues) >= 1
        assert any("Comparison with NaN" in i["message"] for i in issues)
