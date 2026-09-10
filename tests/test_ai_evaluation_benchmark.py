import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from backend.app.services.eval_service import (
    eval_service,
    BenchmarkSample,
    GroundTruthFinding,
    EvaluationSummary
)
from backend.app.services.review_service import ReviewService
from backend.app.services.llm.router import LLMRouter, LLMResponse


def test_eval_finding_match_precision_recall():
    """Verify precision, recall, and F1 score calculation logic in eval_service."""
    gt = GroundTruthFinding(
        category="bug",
        cwe_or_rule_id="CWE-476",
        line_start=2,
        keywords=["user", "null", "profile"]
    )
    sample = BenchmarkSample(
        sample_id="test-001",
        language="python",
        code="def foo(user): return user.profile.name",
        expected_findings=[gt]
    )

    pred_match = {
        "category": "bug",
        "title": "Null pointer dereference",
        "description": "Variable user profile may be null",
        "cwe_or_rule_id": "CWE-476"
    }

    pred_unrelated = {
        "category": "quality",
        "title": "Missing docstring",
        "description": "Function lacks documentation",
        "cwe_or_rule_id": "STYLE-001"
    }

    # Match check
    assert eval_service.evaluate_finding_match(pred_match, gt) is True
    assert eval_service.evaluate_finding_match(pred_unrelated, gt) is False

    # Sample metrics calculation
    review_output = {
        "findings": [pred_match, pred_unrelated],
        "refactoring": {"refactored_code": "def foo(user):\n    if user: return user.profile.name", "validation_status": "passed"}
    }

    sample_metrics = eval_service.compute_sample_metrics(sample, review_output, latency_ms=1200.0)
    assert sample_metrics["true_positives"] == 1
    assert sample_metrics["false_positives"] == 1
    assert sample_metrics["false_negatives"] == 0
    assert sample_metrics["ast_valid"] is True

    # Aggregate metrics
    summary = eval_service.aggregate_metrics([sample_metrics])
    assert isinstance(summary, EvaluationSummary)
    assert summary.total_samples == 1
    assert summary.precision_recall.precision == 0.5
    assert summary.precision_recall.recall == 1.0
    assert summary.ast_validation_pass_rate == 100.0
    assert summary.sla_compliance_rate == 100.0


def test_ast_validation_rates():
    """Verify AST syntax validation rates across multiple languages."""
    py_sample = BenchmarkSample(
        sample_id="py-test",
        language="python",
        code="def bar(): return 1",
        expected_valid_refactor=True
    )
    
    # Valid Python refactor
    py_res_valid = {"findings": [], "refactoring": {"refactored_code": "def bar():\n    return 1"}}
    m1 = eval_service.compute_sample_metrics(py_sample, py_res_valid, latency_ms=500.0)
    assert m1["ast_valid"] is True

    # Invalid Python refactor (syntax error)
    py_res_invalid = {"findings": [], "refactoring": {"refactored_code": "def bar() return 1"}}
    m2 = eval_service.compute_sample_metrics(py_sample, py_res_invalid, latency_ms=500.0)
    assert m2["ast_valid"] is False


def test_sla_latency_compliance():
    """Verify target latency SLA compliance checks."""
    quick_sample = BenchmarkSample(
        sample_id="quick-sla",
        language="python",
        code="x = 1",
        expected_mode="quick",
        target_max_latency_ms=10000.0
    )

    res = {"findings": [], "refactoring": {"refactored_code": "x = 1"}}
    
    # Under SLA (5s < 10s)
    m_pass = eval_service.compute_sample_metrics(quick_sample, res, latency_ms=5000.0)
    assert m_pass["sla_compliant"] is True

    # Over SLA (15s > 10s)
    m_fail = eval_service.compute_sample_metrics(quick_sample, res, latency_ms=15000.0)
    assert m_fail["sla_compliant"] is False


@pytest.mark.asyncio
async def test_fallback_resilience_offline_db():
    """Verify review_service gracefully completes review when MongoDB persistence fails."""
    mock_repo = MagicMock()
    mock_repo.create_review = AsyncMock(side_effect=Exception("Database Connection Error"))

    srv = ReviewService(repo=mock_repo)

    with patch("backend.app.services.review_service.run_review_workflow", new=AsyncMock(return_value={
        "overview": "Offline DB Fallback Test",
        "verdict": "clean",
        "findings": [],
        "refactored_code": "def foo(): pass"
    })):
        res = await srv.run_review(code="def foo(): pass", language="python", mode="quick")

    assert res["summary"]["overview"] == "Offline DB Fallback Test"
    assert res["review_id"].startswith("rev_")


@pytest.mark.asyncio
async def test_fallback_resilience_primary_llm_failure():
    """Verify LLMRouter gracefully falls back to secondary provider on primary failure."""
    router = LLMRouter()

    with patch.object(router, "_init_gemini", side_effect=Exception("Gemini Rate Limit Exceeded 429")):
        with patch.object(router, "_init_mistral") as mock_mistral:
            mock_model = MagicMock()
            mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="Fallback response from Mistral"))
            mock_mistral.return_value = mock_model

            res = await router.generate(messages="Test prompt", tier="flash")

    assert isinstance(res, LLMResponse)
    assert res.provider_used == "mistral"
    assert res.fallback_triggered is True
    assert "Gemini Rate Limit Exceeded" in res.error_message
