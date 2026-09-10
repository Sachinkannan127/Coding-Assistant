import time
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.app.services.code_refactor_validator import validate_refactored_code

logger = logging.getLogger(__name__)


class GroundTruthFinding(BaseModel):
    category: str  # "bug", "security", "quality", "complexity"
    cwe_or_rule_id: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)


class BenchmarkSample(BaseModel):
    sample_id: str
    language: str
    code: str
    expected_mode: str = "quick"  # "quick" or "deep"
    expected_findings: List[GroundTruthFinding] = Field(default_factory=list)
    expected_valid_refactor: bool = True
    target_max_latency_ms: float = 10000.0  # 10s for quick, 45s for deep


class PrecisionRecallMetrics(BaseModel):
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0


class EvaluationSummary(BaseModel):
    total_samples: int = 0
    precision_recall: PrecisionRecallMetrics
    ast_validation_pass_rate: float = 0.0
    avg_latency_ms: float = 0.0
    sla_compliance_rate: float = 0.0
    samples_results: List[Dict[str, Any]] = Field(default_factory=list)


# Labeled Ground Truth Benchmark Dataset covering multi-language vulnerabilities
BENCHMARK_DATASET: List[BenchmarkSample] = [
    BenchmarkSample(
        sample_id="py-001-null-check",
        language="python",
        code="""def get_user_name(user):\n    return user.profile.name\n""",
        expected_mode="quick",
        expected_findings=[
            GroundTruthFinding(
                category="bug",
                cwe_or_rule_id="CWE-476",
                line_start=2,
                keywords=["user", "null", "none", "attribute", "profile"]
            )
        ],
        expected_valid_refactor=True,
        target_max_latency_ms=10000.0
    ),
    BenchmarkSample(
        sample_id="py-002-sql-injection",
        language="python",
        code="""import sqlite3\n\ndef query_user(user_id):\n    conn = sqlite3.connect('app.db')\n    cursor = conn.cursor()\n    cursor.execute("SELECT * FROM users WHERE id = '%s'" % user_id)\n    return cursor.fetchall()\n""",
        expected_mode="deep",
        expected_findings=[
            GroundTruthFinding(
                category="security",
                cwe_or_rule_id="CWE-89",
                line_start=6,
                keywords=["sql", "injection", "parameter", "format"]
            )
        ],
        expected_valid_refactor=True,
        target_max_latency_ms=45000.0
    ),
    BenchmarkSample(
        sample_id="js-001-prototype-pollution",
        language="javascript",
        code="""function merge(target, source) {\n    for (let key in source) {\n        target[key] = source[key];\n    }\n    return target;\n}\n""",
        expected_mode="deep",
        expected_findings=[
            GroundTruthFinding(
                category="security",
                cwe_or_rule_id="CWE-1321",
                line_start=3,
                keywords=["prototype", "pollution", "target", "hasOwnProperty"]
            )
        ],
        expected_valid_refactor=True,
        target_max_latency_ms=45000.0
    ),
    BenchmarkSample(
        sample_id="java-001-resource-leak",
        language="java",
        code="""import java.io.*;\n\npublic class FileRead {\n    public static void readData(String path) throws Exception {\n        FileInputStream fis = new FileInputStream(path);\n        int b = fis.read();\n    }\n}\n""",
        expected_mode="deep",
        expected_findings=[
            GroundTruthFinding(
                category="quality",
                cwe_or_rule_id="CWE-404",
                line_start=6,
                keywords=["stream", "close", "resource", "leak", "try-with-resources"]
            )
        ],
        expected_valid_refactor=True,
        target_max_latency_ms=45000.0
    ),
    BenchmarkSample(
        sample_id="cpp-001-use-after-free",
        language="cpp",
        code="""#include <iostream>\n\nvoid dangling_pointer() {\n    int* ptr = new int(42);\n    delete ptr;\n    std::cout << *ptr << std::endl;\n}\n""",
        expected_mode="quick",
        expected_findings=[
            GroundTruthFinding(
                category="bug",
                cwe_or_rule_id="CWE-416",
                line_start=7,
                keywords=["dangling", "delete", "use-after-free", "pointer"]
            )
        ],
        expected_valid_refactor=True,
        target_max_latency_ms=10000.0
    ),
    BenchmarkSample(
        sample_id="go-001-unhandled-error",
        language="go",
        code="""package main\n\nimport "os"\n\nfunc ReadFile(filename string) []byte {\n    data, _ := os.ReadFile(filename)\n    return data\n}\n""",
        expected_mode="quick",
        expected_findings=[
            GroundTruthFinding(
                category="quality",
                cwe_or_rule_id="CWE-391",
                line_start=6,
                keywords=["error", "err", "unhandled", "ignored"]
            )
        ],
        expected_valid_refactor=True,
        target_max_latency_ms=10000.0
    )
]


class AIEvaluationService:
    """
    AI Quality & Performance Evaluation Service.
    Calculates precision, recall, AST syntax validation rates, and latency SLA metrics.
    """

    def evaluate_finding_match(
        self,
        predicted_finding: Dict[str, Any],
        ground_truth: GroundTruthFinding
    ) -> bool:
        """Determines if a predicted finding matches a ground truth finding."""
        pred_cat = str(predicted_finding.get("category", "")).lower()
        gt_cat = ground_truth.category.lower()

        # Check category match
        if pred_cat != gt_cat and pred_cat != "bug":
            # Allow bug/security overlap if keywords match
            pass

        # Check CWE match if present
        pred_cwe = str(predicted_finding.get("cwe_or_rule_id", "")).upper()
        if ground_truth.cwe_or_rule_id and ground_truth.cwe_or_rule_id.upper() in pred_cwe:
            return True

        # Check keyword matches in title/description/suggestion
        text_content = f"{predicted_finding.get('title', '')} {predicted_finding.get('description', '')} {predicted_finding.get('suggestion', '')}".lower()
        matched_keywords = sum(1 for kw in ground_truth.keywords if kw.lower() in text_content)
        
        return matched_keywords >= 1

    def compute_sample_metrics(
        self,
        sample: BenchmarkSample,
        review_result: Dict[str, Any],
        latency_ms: float
    ) -> Dict[str, Any]:
        """Evaluates review results for a single benchmark sample."""
        predicted_findings = review_result.get("findings", [])
        ground_truths = sample.expected_findings

        tp = 0
        matched_gt_indices = set()

        for pred in predicted_findings:
            for gt_idx, gt in enumerate(ground_truths):
                if gt_idx not in matched_gt_indices:
                    if self.evaluate_finding_match(pred, gt):
                        tp += 1
                        matched_gt_indices.add(gt_idx)
                        break

        fp = max(0, len(predicted_findings) - tp)
        fn = max(0, len(ground_truths) - len(matched_gt_indices))

        # Check AST validation of refactored code
        refactoring = review_result.get("refactoring", {})
        refactored_code = refactoring.get("refactored_code", "")
        ast_val = validate_refactored_code(
            original_code=sample.code,
            refactored_code=refactored_code,
            language=sample.language
        )

        sla_compliant = latency_ms <= sample.target_max_latency_ms

        return {
            "sample_id": sample.sample_id,
            "language": sample.language,
            "mode": sample.expected_mode,
            "latency_ms": latency_ms,
            "sla_compliant": sla_compliant,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "ast_valid": ast_val.is_valid,
            "refactoring_status": refactoring.get("validation_status", "passed")
        }

    def aggregate_metrics(self, sample_results: List[Dict[str, Any]]) -> EvaluationSummary:
        """Aggregates individual sample evaluation metrics into an EvaluationSummary."""
        total_tp = sum(r["true_positives"] for r in sample_results)
        total_fp = sum(r["false_positives"] for r in sample_results)
        total_fn = sum(r["false_negatives"] for r in sample_results)

        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        total_samples = len(sample_results)
        ast_passes = sum(1 for r in sample_results if r["ast_valid"])
        ast_pass_rate = (ast_passes / total_samples * 100.0) if total_samples > 0 else 0.0

        avg_latency = (sum(r["latency_ms"] for r in sample_results) / total_samples) if total_samples > 0 else 0.0
        sla_passes = sum(1 for r in sample_results if r["sla_compliant"])
        sla_compliance_rate = (sla_passes / total_samples * 100.0) if total_samples > 0 else 0.0

        return EvaluationSummary(
            total_samples=total_samples,
            precision_recall=PrecisionRecallMetrics(
                true_positives=total_tp,
                false_positives=total_fp,
                false_negatives=total_fn,
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1, 4)
            ),
            ast_validation_pass_rate=round(ast_pass_rate, 2),
            avg_latency_ms=round(avg_latency, 2),
            sla_compliance_rate=round(sla_compliance_rate, 2),
            samples_results=sample_results
        )


eval_service = AIEvaluationService()
