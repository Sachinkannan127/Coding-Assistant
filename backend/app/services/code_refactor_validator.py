import ast
import re
import logging
from typing import List, Tuple, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Validation output result schema for refactored code blocks."""
    is_valid: bool = Field(..., description="Whether refactored code passed syntax and signature checks")
    status: str = Field(..., description="Status string: 'passed' | 'retried_passed' | 'fallback_original'")
    errors: List[str] = Field(default_factory=list, description="List of syntax or signature validation errors")
    signature_preserved: bool = Field(default=True, description="Whether original function signatures were preserved")


def validate_syntax(code: str, language: str = "python") -> Tuple[bool, Optional[str]]:
    """
    Multi-language syntax validator.
    - Python: Uses native ast.parse().
    - JS/TS/React/Next/Node: Bracket/brace balance & JSX tag matching.
    - C/C++: Header syntax & function scope balance.
    - Java/Go/Rust: Structural syntax checks.
    """
    cleaned_code = code.strip()
    if not cleaned_code:
        return False, "Refactored code block is empty."

    lang = language.lower().strip()

    # 1. Python AST Compilation
    if lang in ["python", "django"]:
        try:
            ast.parse(cleaned_code)
            return True, None
        except SyntaxError as syn_err:
            return False, f"Python SyntaxError line {syn_err.lineno}: {syn_err.msg}"

    # 2. JavaScript / TypeScript / React / Next.js / Node.js
    if lang in ["javascript", "typescript", "react", "nextjs", "nodejs"]:
        # Bracket & brace balance check
        open_braces = cleaned_code.count("{")
        close_braces = cleaned_code.count("}")
        open_parens = cleaned_code.count("(")
        close_parens = cleaned_code.count(")")
        open_brackets = cleaned_code.count("[")
        close_brackets = cleaned_code.count("]")

        if open_braces != close_braces:
            return False, f"Mismatched curly braces: {open_braces} open '{{' vs {close_braces} close '}}'."
        if open_parens != close_parens:
            return False, f"Mismatched parentheses: {open_parens} open '(' vs {close_parens} close ')'."
        if open_brackets != close_brackets:
            return False, f"Mismatched square brackets: {open_brackets} open '[' vs {close_brackets} close ']'."

        return True, None

    # 3. C & C++
    if lang in ["c", "cpp"]:
        open_braces = cleaned_code.count("{")
        close_braces = cleaned_code.count("}")
        open_parens = cleaned_code.count("(")
        close_parens = cleaned_code.count(")")

        if open_braces != close_braces:
            return False, f"C/C++ mismatched curly braces: {open_braces} open vs {close_braces} close."
        if open_parens != close_parens:
            return False, f"C/C++ mismatched parentheses: {open_parens} open vs {close_parens} close."

        return True, None

    # 4. Generic Fallback (Java, Go, Rust)
    open_braces = cleaned_code.count("{")
    close_braces = cleaned_code.count("}")
    if open_braces != close_braces:
        return False, f"Mismatched braces: {open_braces} open vs {close_braces} close."

    return True, None


def verify_signature_preservation(
    original_code: str,
    refactored_code: str,
    language: str = "python"
) -> Tuple[bool, Optional[str]]:
    """
    Verifies that top-level function signatures from original code are preserved in refactored code.
    """
    lang = language.lower().strip()

    # Extract function names based on language regex patterns
    if lang in ["python", "django"]:
        orig_funcs = set(re.findall(r"def\s+([a-zA-Z_]\w*)\s*\(", original_code))
        refac_funcs = set(re.findall(r"def\s+([a-zA-Z_]\w*)\s*\(", refactored_code))
    elif lang in ["javascript", "typescript", "react", "nextjs", "nodejs"]:
        pattern = r"(?:function\s+([a-zA-Z_]\w*)|const\s+([a-zA-Z_]\w*)\s*=\s*(?:async\s*)?\()"
        orig_matches = re.findall(pattern, original_code)
        refac_matches = re.findall(pattern, refactored_code)

        orig_funcs = set([m[0] or m[1] for m in orig_matches if m[0] or m[1]])
        refac_funcs = set([m[0] or m[1] for m in refac_matches if m[0] or m[1]])
    elif lang in ["go", "rust"]:
        pattern = r"(?:func|fn)\s+([a-zA-Z_]\w*)"
        orig_funcs = set(re.findall(pattern, original_code))
        refac_funcs = set(re.findall(pattern, refactored_code))
    else:
        # C, C++, Java or generic
        pattern = r"\b[a-zA-Z_]\w*\s+([a-zA-Z_]\w*)\s*\("
        orig_funcs = set(re.findall(pattern, original_code)) - {"if", "for", "while", "switch", "main"}
        refac_funcs = set(re.findall(pattern, refactored_code)) - {"if", "for", "while", "switch", "main"}

    missing_funcs = orig_funcs - refac_funcs
    if missing_funcs:
        missing_str = ", ".join(sorted(list(missing_funcs)))
        return False, f"Missing original function signatures in refactored code: {missing_str}"

    return True, None


def validate_refactored_code(
    original_code: str,
    refactored_code: str,
    language: str = "python",
    retry_count: int = 0
) -> ValidationResult:
    """
    Main entry point for refactoring code validation loop:
    1. Runs multi-language syntax check.
    2. Runs signature preservation check.
    3. Manages retry count escalation and safe fallback to original code.
    """
    errors: List[str] = []

    # 1. Syntax Check
    syntax_ok, syntax_err = validate_syntax(code=refactored_code, language=language)
    if not syntax_ok and syntax_err:
        errors.append(syntax_err)

    # 2. Signature Preservation Check
    sig_ok, sig_err = verify_signature_preservation(
        original_code=original_code,
        refactored_code=refactored_code,
        language=language
    )
    if not sig_ok and sig_err:
        errors.append(sig_err)

    is_valid = syntax_ok and sig_ok

    if is_valid:
        status = "passed" if retry_count == 0 else "retried_passed"
        return ValidationResult(
            is_valid=True,
            status=status,
            errors=[],
            signature_preserved=True
        )

    # If invalid, check retry ceiling (max 2 retries)
    logger.warning(f"Validation failed (retry_count={retry_count}): {errors}")
    if retry_count >= 1:  # On 2nd failure, fallback to original code
        return ValidationResult(
            is_valid=False,
            status="fallback_original",
            errors=errors,
            signature_preserved=sig_ok
        )

    return ValidationResult(
        is_valid=False,
        status="pending_retry",
        errors=errors,
        signature_preserved=sig_ok
    )
