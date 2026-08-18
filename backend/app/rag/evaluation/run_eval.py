"""
CLI Entrypoint for Grounded Answer Evaluation — Day 74 Part A2.

Run with:
    python -m app.rag.evaluation.run_eval

Options:
    --write-report : Saves JSON report to evaluation_reports/grounded_answer_eval.json
    --output PATH  : Custom output file path

Example:
    python -m app.rag.evaluation.run_eval --write-report
"""
from __future__ import annotations

import sys
from app.rag.evaluation.eval_dataset import get_dataset
from app.rag.evaluation.eval_runner import EvaluationRunner


def main():
    write_report = "--write-report" in sys.argv
    output_path = None
    if "--output" in sys.argv:
        try:
            idx = sys.argv.index("--output")
            output_path = sys.argv[idx + 1]
        except (IndexError, ValueError):
            pass

    print("=" * 60)
    print("SkillSwap Arena — Grounded Answer Evaluation Runner")
    print("=" * 60)

    dataset = get_dataset()
    print(f"Loaded evaluation dataset: {len(dataset)} cases across 9 categories.")

    runner = EvaluationRunner()
    results, report = runner.run(
        dataset=dataset,
        write_report=write_report,
        output_path=output_path,
    )

    print("\n" + report.format_human_readable() + "\n")

    if write_report:
        print(f"Report written successfully to evaluation_reports/grounded_answer_eval.json")

    sys.exit(0 if report.failed_cases == 0 else 1)


if __name__ == "__main__":
    main()
