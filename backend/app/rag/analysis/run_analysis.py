"""
CLI Script for Day 75 Context Quality Analysis & Before/After Context Optimization.

Runs the 25 evaluation dataset cases through:
    1. Unoptimized Context Quality Analysis (Part A1)
    2. Context Optimizer Pass (Part A2)
    3. Optimized Context Quality Analysis (Part A2)

Run with:
    python -m app.rag.analysis.run_analysis
"""
from __future__ import annotations

import sys
from app.rag.analysis.context_analyzer import ContextAnalyzer
from app.rag.analysis.context_snapshot import ContextSnapshot
from app.rag.evaluation.eval_dataset import get_dataset
from app.rag.evaluation.eval_runner import EvaluationRunner
from app.rag.optimization.context_optimizer import DefaultContextOptimizer


def main():
    print("=" * 65)
    print("SkillSwap Arena -- Day 75 Context Quality & Optimization Runner")
    print("=" * 65)

    dataset = get_dataset()
    print(f"Dataset cases: {len(dataset)} across 9 categories.")

    analyzer = ContextAnalyzer()
    optimizer = DefaultContextOptimizer.from_settings()

    unoptimized_analyses = []
    optimized_analyses = []

    total_orig_chunks = 0
    total_opt_chunks = 0
    total_orig_tokens = 0
    total_opt_tokens = 0

    for case in dataset:
        mock_chunks = EvaluationRunner._build_mock_chunks(case)

        # Part A1: Unoptimized Context Analysis
        snap_unopt = ContextSnapshot.from_chunks(mock_chunks, query=case.question)
        analysis_unopt = analyzer.analyze_snapshot(
            snap_unopt,
            case_id=case.case_id,
            expected_facts=case.expected_answer_facts,
            expected_source_ids=case.expected_source_ids,
            should_answer=case.should_answer,
        )
        unoptimized_analyses.append(analysis_unopt)

        # Part A2: Context Optimization Pass
        opt_res = optimizer.optimize(mock_chunks)
        total_orig_chunks += opt_res.original_chunk_count
        total_opt_chunks += opt_res.optimized_chunk_count
        total_orig_tokens += opt_res.original_token_estimate
        total_opt_tokens += opt_res.optimized_token_estimate

        # Part A2: Optimized Context Analysis
        snap_opt = ContextSnapshot.from_chunks(opt_res.optimized_chunks, query=case.question)
        analysis_opt = analyzer.analyze_snapshot(
            snap_opt,
            case_id=case.case_id,
            expected_facts=case.expected_answer_facts,
            expected_source_ids=case.expected_source_ids,
            should_answer=case.should_answer,
        )
        optimized_analyses.append(analysis_opt)

    report_unopt = analyzer.compute_aggregate(unoptimized_analyses)
    report_opt = analyzer.compute_aggregate(optimized_analyses)

    print("\n--- PART A1: UNOPTIMIZED CONTEXT BASELINE ---")
    print(report_unopt.format_human_readable())

    print("\n--- PART A2: OPTIMIZED CONTEXT SUMMARY ---")
    print(report_opt.format_human_readable())

    print("\n" + "=" * 65)
    print("BEFORE vs AFTER OPTIMIZATION COMPARISON")
    print("=" * 65)
    print(f"Total Chunks:            {total_orig_chunks}  ==>  {total_opt_chunks}  (Reduced by {total_orig_chunks - total_opt_chunks})")
    print(f"Total Estimated Tokens:  {total_orig_tokens}  ==>  {total_opt_tokens}  (Saved {total_orig_tokens - total_opt_tokens} tokens)")
    print(f"Redundant Cases:         {report_unopt.redundant_context_count}  ==>  {report_opt.redundant_context_count}")
    print(f"Evidence Sufficiency:    {report_unopt.evidence_sufficiency_rate * 100:.1f}%  ==>  {report_opt.evidence_sufficiency_rate * 100:.1f}%")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
