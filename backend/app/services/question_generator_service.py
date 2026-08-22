import json
import logging
from typing import List
from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.models.assessment import AssessmentQuestion
from app.repositories.verification_repository import create_assessment_question
from app.services.skill_engine import SkillEngine, GeneratedQuestion, SkillProfiler, QuestionValidator

logger = logging.getLogger("skillswap.question_generator")


def ensure_ten_questions_for_skill(db: Session, skill: Skill) -> List[AssessmentQuestion]:
    """
    Ensures that a skill has a validated, authoritative 10-question assessment bank
    structured across Easy (3), Intermediate (4), and Hard (3) difficulties.
    Purges any contaminated, invalid, or obsolete questions.
    """
    profile = SkillProfiler.get_profile(skill.name)
    existing = db.query(AssessmentQuestion).filter(AssessmentQuestion.skill_id == skill.id).all()

    # 1. Validate all existing questions against the skill profile
    valid_existing = []
    seen_texts = set()
    needs_commit = False

    for q in existing:
        try:
            options_list = json.loads(q.options) if isinstance(q.options, str) else q.options
        except Exception:
            options_list = []

        gq = GeneratedQuestion(
            skill=profile.canonical_name,
            knowledge_area="",
            difficulty=q.difficulty,
            question_type="",
            question_text=q.question_text,
            options=options_list,
            correct_option=q.correct_option,
            explanation=q.explanation or "",
            expected_concepts=[]
        )

        val_result = QuestionValidator.validate_question(gq, profile, seen_texts=seen_texts)
        if not val_result.is_valid:
            logger.warning(
                f"Purging contaminated assessment question ID {q.id} for skill '{skill.name}': {val_result.rejection_reason}"
            )
            db.delete(q)
            needs_commit = True
        else:
            valid_existing.append(q)

    if needs_commit:
        db.commit()

    if len(valid_existing) >= 10:
        return sort_questions_by_difficulty(valid_existing[:10])

    needed = 10 - len(valid_existing)
    logger.info(
        "skill.verification.started",
        extra={"skill_id": skill.id, "skill_name": skill.name, "valid_count": len(valid_existing), "needed": needed}
    )

    # Use the domain-agnostic SkillEngine
    generated_questions: List[GeneratedQuestion] = SkillEngine.generate_assessment_for_skill(skill.name)

    existing_texts = {q.question_text.lower().strip() for q in valid_existing}
    added = []

    for gq in generated_questions:
        if len(valid_existing) + len(added) >= 10:
            break

        if gq.question_text.lower().strip() not in existing_texts:
            new_q = AssessmentQuestion(
                skill_id=skill.id,
                question_text=gq.question_text,
                options=json.dumps(gq.options),
                correct_option=gq.correct_option,
                explanation=gq.explanation,
                difficulty=gq.difficulty
            )
            created = create_assessment_question(db, new_q)
            added.append(created)
            existing_texts.add(gq.question_text.lower().strip())

    all_questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.skill_id == skill.id).all()
    return sort_questions_by_difficulty(all_questions[:10])


def sort_questions_by_difficulty(questions: List[AssessmentQuestion]) -> List[AssessmentQuestion]:
    diff_order = {"EASY": 1, "BEGINNER": 1, "INTERMEDIATE": 2, "MEDIUM": 2, "ADVANCED": 3, "HARD": 3}
    return sorted(questions, key=lambda q: diff_order.get(q.difficulty.upper(), 2))
