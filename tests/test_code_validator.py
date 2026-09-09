import sys
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.services.code_validator import (
    CodeValidationError,
    detect_language,
    validate_is_code,
    normalize_code,
    validate_and_normalize_code,
)


def test_empty_code_validation():
    """Verify empty or whitespace-only code raises CodeValidationError."""
    with pytest.raises(CodeValidationError) as exc:
        validate_and_normalize_code("")
    assert "Code input cannot be empty" in str(exc.value.detail)

    with pytest.raises(CodeValidationError) as exc:
        validate_and_normalize_code("   \n\t  ")
    assert "Code input cannot be empty" in str(exc.value.detail)


def test_payload_size_limit():
    """Verify code > 50 KB raises CodeValidationError."""
    large_code = "x = 1\n" * 9000  # ~54 KB
    with pytest.raises(CodeValidationError) as exc:
        validate_and_normalize_code(large_code)
    assert "exceeds maximum limit of 50 KB" in str(exc.value.detail)


def test_natural_language_rejection():
    """Verify plain English prose without code markers is rejected."""
    prose = "This is a simple paragraph written in plain English to describe a system specification. It has no code markers or syntax."
    with pytest.raises(CodeValidationError) as exc:
        validate_and_normalize_code(prose)
    assert "does not appear to be valid program code" in str(exc.value.detail)


def test_language_detection_c_and_cpp():
    """Verify language detection for C and C++ snippets."""
    c_code = """
    #include <stdio.h>
    #include <stdlib.h>

    int main() {
        printf("Hello World\\n");
        return 0;
    }
    """
    assert detect_language(c_code) == "c"

    cpp_code = """
    #include <iostream>
    using namespace std;

    int main() {
        std::cout << "Hello C++" << std::endl;
        return 0;
    }
    """
    assert detect_language(cpp_code) == "cpp"


def test_language_detection_frameworks():
    """Verify framework detection for Django, React, Next.js, and Node.js."""
    django_code = """
    from django.db import models

    class UserProfile(models.Model):
        username = models.CharField(max_length=100)
    """
    assert detect_language(django_code) == "django"

    react_code = """
    import React, { useState } from 'react';

    export const Counter = () => {
        const [count, setCount] = useState(0);
        return <button onClick={() => setCount(count + 1)}>Count: {count}</button>;
    };
    """
    assert detect_language(react_code) == "react"

    nextjs_code = """
    'use client';
    import { useRouter } from 'next/navigation';

    export default function Dashboard() {
        const router = useRouter();
        return <div>Dashboard Page</div>;
    }
    """
    assert detect_language(nextjs_code) == "nextjs"

    nodejs_code = """
    const express = require('express');
    const app = express();

    app.get('/api', (req, res) => {
        res.json({ status: 'ok' });
    });
    """
    assert detect_language(nodejs_code) == "nodejs"


def test_language_detection_standard_languages():
    """Verify auto-detection for Python, JS, TS, Java, Go, Rust."""
    py_code = "def process_data(items):\n    return [item.strip() for item in items]"
    assert detect_language(py_code) == "python"

    ts_code = "interface User {\n    id: number;\n    name: string;\n}"
    assert detect_language(ts_code) == "typescript"

    java_code = "public class App {\n    public static void main(String[] args) {\n        System.out.println(\"Hi\");\n    }\n}"
    assert detect_language(java_code) == "java"

    go_code = "package main\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello\")\n}"
    assert detect_language(go_code) == "go"

    rust_code = "fn main() {\n    let mut x = 5;\n    println!(\"Val: {}\", x);\n}"
    assert detect_language(rust_code) == "rust"


def test_line_normalization_and_hash():
    """Verify CRLF normalization, SHA256 hashing, and 1-indexed line mapping."""
    raw_code = "def foo():\r\n    a = 10\r\n    return a\r\n"
    res = validate_and_normalize_code(raw_code, language="python")

    assert "\r" not in res.normalized_code
    assert res.line_count == 4
    assert res.line_mapping[1] == "def foo():"
    assert res.line_mapping[2] == "    a = 10"
    assert len(res.hash) == 64
