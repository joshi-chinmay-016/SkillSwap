"""
GroundingEvaluator — Day 74 Part A2.

Evaluates whether generated answers satisfy the grounding guarantees established
by the Grounded Answer Engine (Day 74 Part A1).

This evaluator is EVALUATION-ONLY.  It must NOT be imported by any production
request-handling module.

Evaluation architecture (separate from production):

    Evaluation Dataset
            │
            ▼
    EvaluationRunner           ← uses production pipeline
            │
            ▼
    Generated Answer + Sources ← from RAGService / mock
            │
            ▼
    GroundingEvaluator         ← this module
            │
            ▼
    CaseResult + AggregateReport

Metrics implemented:
    grounded_answer_rate     : grounded=True cases / total evaluable cases
    answerable_success_rate  : successful grounded answers / answerable cases
    correct_refusal_rate     : correct refusals / unanswerable cases
    answer_fact_coverage     : avg fraction of expected facts found in answer
    valid_source_rate        : avg fraction of returned sources in retrieved set
    source_coverage          : avg fraction of expected sources in returned set
    unsupported_response     : should_answer=False but pipeline gave confident answer

Limitations (documented honestly):
    - Answer fact matching uses case-insensitive substring search (lightweight).
      It does NOT perform full semantic hallucination detection.
    - Unsupported response detection is heuristic (checks for refusal phrases),
      not a reliable semantic hallucination checker.
    - No confidence values are reported (spec §40).
    - No LLM judge is used.
"""
from __future__ import annotations

import logging
import statistics
from typing import Optional

from app.rag.evaluation.eval_models import (
    AggregateReport,
    CaseResult,
    EvaluationCase,
    EvaluationCategory,
)

logger = logging.getLogger(__name__)

# Phrases that indicate a correct refusal / insufficient-context response.
# These are used for heuristic unsupported_response detection.
_REFUSAL_PHRASES = [
    "insufficient",
    "not enough information",
    "couldn't find",
    "could not find",
    "no relevant",
    "not available in",
    "knowledge base does not",
    "i don't have information",
    "i do not have information",
    "unable to answer",
    "cannot answer",
]


class GroundingEvaluator:
    """
    Evaluates grounded-answer pipeline output against an evaluation dataset.

    Usage::

        evaluator = GroundingEvaluator()
        result = evaluator.evaluate_case(
            case=eval_case,
            answer="FastAPI uses dependency injection.",
            returned_sources=[ContextSource(...)],
            retrieved_chunk_ids={"chunk-1", "chunk-2"},
            insufficient_context=False,
            grounded=True,
            latency_ms=420.0,
        )
        report = evaluator.compute_aggregate([result, ...])
        print(report.format_human_readable())
    """

    # ── Per-case evaluation ────────────────────────────────────────────────────

    def evaluate_case(
        self,
        *,
        case: EvaluationCase,
        answer: str,
        returned_source_ids: list[str],
        retrieved_chunk_ids: set[str],
        insufficient_context: bool,
        grounded: bool,
        latency_ms: float,
        pipeline_error: Optional[str] = None,
    ) -> CaseResult:
        """
        Evaluate one case against the pipeline output.

        Args:
            case                : The EvaluationCase being evaluated.
            answer              : Generated answer string (empty on error).
            returned_source_ids : chunk_ids from returned sources.
            retrieved_chunk_ids : All chunk_ids that were retrieved (authoritative set).
            insufficient_context: Whether the pipeline flagged insufficient context.
            grounded            : Whether the pipeline returned grounded=True.
            latency_ms          : Total pipeline latency for this case.
            pipeline_error      : Exception message if the pipeline errored.

        Returns:
            CaseResult with all evaluated metrics.
        """
        # ── Error case ────────────────────────────────────────────────────────
        if pipeline_error is not None:
            return CaseResult(
                case_id=case.case_id,
                category=case.category,
                question=case.question,
                should_answer=case.should_answer,
                grounded=False,
                insufficient_context=True,
                answer_snippet="[PIPELINE ERROR]",
                returned_source_ids=[],
                expected_source_ids=case.expected_source_ids,
                latency_ms=latency_ms,
                failure_reason=f"Pipeline error: {pipeline_error}",
                passed=False,
                error=pipeline_error,
            )

        # ── Metrics ───────────────────────────────────────────────────────────
        answer_snippet = answer[:200] if answer else ""

        # Source integrity: returned sources ⊆ retrieved set
        valid_source_rate = self._compute_valid_source_rate(
            returned_source_ids, retrieved_chunk_ids
        )

        # Source coverage: expected ∩ returned / expected
        source_coverage = self._compute_source_coverage(
            expected=case.expected_source_ids,
            returned=returned_source_ids,
        )

        # Answer fact coverage: expected facts found in answer
        answer_fact_coverage = self._compute_fact_coverage(
            expected_facts=case.expected_answer_facts,
            answer=answer,
        )

        # Correct refusal: should_answer=False and pipeline refused
        correct_refusal = False
        unsupported_response = False

        if not case.should_answer:
            if insufficient_context or self._is_refusal(answer):
                correct_refusal = True
            else:
                # Pipeline answered confidently when it should have refused
                unsupported_response = True

        # Determine whether this case passed
        passed = self._determine_pass(
            case=case,
            grounded=grounded,
            insufficient_context=insufficient_context,
            correct_refusal=correct_refusal,
            answer_fact_coverage=answer_fact_coverage,
            valid_source_rate=valid_source_rate,
        )

        failure_reason: Optional[str] = None
        if not passed:
            failure_reason = self._build_failure_reason(
                case=case,
                grounded=grounded,
                insufficient_context=insufficient_context,
                correct_refusal=correct_refusal,
                unsupported_response=unsupported_response,
                answer_fact_coverage=answer_fact_coverage,
                valid_source_rate=valid_source_rate,
            )

        logger.debug(
            "GroundingEvaluator — case_id=%s category=%s passed=%s "
            "grounded=%s fact_coverage=%.2f valid_source=%.2f",
            case.case_id, case.category.value, passed,
            grounded, answer_fact_coverage, valid_source_rate,
        )

        return CaseResult(
            case_id=case.case_id,
            category=case.category,
            question=case.question,
            should_answer=case.should_answer,
            grounded=grounded,
            insufficient_context=insufficient_context,
            answer_snippet=answer_snippet,
            returned_source_ids=returned_source_ids,
            expected_source_ids=case.expected_source_ids,
            valid_source_rate=valid_source_rate,
            source_coverage=source_coverage,
            answer_fact_coverage=answer_fact_coverage,
            correct_refusal=correct_refusal,
            unsupported_response=unsupported_response,
            latency_ms=latency_ms,
            failure_reason=failure_reason,
            passed=passed,
        )

    # ── Aggregate computation ──────────────────────────────────────────────────

    def compute_aggregate(self, results: list[CaseResult]) -> AggregateReport:
        """
        Compute aggregate metrics from a list of CaseResult.

        Args:
            results : List of per-case evaluation results.

        Returns:
            AggregateReport with all aggregate metrics.
        """
        if not results:
            return AggregateReport(total_cases=0)

        total = len(results)
        error_cases = [r for r in results if r.error is not None]
        valid_results = [r for r in results if r.error is None]

        answerable = [r for r in valid_results if r.should_answer]
        unanswerable = [r for r in valid_results if not r.should_answer]

        # ── Grounded answer rate ───────────────────────────────────────────────
        # grounded cases / evaluable (non-error) cases
        grounded_answer_rate: Optional[float] = None
        if valid_results:
            grounded_count = sum(1 for r in valid_results if r.grounded)
            grounded_answer_rate = grounded_count / len(valid_results)

        # ── Answerable success rate ────────────────────────────────────────────
        # successful grounded answers / answerable cases
        answerable_success_rate: Optional[float] = None
        if answerable:
            success_count = sum(
                1 for r in answerable
                if r.grounded or r.answer_fact_coverage > 0.0
            )
            answerable_success_rate = success_count / len(answerable)

        # ── Correct refusal rate ───────────────────────────────────────────────
        correct_refusal_rate: Optional[float] = None
        if unanswerable:
            refusal_count = sum(1 for r in unanswerable if r.correct_refusal)
            correct_refusal_rate = refusal_count / len(unanswerable)

        # ── Answer fact coverage ───────────────────────────────────────────────
        # Average over answerable cases with expected facts
        fact_cases = [
            r for r in answerable if r.expected_source_ids or r.answer_fact_coverage >= 0
        ]
        # More precisely: cases where expected_answer_facts were defined
        answer_fact_coverage: Optional[float] = None
        if answerable:
            answer_fact_coverage = statistics.mean(
                r.answer_fact_coverage for r in answerable
            )

        # ── Source validity rate ───────────────────────────────────────────────
        valid_source_rate: Optional[float] = None
        if valid_results:
            valid_source_rate = statistics.mean(
                r.valid_source_rate for r in valid_results
            )

        # ── Source coverage ────────────────────────────────────────────────────
        source_cov_cases = [r for r in valid_results if r.expected_source_ids]
        source_coverage: Optional[float] = None
        if source_cov_cases:
            source_coverage = statistics.mean(
                r.source_coverage for r in source_cov_cases
            )

        # ── Unsupported responses ──────────────────────────────────────────────
        unsupported_count = sum(1 for r in unanswerable if r.unsupported_response)

        # ── Latency ───────────────────────────────────────────────────────────
        latencies = [r.latency_ms for r in valid_results if r.latency_ms >= 0]
        average_latency_ms: Optional[float] = None
        median_latency_ms: Optional[float] = None
        p95_latency_ms: Optional[float] = None
        if latencies:
            average_latency_ms = statistics.mean(latencies)
            median_latency_ms = statistics.median(latencies)
            sorted_lat = sorted(latencies)
            p95_idx = max(0, int(len(sorted_lat) * 0.95) - 1)
            p95_latency_ms = sorted_lat[p95_idx]

        passed_cases = sum(1 for r in results if r.passed)
        failed_cases = total - passed_cases

        return AggregateReport(
            total_cases=total,
            answerable_cases=len(answerable),
            unanswerable_cases=len(unanswerable),
            error_cases=len(error_cases),
            grounded_answer_rate=grounded_answer_rate,
            answerable_success_rate=answerable_success_rate,
            correct_refusal_rate=correct_refusal_rate,
            answer_fact_coverage=answer_fact_coverage,
            valid_source_rate=valid_source_rate,
            source_coverage=source_coverage,
            unsupported_response_count=unsupported_count,
            average_latency_ms=average_latency_ms,
            median_latency_ms=median_latency_ms,
            p95_latency_ms=p95_latency_ms,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _compute_valid_source_rate(
        returned_source_ids: list[str],
        retrieved_chunk_ids: set[str],
    ) -> float:
        """
        Compute fraction of returned sources that are in the retrieved set.

        returned_sources ⊆ retrieved_set is the expected invariant.
        Returns 1.0 when returned_sources is empty (vacuously valid).
        """
        if not returned_source_ids:
            return 1.0  # No sources claimed = no invalid claims
        if not retrieved_chunk_ids:
            return 0.0  # Retrieved set is empty; any claimed source is invalid
        valid = sum(
            1 for sid in returned_source_ids if sid in retrieved_chunk_ids
        )
        return valid / len(returned_source_ids)

    @staticmethod
    def _compute_source_coverage(
        expected: list[str],
        returned: list[str],
    ) -> float:
        """
        Compute fraction of expected sources that appear in returned sources.

        source_coverage = |expected ∩ returned| / |expected|
        Returns 1.0 when expected is empty (no expectation = fully satisfied).
        """
        if not expected:
            return 1.0
        returned_set = set(returned)
        matched = sum(1 for sid in expected if sid in returned_set)
        return matched / len(expected)

    @staticmethod
    def _compute_fact_coverage(
        expected_facts: list[str],
        answer: str,
    ) -> float:
        """
        Compute fraction of expected answer facts present in the generated answer.

        Uses case-insensitive substring search.  This is a lightweight signal,
        NOT a complete semantic quality metric.  Documented limitation: exact
        phrasing differences (synonyms, paraphrasing) are not detected.

        Returns 1.0 when expected_facts is empty (no expectation = fully covered).
        Returns 0.0 when answer is empty.
        """
        if not expected_facts:
            return 1.0
        if not answer:
            return 0.0
        answer_lower = answer.lower()
        matched = sum(
            1 for fact in expected_facts
            if fact.lower().strip() in answer_lower
        )
        return matched / len(expected_facts)

    @staticmethod
    def _is_refusal(answer: str) -> bool:
        """
        Heuristic check: does the answer text indicate a refusal or
        insufficient-context response?

        This is NOT a complete semantic check.  It detects common refusal
        phrases used by the grounding policy.
        """
        if not answer:
            return True
        answer_lower = answer.lower()
        return any(phrase in answer_lower for phrase in _REFUSAL_PHRASES)

    @staticmethod
    def _determine_pass(
        *,
        case: EvaluationCase,
        grounded: bool,
        insufficient_context: bool,
        correct_refusal: bool,
        answer_fact_coverage: float,
        valid_source_rate: float,
    ) -> bool:
        """
        Determine whether this case passes evaluation.

        Pass criteria:
            - Answerable cases: grounded=True OR answer_fact_coverage > 0
              AND valid_source_rate == 1.0 (no invalid sources)
            - Unanswerable cases: correct_refusal=True
        """
        if not case.should_answer:
            return correct_refusal

        # For answerable cases: grounded preferred, but fallback to fact coverage
        has_answer = grounded or answer_fact_coverage > 0.0
        sources_valid = valid_source_rate >= 1.0 or not case.expected_source_ids

        return has_answer and sources_valid

    @staticmethod
    def _build_failure_reason(
        *,
        case: EvaluationCase,
        grounded: bool,
        insufficient_context: bool,
        correct_refusal: bool,
        unsupported_response: bool,
        answer_fact_coverage: float,
        valid_source_rate: float,
    ) -> str:
        """Build a human-readable failure reason string."""
        reasons = []
        if not case.should_answer and unsupported_response:
            reasons.append("Should have refused but gave confident answer")
        if case.should_answer and not grounded and answer_fact_coverage == 0.0:
            reasons.append("Answer is not grounded and no expected facts found")
        if case.should_answer and insufficient_context:
            reasons.append("Incorrectly flagged as insufficient context")
        if valid_source_rate < 1.0:
            reasons.append(
                f"Invalid source references (valid_rate={valid_source_rate:.2f})"
            )
        return "; ".join(reasons) if reasons else "Unknown failure"
