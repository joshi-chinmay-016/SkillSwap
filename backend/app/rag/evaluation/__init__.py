"""
RAG Evaluation Package — Day 74 Part A2.

Provides a controlled evaluation framework for the Grounded Answer Engine.

This package is EVALUATION-ONLY and must NOT be imported by production
request-handling code.  Importing evaluation modules in production paths
is a design violation.

Components:
    eval_models       : EvaluationCase, CaseResult, AggregateReport schemas
    eval_dataset      : Controlled dataset with 9 categories (A-I)
    grounding_evaluator: GroundingEvaluator — per-case and aggregate metrics
    eval_runner       : EvaluationRunner — runs dataset through production pipeline
"""
from app.rag.evaluation.eval_models import (
    AggregateReport,
    CaseResult,
    EvaluationCase,
    EvaluationCategory,
)
from app.rag.evaluation.grounding_evaluator import GroundingEvaluator

__all__ = [
    "EvaluationCase",
    "EvaluationCategory",
    "CaseResult",
    "AggregateReport",
    "GroundingEvaluator",
]
