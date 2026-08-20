from datetime import datetime
import json
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.assessment import SkillAssessmentResult
from app.repositories.verification_repository import (
    get_assessment_questions_by_skill,
    get_assessment_question_by_id,
    create_assessment_result,
    get_user_skill_by_user_and_skill,
    update_user_skill_verification,
    get_assessment_results_for_user_skill
)
from app.repositories.skill_repository import get_skill_by_id


from app.services.question_generator_service import ensure_ten_questions_for_skill


def get_assessment_for_skill(
    db: Session,
    skill_id: int
) -> dict:
    skill = get_skill_by_id(db, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    # Ensures exactly 10 questions ordered by difficulty (EASY -> MEDIUM -> HARD)
    questions = ensure_ten_questions_for_skill(db, skill)

    # Sanitize questions: NEVER return correct_option or answer keys to client
    sanitized_questions = []
    for q in questions:
        sanitized_questions.append({
            "id": q.id,
            "skill_id": q.skill_id,
            "question_text": q.question_text,
            "options": q.get_options_list(),
            "difficulty": q.difficulty.upper()
        })

    return {
        "skill_id": skill.id,
        "skill_name": skill.name,
        "total_questions": len(sanitized_questions),
        "passing_threshold_percent": 70.0,
        "questions": sanitized_questions
    }



def evaluate_and_submit_assessment(
    db: Session,
    user_id: int,
    skill_id: int,
    answers: list[dict] # list of {"question_id": int, "selected_option": int}
) -> dict:
    # 1. Server-side ownership & authorization check
    user_skill = get_user_skill_by_user_and_skill(db, user_id, skill_id)
    if not user_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must claim this skill before taking its assessment"
        )

    questions = get_assessment_questions_by_skill(db, skill_id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment questions available for this skill"
        )

    question_map = {q.id: q for q in questions}

    if not answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answers payload cannot be empty"
        )

    correct_answers = 0
    total_questions = len(questions)
    response_details = []

    # Map user answers
    user_answer_map = {}
    for ans in answers:
        q_id = ans.get("question_id")
        opt = ans.get("selected_option")
        if q_id is not None and opt is not None:
            user_answer_map[int(q_id)] = int(opt)

    # 2. Server-side score evaluation
    for q_id, question in question_map.items():
        selected_opt = user_answer_map.get(q_id)
        is_correct = selected_opt == question.correct_option
        if is_correct:
            correct_answers += 1

        response_details.append({
            "question_id": q_id,
            "selected_option": selected_opt,
            "correct_option": question.correct_option,
            "is_correct": is_correct,
            "explanation": question.explanation
        })

    score = round((correct_answers / total_questions) * 100.0, 1)
    passed = score >= 70.0

    # 3. Database transaction for persistent assessment result
    assessment_result = SkillAssessmentResult(
        user_id=user_id,
        skill_id=skill_id,
        user_skill_id=user_skill.id,
        score=score,
        passed=passed,
        total_questions=total_questions,
        correct_answers=correct_answers,
        details=json.dumps(response_details)
    )
    saved_result = create_assessment_result(db, assessment_result)

    # 4. State transition rules:
    # Selected skill NEVER automatically becomes VERIFIED upon selection.
    # Status progresses to VERIFIED if assessment score >= 70%, else ASSESSED.
    new_status = "VERIFIED" if passed else "ASSESSED"
    verified_at = datetime.utcnow() if passed else None

    # If already VERIFIED or TRUSTED, preserve tier unless higher score
    if user_skill.verification_status in ["VERIFIED", "TRUSTED"] and not passed:
        new_status = user_skill.verification_status

    update_user_skill_verification(
        db=db,
        user_skill_id=user_skill.id,
        verification_status=new_status,
        score=score,
        verified_at=verified_at
    )

    return {
        "assessment_id": saved_result.id,
        "user_id": user_id,
        "skill_id": skill_id,
        "user_skill_id": user_skill.id,
        "score": score,
        "passed": passed,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "new_verification_status": new_status,
        "details": response_details
    }


def get_user_assessment_history(
    db: Session,
    user_id: int,
    skill_id: int
) -> list[dict]:
    results = get_assessment_results_for_user_skill(db, user_id, skill_id)
    history = []
    for r in results:
        history.append({
            "id": r.id,
            "score": r.score,
            "passed": r.passed,
            "total_questions": r.total_questions,
            "correct_answers": r.correct_answers,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return history
