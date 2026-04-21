"""
LLM-as-Judge evaluation pipeline.
In productie: judge model = llama3 via Ollama.
In tests: mock judge voor deterministische resultaten.
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import json
import os


class EvalMetric(Enum):
    FAITHFULNESS = "faithfulness"      # klopt output met input?
    RELEVANCE = "relevance"            # is output relevant voor taak?
    COMPLETENESS = "completeness"      # zijn alle vereiste elementen aanwezig?
    SAFETY = "safety"                  # geen GDPR-schendingen, geen gevaarlijke data?


@dataclass
class EvalCase:
    """Single evaluation test case."""
    case_id: str
    agent_name: str
    input_prompt: str
    expected_output: str
    actual_output: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class EvalScore:
    metric: EvalMetric
    score: float          # 0.0 - 1.0
    rationale: str
    passed: bool = False  # True if score >= threshold

    def __post_init__(self):
        self.passed = self.score >= 0.7  # default threshold


@dataclass
class EvalResult:
    case_id: str
    agent_name: str
    scores: list[EvalScore]
    overall_score: float = 0.0
    verdict: str = "UNKNOWN"  # PASS | FAIL | NEEDS_REVIEW

    def __post_init__(self):
        if self.scores:
            self.overall_score = sum(s.score for s in self.scores) / len(self.scores)
        if self.overall_score >= 0.8:
            self.verdict = "PASS"
        elif self.overall_score >= 0.6:
            self.verdict = "NEEDS_REVIEW"
        else:
            self.verdict = "FAIL"


class JudgeBackend:
    """Abstract judge backend — swap real LLM for mock in tests."""

    def evaluate(self, case: EvalCase, metric: EvalMetric) -> EvalScore:
        raise NotImplementedError


class MockJudgeBackend(JudgeBackend):
    """Deterministic mock judge for testing."""

    def evaluate(self, case: EvalCase, metric: EvalMetric) -> EvalScore:
        # Simple heuristic: longer output = more complete
        score = min(1.0, len(case.actual_output) / max(len(case.expected_output), 1))
        score = round(min(score, 1.0), 2)
        return EvalScore(
            metric=metric,
            score=score,
            rationale=f"Mock evaluation: output length ratio {score:.2f}",
        )


class OllamaJudgeBackend(JudgeBackend):
    """Real Ollama judge — only used in production."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def evaluate(self, case: EvalCase, metric: EvalMetric) -> EvalScore:
        # Would call Ollama API in production
        raise NotImplementedError("OllamaJudgeBackend requires running Ollama instance")


class EvalPipeline:
    """Runs evaluation cases against a judge backend."""

    def __init__(self, backend: Optional[JudgeBackend] = None):
        self.backend = backend or MockJudgeBackend()
        self._results: list[EvalResult] = []

    def evaluate_case(self, case: EvalCase, metrics: Optional[list[EvalMetric]] = None) -> EvalResult:
        if metrics is None:
            metrics = list(EvalMetric)
        scores = [self.backend.evaluate(case, m) for m in metrics]
        result = EvalResult(case_id=case.case_id, agent_name=case.agent_name, scores=scores)
        self._results.append(result)
        return result

    def load_jsonl(self, path: str) -> list[EvalCase]:
        """Loads eval cases from JSONL file."""
        cases = []
        if not os.path.exists(path):
            return cases
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    cases.append(EvalCase(**data))
        return cases

    def run_from_jsonl(self, path: str) -> list[EvalResult]:
        cases = self.load_jsonl(path)
        return [self.evaluate_case(c) for c in cases]

    def get_summary(self) -> dict:
        if not self._results:
            return {"total": 0, "passed": 0, "failed": 0, "needs_review": 0}
        return {
            "total": len(self._results),
            "passed": sum(1 for r in self._results if r.verdict == "PASS"),
            "failed": sum(1 for r in self._results if r.verdict == "FAIL"),
            "needs_review": sum(1 for r in self._results if r.verdict == "NEEDS_REVIEW"),
            "avg_score": sum(r.overall_score for r in self._results) / len(self._results),
        }

    def get_agent_scores(self, agent_name: str) -> list[EvalResult]:
        return [r for r in self._results if r.agent_name == agent_name]

    def clear(self):
        self._results = []
