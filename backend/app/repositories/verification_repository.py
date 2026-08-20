from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, or_

from app.models.assessment import AssessmentQuestion, SkillAssessmentResult
from app.models.user_skill import UserSkill
from app.models.session import Session as SessionModel
from app.models.feedback import Feedback


def get_assessment_questions_by_skill(
    db: Session,
    skill_id: int
) -> list[AssessmentQuestion]:
    return (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.skill_id == skill_id)
        .all()
    )


def get_assessment_question_by_id(
    db: Session,
    question_id: int
) -> AssessmentQuestion | None:
    return (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.id == question_id)
        .first()
    )


def create_assessment_question(
    db: Session,
    question: AssessmentQuestion
) -> AssessmentQuestion:
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def create_assessment_result(
    db: Session,
    result: SkillAssessmentResult
) -> SkillAssessmentResult:
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_assessment_results_for_user_skill(
    db: Session,
    user_id: int,
    skill_id: int
) -> list[SkillAssessmentResult]:
    return (
        db.query(SkillAssessmentResult)
        .filter(
            SkillAssessmentResult.user_id == user_id,
            SkillAssessmentResult.skill_id == skill_id
        )
        .order_by(SkillAssessmentResult.created_at.desc())
        .all()
    )


def get_user_skill_by_user_and_skill(
    db: Session,
    user_id: int,
    skill_id: int,
    skill_type: str | None = None
) -> UserSkill | None:
    query = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == skill_id
    )
    if skill_type:
        query = query.filter(UserSkill.type == skill_type)
    return query.first()


def get_user_skill_by_id(
    db: Session,
    user_skill_id: int
) -> UserSkill | None:
    return (
        db.query(UserSkill)
        .filter(UserSkill.id == user_skill_id)
        .first()
    )


def update_user_skill_verification(
    db: Session,
    user_skill_id: int,
    verification_status: str,
    score: float | None = None,
    verified_at: datetime | None = None
) -> UserSkill | None:
    user_skill = get_user_skill_by_id(db, user_skill_id)
    if not user_skill:
        return None

    user_skill.verification_status = verification_status
    if score is not None:
        user_skill.score = score
    if verified_at is not None:
        user_skill.verified_at = verified_at

    db.commit()
    db.refresh(user_skill)
    return user_skill


def get_completed_sessions_count_for_mentor(
    db: Session,
    user_id: int,
    skill_id: int | None = None
) -> int:
    query = db.query(SessionModel).filter(
        SessionModel.mentor_id == user_id,
        or_(
            SessionModel.status == "completed",
            SessionModel.status == "COMPLETED"
        )
    )
    if skill_id is not None:
        query = query.filter(SessionModel.skill_id == skill_id)
    return query.count()


def get_feedback_summary_for_mentor(
    db: Session,
    user_id: int
) -> dict:
    feedback_list = db.query(Feedback).filter(
        Feedback.reviewee_id == user_id
    ).all()
    count = len(feedback_list)
    if count == 0:
        return {"count": 0, "average_rating": 0.0}

    total_rating = sum(f.rating for f in feedback_list)
    return {
        "count": count,
        "average_rating": round(total_rating / count, 2)
    }


def get_repeat_learners_count(
    db: Session,
    user_id: int
) -> int:
    # Query requester_ids having > 1 completed sessions with this mentor
    results = (
        db.query(SessionModel.requester_id, func.count(SessionModel.id))
        .filter(
            SessionModel.mentor_id == user_id,
            or_(
                SessionModel.status == "completed",
                SessionModel.status == "COMPLETED"
            )
        )
        .group_by(SessionModel.requester_id)
        .having(func.count(SessionModel.id) > 1)
        .all()
    )
    return len(results)
