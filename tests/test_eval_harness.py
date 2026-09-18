import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.eval_service import eval_service, BENCHMARK_DATASET, GroundTruthFinding, BenchmarkSample

client = TestClient(app)


def test_get_benchmark_samples():
    """Verify API endpoint returning labeled evaluation benchmark samples."""
    response = client.get("/api/eval/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "total_samples" in data
    assert data["total_samples"] == len(BENCHMARK_DATASET)
    assert len(data["samples"]) > 0
    assert "sample_id" in data["samples"][0]


def test_run_eval_benchmark_endpoint_mock():
    """Verify execution of evaluation benchmark via REST API in mock mode."""
    response = client.post("/api/eval/run", json={"use_mock": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["mode"] == "mock"
    assert "summary" in data
    summary = data["summary"]
    assert summary["total_samples"] == len(BENCHMARK_DATASET)
    assert summary["precision_recall"]["precision"] >= 0.0
    assert summary["ast_validation_pass_rate"] >= 0.0


def test_eval_service_unit_metrics():
    """Verify precision/recall calculations in eval_service."""
    gt = GroundTruthFinding(category="security", cwe_or_rule_id="CWE-89", keywords=["sql"])
    pred_true = {"category": "security", "cwe_or_rule_id": "CWE-89", "title": "SQL Injection"}
    pred_false = {"category": "quality", "cwe_or_rule_id": "CWE-100", "title": "Formatting"}

    assert eval_service.evaluate_finding_match(pred_true, gt) is True
    assert eval_service.evaluate_finding_match(pred_false, gt) is False
