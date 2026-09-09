import sys
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.services.code_refactor_validator import (
    validate_syntax,
    verify_signature_preservation,
    validate_refactored_code,
)


def test_python_ast_syntax_validation():
    """Verify Python AST syntax validation for valid and invalid snippets."""
    valid_py = "def calculate(a, b):\n    return a + b\n"
    ok, err = validate_syntax(valid_py, language="python")
    assert ok is True
    assert err is None

    invalid_py = "def calculate(a, b:\n    return a + b\n"
    ok, err = validate_syntax(invalid_py, language="python")
    assert ok is False
    assert "SyntaxError" in err


def test_js_cpp_bracket_validation():
    """Verify JS/React/C++ bracket balance syntax validation."""
    valid_js = "const add = (a, b) => { return a + b; };"
    ok, err = validate_syntax(valid_js, language="javascript")
    assert ok is True

    invalid_js = "const add = (a, b) => { return a + b;"
    ok, err = validate_syntax(invalid_js, language="javascript")
    assert ok is False
    assert "curly braces" in err


def test_signature_preservation():
    """Verify function signature preservation check."""
    orig = "def process_data(items):\n    pass\ndef save_result(res):\n    pass\n"
    valid_refac = "def process_data(items):\n    return True\ndef save_result(res):\n    return True\n"
    invalid_refac = "def process_data(items):\n    return True\n"

    ok, err = verify_signature_preservation(orig, valid_refac, language="python")
    assert ok is True
    assert err is None

    ok, err = verify_signature_preservation(orig, invalid_refac, language="python")
    assert ok is False
    assert "save_result" in err


def test_validate_refactored_code_retry_fallback():
    """Verify retry escalation and fallback to original code on repeated failure."""
    orig = "def run():\n    pass\n"
    invalid_refac = "def run(:\n    pass\n"

    # Retry 0: pending_retry
    res0 = validate_refactored_code(orig, invalid_refac, language="python", retry_count=0)
    assert res0.is_valid is False
    assert res0.status == "pending_retry"

    # Retry 1: fallback_original
    res1 = validate_refactored_code(orig, invalid_refac, language="python", retry_count=1)
    assert res1.is_valid is False
    assert res1.status == "fallback_original"
