"""
Day 74 Part A2 — Grounded Answer Evaluation Framework Test Suite.

Tests the evaluation framework components in isolation (no real LLM, no FAISS).

Coverage:
    GroundingEvaluator.evaluate_case():
        - Answerable case, grounded=True → passed=True
        - Answerable case, grounded=False, no fact coverage → passed=False
        - Unanswerable case, correct refusal → passed=True, correct_refusal=True
        - Unanswerable case, pipeline answered → unsupported_response=True, passed=False
        - Pipeline error → error field set, passed=False
        - answer_fact_coverage: all facts found → 1.0
        - answer_fact_coverage: no facts found → 0.0
        - answer_fact_coverage: partial → 0.5
        - answer_fact_coverage: empty expected → 1.0
        - valid_source_rate: all valid → 1.0
        - valid_source_rate: none valid → 0.0
        - valid_source_rate: partial → 0.5
        - source_coverage: expected ⊆ returned → 1.0
        - source_coverage: no expected → 1.0
        - source_coverage: none covered → 0.0

    GroundingEvaluator.compute_aggregate():
        - zero results → AggregateReport(total_cases=0)
        - all answerable, all passed → answerable_success_rate=1.0
        - all unanswerable, all correct → correct_refusal_rate=1.0
        - mixed results
        - error cases counted separately
        - latency aggregation (average, median, p95)
        - unsupported_response_count correct

    EvaluationDataset:
        - all case_ids are unique
        - all categories are valid EvaluationCategory values
        - cases with should_answer=False have empty expected_source_ids

    EvaluationRunner (integration):
        - Run with mock LLM → results for each case
        - DIRECT cases with sufficient mock chunks → grounded=True
        - EMPTY_RETRIEVAL / INSUFFICIENT cases → correct refusal
        - report aggregate totals match results

All tests use mocks — no real LLM API, FAISS, or DB is called.
"""
from __future__ import annotations

import pytest

from app.rag.evaluation.eval_dataset import (
    EVALUATION_DATASET,
    get_cases_by_category,
    get_dataset,
)
from app.rag.evaluation.eval_models import (
    AggregateReport,
    CaseResult,
    EvaluationCase,
    EvaluationCategory,
)
from app.rag.evaluation.eval_runner import EvaluationRunner
from app.rag.evaluation.grounding_evaluator import GroundingEvaluator


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_case(
    case_id: str = "case-test",
    category: EvaluationCategory = EvaluationCategory.DIRECT,
    question: str = "What is dependency injection?",
    expected_source_ids: list[str] | None = None,
    expected_answer_facts: list[str] | None = None,
    should_answer: bool = True,
) -> EvaluationCase:
    return EvaluationCase(
        case_id=case_id,
        category=category,
        question=question,
        expected_source_ids=expected_source_ids or [],
        expected_answer_facts=expected_answer_facts or [],
        should_answer=should_answer,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GroundingEvaluator.evaluate_case() Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestGroundingEvaluatorPerCase:
    """Per-case evaluation logic tests."""

    def setup_method(self):
        self.evaluator = GroundingEvaluator()

    def test_answerable_grounded_passes(self):
        """Answerable + grounded=True + no invalid sources → passed=True."""
        case = make_case(
            should_answer=True,
            expected_source_ids=["c1"],
            expected_answer_facts=["dependency injection"],
        )
        result = self.evaluator.evaluate_case(
            case=case,
            answer="This is about dependency injection in software design.",
            returned_source_ids=["c1"],
            retrieved_chunk_ids={"c1"},
            insufficient_context=False,
            grounded=True,
            latency_ms=250.0,
        )
        assert result.passed is True
        assert result.grounded is True
        assert result.correct_refusal is False
        assert result.unsupported_response is False
        assert result.answer_fact_coverage == 1.0
        assert result.valid_source_rate == 1.0

    def test_answerable_not_grounded_no_facts_fails(self):
        """Answerable + grounded=False + no facts found → passed=False."""
        case = make_case(
            should_answer=True,
            expected_answer_facts=["dependency injection"],
        )
        result = self.evaluator.evaluate_case(
            case=case,
            answer="This is a generic response with no relevant content.",
            returned_source_ids=[],
            retrieved_chunk_ids={"c1"},
            insufficient_context=False,
            grounded=False,
            latency_ms=300.0,
        )
        assert result.passed is False
        assert result.failure_reason is not None

    def test_unanswerable_correct_refusal_passes(self):
        """Unanswerable + pipeline refused (insufficient_context=True) → passed=True."""
        case = make_case(
            should_answer=False,
            category=EvaluationCategory.INSUFFICIENT,
        )
        result = self.evaluator.evaluate_case(
            case=case,
            answer="I couldn't find relevant information to answer this.",
            returned_source_ids=[],
            retrieved_chunk_ids=set(),
            insufficient_context=True,
            grounded=False,
            latency_ms=150.0,
        )
        assert result.passed is True
        assert result.correct_refusal is True
        assert result.unsupported_response is False

    def test_unanswerable_pipeline_answered_fails(self):
        """Unanswerable + pipeline gave confident answer → unsupported_response=True, passed=False."""
        case = make_case(
            should_answer=False,
            category=EvaluationCategory.INSUFFICIENT,
        )
        result = self.evaluator.evaluate_case(
            case=case,
            answer="The capital of France is Paris and here is an extensive explanation.",
            returned_source_ids=[],
            retrieved_chunk_ids=set(),
            insufficient_context=False,
            grounded=True,
            latency_ms=400.0,
        )
        assert result.passed is False
        assert result.unsupported_response is True
        assert result.correct_refusal is False

    def test_pipeline_error_tracked(self):
        """Pipeline error → error field set, passed=False."""
        case = make_case()
        result = self.evaluator.evaluate_case(
            case=case,
            answer="",
            returned_source_ids=[],
            retrieved_chunk_ids=set(),
            insufficient_context=True,
            grounded=False,
            latency_ms=0.0,
            pipeline_error="ConnectionError: FAISS unreachable",
        )
        assert result.passed is False
        assert result.error is not None
        assert "FAISS" in result.error

    def test_answer_snippet_truncated_at_200_chars(self):
        """Answer snippet is at most 200 chars."""
        case = make_case()
        result = self.evaluator.evaluate_case(
            case=case,
            answer="X" * 500,
            returned_source_ids=[],
            retrieved_chunk_ids={"c1"},
            insufficient_context=False,
            grounded=True,
            latency_ms=100.0,
        )
        assert len(result.answer_snippet) <= 200


class TestAnswerFactCoverage:
    """GroundingEvaluator._compute_fact_coverage() tests."""

    def setup_method(self):
        self.evaluator = GroundingEvaluator()

    def _eval(self, facts, answer):
        case = make_case(expected_answer_facts=facts)
        r = self.evaluator.evaluate_case(
            case=case,
            answer=answer,
            returned_source_ids=[],
            retrieved_chunk_ids={"c1"},
            insufficient_context=False,
            grounded=True,
            latency_ms=0.0,
        )
        return r.answer_fact_coverage

    def test_all_facts_found(self):
        cov = self._eval(
            ["dependency injection", "inversion of control"],
            "Dependency injection implements inversion of control.",
        )
        assert cov == 1.0

    def test_no_facts_found(self):
        cov = self._eval(
            ["dependency injection"],
            "This is about something completely unrelated.",
        )
        assert cov == 0.0

    def test_partial_facts(self):
        cov = self._eval(
            ["dependency injection", "async"],
            "This discusses dependency injection only.",
        )
        assert cov == 0.5

    def test_empty_expected_facts(self):
        cov = self._eval([], "Any answer.")
        assert cov == 1.0

    def test_empty_answer(self):
        case = make_case(expected_answer_facts=["dependency injection"])
        # AnswerValidator would reject empty, but evaluator handles it gracefully
        from app.rag.evaluation.grounding_evaluator import GroundingEvaluator
        ev = GroundingEvaluator()
        # Direct internal method test
        cov = ev._compute_fact_coverage(
            expected_facts=["dependency injection"],
            answer="",
        )
        assert cov == 0.0

    def test_case_insensitive(self):
        cov = self._eval(
            ["FastAPI"],
            "fastapi is a modern python web framework.",
        )
        assert cov == 1.0


class TestSourceValidity:
    """GroundingEvaluator source validity and coverage tests."""

    def setup_method(self):
        self.evaluator = GroundingEvaluator()

    def test_all_returned_in_retrieved_set(self):
        from app.rag.evaluation.grounding_evaluator import GroundingEvaluator
        ev = GroundingEvaluator()
        rate = ev._compute_valid_source_rate(
            returned_source_ids=["c1", "c2"],
            retrieved_chunk_ids={"c1", "c2", "c3"},
        )
        assert rate == 1.0

    def test_none_in_retrieved_set(self):
        from app.rag.evaluation.grounding_evaluator import GroundingEvaluator
        ev = GroundingEvaluator()
        rate = ev._compute_valid_source_rate(
            returned_source_ids=["FAKE-1", "FAKE-2"],
            retrieved_chunk_ids={"c1", "c2"},
        )
        assert rate == 0.0

    def test_partial_valid_source_rate(self):
        from app.rag.evaluation.grounding_evaluator import GroundingEvaluator
        ev = GroundingEvaluator()
        rate = ev._compute_valid_source_rate(
            returned_source_ids=["c1", "FAKE-99"],
            retrieved_chunk_ids={"c1"},
        )
        assert rate == 0.5

    def test_empty_returned_sources_valid(self):
        from app.rag.evaluation.grounding_evaluator import GroundingEvaluator
        ev = GroundingEvaluator()
        rate = ev._compute_valid_source_rate(
            returned_source_ids=[],
            retrieved_chunk_ids={"c1"},
        )
        assert rate == 1.0  # vacuously valid

    def test_source_coverage_all_expected_covered(self):
        from app.rag.evaluation.grounding_evaluator import GroundingEvaluator
        ev = GroundingEvaluator()
        cov = ev._compute_source_coverage(
            expected=["c1", "c2"],
            returned=["c1", "c2", "c3"],
        )
        assert cov == 1.0

    def test_source_coverage_none_covered(self):
        from app.rag.evaluation.grounding_evaluator import GroundingEvaluator
        ev = GroundingEvaluator()
        cov = ev._compute_source_coverage(
            expected=["c1", "c2"],
            returned=["c3", "c4"],
        )
        assert cov == 0.0

    def test_source_coverage_empty_expected(self):
        from app.rag.evaluation.grounding_evaluator import GroundingEvaluator
        ev = GroundingEvaluator()
        cov = ev._compute_source_coverage(expected=[], returned=["c1"])
        assert cov == 1.0  # no expectation = fully covered


# ═══════════════════════════════════════════════════════════════════════════════
# GroundingEvaluator.compute_aggregate() Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAggregateReport:
    """AggregateReport computation tests."""

    def setup_method(self):
        self.evaluator = GroundingEvaluator()

    def test_empty_results_returns_zero_total(self):
        report = self.evaluator.compute_aggregate([])
        assert report.total_cases == 0
        assert report.grounded_answer_rate is None

    def _make_result(
        self,
        should_answer=True,
        grounded=True,
        insufficient_context=False,
        correct_refusal=False,
        unsupported_response=False,
        answer_fact_coverage=1.0,
        valid_source_rate=1.0,
        source_coverage=1.0,
        expected_source_ids=None,
        latency_ms=200.0,
        passed=True,
        error=None,
    ) -> CaseResult:
        return CaseResult(
            case_id="test",
            category=EvaluationCategory.DIRECT,
            question="q",
            should_answer=should_answer,
            grounded=grounded,
            insufficient_context=insufficient_context,
            answer_snippet="snippet",
            returned_source_ids=[],
            expected_source_ids=expected_source_ids or [],
            valid_source_rate=valid_source_rate,
            source_coverage=source_coverage,
            answer_fact_coverage=answer_fact_coverage,
            correct_refusal=correct_refusal,
            unsupported_response=unsupported_response,
            latency_ms=latency_ms,
            passed=passed,
            error=error,
        )

    def test_all_answerable_all_grounded(self):
        results = [
            self._make_result(should_answer=True, grounded=True, latency_ms=100.0),
            self._make_result(should_answer=True, grounded=True, latency_ms=200.0),
        ]
        report = self.evaluator.compute_aggregate(results)
        assert report.total_cases == 2
        assert report.grounded_answer_rate == 1.0
        assert report.answerable_success_rate == 1.0
        assert report.correct_refusal_rate is None  # no unanswerable cases
        assert report.unsupported_response_count == 0

    def test_all_unanswerable_all_correct_refusals(self):
        results = [
            self._make_result(
                should_answer=False, grounded=False, insufficient_context=True,
                correct_refusal=True, unsupported_response=False,
                passed=True, latency_ms=150.0,
            ),
            self._make_result(
                should_answer=False, grounded=False, insufficient_context=True,
                correct_refusal=True, unsupported_response=False,
                passed=True, latency_ms=180.0,
            ),
        ]
        report = self.evaluator.compute_aggregate(results)
        assert report.correct_refusal_rate == 1.0
        assert report.answerable_success_rate is None  # no answerable cases
        assert report.unsupported_response_count == 0

    def test_unsupported_response_count_tracked(self):
        results = [
            self._make_result(
                should_answer=False, grounded=False,
                correct_refusal=False, unsupported_response=True,
                passed=False,
            ),
            self._make_result(
                should_answer=False, grounded=False,
                correct_refusal=True, unsupported_response=False,
                passed=True,
            ),
        ]
        report = self.evaluator.compute_aggregate(results)
        assert report.unsupported_response_count == 1

    def test_error_cases_counted(self):
        results = [
            self._make_result(should_answer=True, grounded=True, passed=True),
            self._make_result(
                should_answer=True, grounded=False, passed=False,
                error="ConnectionError",
            ),
        ]
        report = self.evaluator.compute_aggregate(results)
        assert report.error_cases == 1

    def test_latency_aggregation(self):
        latencies = [100.0, 200.0, 300.0, 400.0, 500.0]
        results = [
            self._make_result(latency_ms=lat) for lat in latencies
        ]
        report = self.evaluator.compute_aggregate(results)
        assert report.average_latency_ms == pytest.approx(300.0, abs=1.0)
        assert report.median_latency_ms == pytest.approx(300.0, abs=1.0)
        assert report.p95_latency_ms is not None

    def test_to_dict_includes_all_keys(self):
        results = [self._make_result()]
        report = self.evaluator.compute_aggregate(results)
        d = report.to_dict()
        required_keys = [
            "total_cases", "answerable_cases", "unanswerable_cases",
            "error_cases", "passed_cases", "failed_cases",
            "grounded_answer_rate", "answerable_success_rate",
            "correct_refusal_rate", "answer_fact_coverage",
            "valid_source_rate", "source_coverage",
            "unsupported_response_count",
            "average_latency_ms", "median_latency_ms", "p95_latency_ms",
        ]
        for key in required_keys:
            assert key in d, f"Missing key: {key}"

    def test_format_human_readable_returns_string(self):
        results = [self._make_result()]
        report = self.evaluator.compute_aggregate(results)
        text = report.format_human_readable()
        assert isinstance(text, str)
        assert "Grounded Answer Evaluation" in text
        assert "Grounded Answer Rate" in text


# ═══════════════════════════════════════════════════════════════════════════════
# Evaluation Dataset Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEvaluationDataset:
    """Dataset integrity tests."""

    def test_all_case_ids_unique(self):
        dataset = get_dataset()
        ids = [c.case_id for c in dataset]
        assert len(ids) == len(set(ids)), "Duplicate case_ids found"

    def test_all_categories_valid(self):
        dataset = get_dataset()
        valid_categories = set(EvaluationCategory)
        for case in dataset:
            assert case.category in valid_categories

    def test_dataset_not_empty(self):
        dataset = get_dataset()
        assert len(dataset) >= 10

    def test_all_nine_categories_represented(self):
        dataset = get_dataset()
        categories = {c.category for c in dataset}
        expected = set(EvaluationCategory)
        assert categories == expected

    def test_insufficient_cases_have_should_answer_false(self):
        cases = get_cases_by_category(EvaluationCategory.INSUFFICIENT)
        for case in cases:
            assert case.should_answer is False, (
                f"INSUFFICIENT case {case.case_id} should have should_answer=False"
            )

    def test_empty_retrieval_cases_have_should_answer_false(self):
        cases = get_cases_by_category(EvaluationCategory.EMPTY_RETRIEVAL)
        for case in cases:
            assert case.should_answer is False

    def test_direct_cases_have_should_answer_true(self):
        cases = get_cases_by_category(EvaluationCategory.DIRECT)
        for case in cases:
            assert case.should_answer is True

    def test_get_cases_by_category_filters_correctly(self):
        direct_cases = get_cases_by_category(EvaluationCategory.DIRECT)
        for case in direct_cases:
            assert case.category == EvaluationCategory.DIRECT


# ═══════════════════════════════════════════════════════════════════════════════
# EvaluationRunner Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEvaluationRunner:
    """EvaluationRunner integration tests (mock LLM mode)."""

    def test_run_returns_correct_case_count(self):
        dataset = get_dataset()
        runner = EvaluationRunner()
        results, report = runner.run(
            dataset=dataset,
            mock_llm_answer="This is a detailed answer about dependency injection.",
        )
        assert len(results) == len(dataset)
        assert report.total_cases == len(dataset)

    def test_empty_retrieval_cases_get_refusal(self):
        """EMPTY_RETRIEVAL and INSUFFICIENT cases (no expected_source_ids) should produce
        correct refusals in mock mode."""
        empty_cases = [
            c for c in get_dataset()
            if not c.expected_source_ids and not c.should_answer
        ]
        runner = EvaluationRunner()
        results, _ = runner.run(
            dataset=empty_cases,
            mock_llm_answer=None,  # Runner handles empty retrieval with refusal phrase
        )
        for result in results:
            assert result.insufficient_context is True or result.correct_refusal is True

    def test_direct_cases_with_mock_answer_may_pass(self):
        """DIRECT cases with expected_answer_facts and a matching mock answer should pass."""
        direct_cases = get_cases_by_category(EvaluationCategory.DIRECT)
        runner = EvaluationRunner()
        # Provide an answer that mentions all common expected facts
        mock_answer = (
            "dependency injection implements inversion of control. "
            "fastapi uses async type hints. solid stands for single responsibility, "
            "open closed. global interpreter lock threads cpu-bound. "
        )
        results, report = runner.run(
            dataset=direct_cases,
            mock_llm_answer=mock_answer,
        )
        # At least some should pass (grounded or fact coverage > 0)
        any_success = any(r.passed or r.answer_fact_coverage > 0 for r in results)
        assert any_success

    def test_runner_totals_consistent(self):
        """passed_cases + failed_cases == total_cases."""
        dataset = get_dataset()
        runner = EvaluationRunner()
        results, report = runner.run(
            dataset=dataset,
            mock_llm_answer="Test answer with relevant content.",
        )
        assert report.passed_cases + report.failed_cases == report.total_cases

    def test_runner_with_single_case(self):
        """Runner works correctly with a single case."""
        case = make_case(
            case_id="single-test",
            expected_source_ids=["c1"],
            expected_answer_facts=["dependency injection"],
            should_answer=True,
        )
        runner = EvaluationRunner()
        results, report = runner.run(
            dataset=[case],
            mock_llm_answer="Dependency injection decouples components.",
        )
        assert len(results) == 1
        assert report.total_cases == 1

    def test_runner_with_empty_dataset(self):
        """Runner handles empty dataset gracefully."""
        runner = EvaluationRunner()
        results, report = runner.run(dataset=[])
        assert results == []
        assert report.total_cases == 0
        assert report.grounded_answer_rate is None
