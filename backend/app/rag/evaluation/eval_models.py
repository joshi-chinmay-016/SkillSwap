"""
Evaluation Models — Day 74 Part A2.

Pure data containers for the grounded-answer evaluation framework.

These models are EVALUATION-ONLY.  They must NOT be imported by any
production request-handling module.

Schema:
    EvaluationCategory : Enum of dataset case categories.
    EvaluationCase     : One test case in the evaluation dataset.
    CaseResult         : Per-case evaluation result.
    AggregateReport    : Summary metrics over all evaluated cases.

Grounded definition (for this evaluator):
    A case is grounded when:
        - should_answer = True
        - The pipeline returned grounded=True OR produced an answer
          containing at least one expected fact
        - No invalid source IDs were returned
        - The response is not an unsupported fabrication

Correct refusal definition:
    A case is a correct refusal when:
        - should_answer = False
        - The pipeline returned insufficient_context=True OR
          the answer contains explicit refusal language
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EvaluationCategory(str, Enum):
    """
    Categories for evaluation dataset cases.

    A  — DIRECT            : Knowledge contains the required information.
    B  — MULTI_SOURCE      : Answer requires multiple retrieved sources.
    C  — INSUFFICIENT      : Knowledge does not contain enough information.
    D  — IRRELEVANT        : Retriever returns non-useful chunks.
    E  — SOURCE_ATTRIBUTION: Verify source IDs match retrieved set.
    F  — FABRICATED_SOURCE : LLM attempts to reference an unretieved source.
    G  — PROMPT_INJECTION  : Retrieved content contains malicious instructions.
    H  — EMPTY_RETRIEVAL   : Zero retrieved chunks.
    I  — NORMAL_KNOWLEDGE  : Straightforward knowledge question (anti-over-hardening).
    """

    DIRECT = "direct"
    MULTI_SOURCE = "multi_source"
    INSUFFICIENT = "insufficient"
    IRRELEVANT = "irrelevant"
    SOURCE_ATTRIBUTION = "source_attribution"
    FABRICATED_SOURCE = "fabricated_source"
    PROMPT_INJECTION = "prompt_injection"
    EMPTY_RETRIEVAL = "empty_retrieval"
    NORMAL_KNOWLEDGE = "normal_knowledge"


@dataclass
class EvaluationCase:
    """
    One test case in the evaluation dataset.

    Fields:
        case_id              : Unique case identifier (e.g. \"case-001\").
        category             : EvaluationCategory enum value.
        question             : Natural-language question to evaluate.
        expected_source_ids  : chunk_ids the answer should reference.
                               Empty list = no source expectation for this case.
        expected_answer_facts: Strings that should appear in a correct answer.
                               Each fact is a short canonical phrase.
                               Empty list = no fact expectation.
        should_answer        : True if the pipeline SHOULD produce an answer.
                               False if the pipeline should refuse (insufficient).
        description          : Human-readable description of what this case tests.
    """

    case_id: str
    category: EvaluationCategory
    question: str
    expected_source_ids: list[str] = field(default_factory=list)
    expected_answer_facts: list[str] = field(default_factory=list)
    should_answer: bool = True
    description: str = ""


@dataclass
class CaseResult:
    """
    Per-case evaluation result produced by GroundingEvaluator.

    Fields:
        case_id              : Matches EvaluationCase.case_id.
        category             : Matches EvaluationCase.category.
        question             : The evaluated question.
        should_answer        : Expected behavior.
        grounded             : Whether the pipeline returned grounded=True.
        insufficient_context : Whether the pipeline returned insufficient_context=True.
        answer_snippet       : First 200 chars of the generated answer (no raw content stored).
        returned_source_ids  : chunk_ids in the returned sources.
        expected_source_ids  : From the EvaluationCase.
        valid_source_rate    : Fraction of returned sources in the retrieved set.
        source_coverage      : Fraction of expected_source_ids that appear in returned sources.
        answer_fact_coverage : Fraction of expected_answer_facts present in the answer.
        correct_refusal      : True if should_answer=False AND pipeline refused correctly.
        unsupported_response : True if should_answer=False BUT pipeline gave a confident answer.
        latency_ms           : Total pipeline latency for this case.
        failure_reason       : Description of why the case failed, if applicable.
        passed               : Whether this case meets all expected behaviors.
    """

    case_id: str
    category: EvaluationCategory
    question: str
    should_answer: bool
    grounded: bool = False
    insufficient_context: bool = False
    answer_snippet: str = ""
    returned_source_ids: list[str] = field(default_factory=list)
    expected_source_ids: list[str] = field(default_factory=list)
    valid_source_rate: float = 0.0        # returned sources ⊆ retrieved set
    source_coverage: float = 0.0          # expected ∩ returned / expected
    answer_fact_coverage: float = 0.0     # expected facts found in answer
    correct_refusal: bool = False
    unsupported_response: bool = False
    latency_ms: float = 0.0
    failure_reason: Optional[str] = None
    passed: bool = False
    error: Optional[str] = None           # Pipeline error, if any


@dataclass
class AggregateReport:
    """
    Aggregate evaluation metrics over all evaluated cases.

    Metric definitions:
        grounded_answer_rate    : grounded cases / evaluable cases (pipeline succeeded)
        answerable_success_rate : successful grounded answers / answerable cases
        correct_refusal_rate    : correct refusals / unanswerable cases
        answer_fact_coverage    : avg fact coverage across answerable cases (0.0-1.0)
        valid_source_rate       : avg valid_source_rate across all cases
        source_coverage         : avg source_coverage across cases with expected sources
        unsupported_response_count: cases where should_answer=False but pipeline answered

    Latency:
        average_latency_ms, median_latency_ms, p95_latency_ms (all cases)

    Note:
        Metrics that cannot be reliably computed (e.g., zero denominator)
        are reported as None.
    """

    total_cases: int = 0
    answerable_cases: int = 0
    unanswerable_cases: int = 0
    error_cases: int = 0

    grounded_answer_rate: Optional[float] = None
    answerable_success_rate: Optional[float] = None
    correct_refusal_rate: Optional[float] = None

    answer_fact_coverage: Optional[float] = None
    valid_source_rate: Optional[float] = None
    source_coverage: Optional[float] = None

    unsupported_response_count: int = 0

    average_latency_ms: Optional[float] = None
    median_latency_ms: Optional[float] = None
    p95_latency_ms: Optional[float] = None

    passed_cases: int = 0
    failed_cases: int = 0

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict for machine-readable output."""
        return {
            "total_cases": self.total_cases,
            "answerable_cases": self.answerable_cases,
            "unanswerable_cases": self.unanswerable_cases,
            "error_cases": self.error_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "grounded_answer_rate": self.grounded_answer_rate,
            "answerable_success_rate": self.answerable_success_rate,
            "correct_refusal_rate": self.correct_refusal_rate,
            "answer_fact_coverage": self.answer_fact_coverage,
            "valid_source_rate": self.valid_source_rate,
            "source_coverage": self.source_coverage,
            "unsupported_response_count": self.unsupported_response_count,
            "average_latency_ms": self.average_latency_ms,
            "median_latency_ms": self.median_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
        }

    def format_human_readable(self) -> str:
        """Return a human-readable text report."""

        def fmt_rate(v: Optional[float]) -> str:
            return f"{v * 100:.1f}%" if v is not None else "N/A"

        def fmt_ms(v: Optional[float]) -> str:
            return f"{v:.1f} ms" if v is not None else "N/A"

        lines = [
            "Grounded Answer Evaluation",
            "─" * 43,
            f"Cases:                  {self.total_cases}",
            f"Answerable:             {self.answerable_cases}",
            f"Unanswerable:           {self.unanswerable_cases}",
            f"Errors:                 {self.error_cases}",
            f"Passed:                 {self.passed_cases}",
            f"Failed:                 {self.failed_cases}",
            "",
            f"Grounded Answer Rate:   {fmt_rate(self.grounded_answer_rate)}",
            f"Answerable Success:     {fmt_rate(self.answerable_success_rate)}",
            f"Correct Refusal Rate:   {fmt_rate(self.correct_refusal_rate)}",
            "",
            f"Answer Fact Coverage:   {fmt_rate(self.answer_fact_coverage)}",
            f"Source Validity Rate:   {fmt_rate(self.valid_source_rate)}",
            f"Source Coverage:        {fmt_rate(self.source_coverage)}",
            "",
            f"Unsupported Responses:  {self.unsupported_response_count}",
            "",
            f"Avg Latency:            {fmt_ms(self.average_latency_ms)}",
            f"Median Latency:         {fmt_ms(self.median_latency_ms)}",
            f"P95 Latency:            {fmt_ms(self.p95_latency_ms)}",
        ]
        return "\n".join(lines)
