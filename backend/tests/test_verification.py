import pytest
from datetime import datetime
from app.models.user import User

from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.session import Session as SessionModel
from app.models.feedback import Feedback
from app.models.assessment import AssessmentQuestion
from app.services.skill_service import assign_skill_to_user
from app.services.assessment_service import (
    get_assessment_for_skill,
    evaluate_and_submit_assessment,
)
from app.services.credibility_service import (
    get_skill_credibility_breakdown,
    get_user_overall_credibility,
)


from app.core.database import SessionLocal, engine
from app.models.base import Base

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import uuid

@pytest.fixture
def setup_verification_db(db_session):
    test_id = uuid.uuid4().hex[:8]
    # Create test user
    user = User(
        name=f"Verification Test User {test_id}",
        email=f"verify_test_{test_id}@example.com",
        password_hash="hashed_pw"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create test skill
    skill = Skill(
        name=f"Verification Skill {test_id}",
        category="Test Category",
        description="Test skill for verification"
    )

    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)

    # Create assessment questions for skill
    q1 = AssessmentQuestion(
        skill_id=skill.id,
        question_text="What is 2+2 in Python?",
        options='["3", "4", "5", "6"]',
        correct_option=1,
        explanation="2+2 equals 4",
        difficulty="BEGINNER"
    )
    q2 = AssessmentQuestion(
        skill_id=skill.id,
        question_text="Which keyword defines a function?",
        options='["function", "def", "func", "lambda"]',
        correct_option=1,
        explanation="def defines a function",
        difficulty="BEGINNER"
    )
    db_session.add_all([q1, q2])
    db_session.commit()

    return {
        "user": user,
        "skill": skill,
        "q1": q1,
        "q2": q2
    }


def test_skill_claim_defaults_to_claimed(db_session, setup_verification_db):
    user = setup_verification_db["user"]
    skill = setup_verification_db["skill"]

    # Claim skill
    user_skill = assign_skill_to_user(
        db=db_session,
        user_id=user.id,
        skill_id=skill.id,
        skill_type="teach"
    )

    assert user_skill.id is not None
    # RULE: A selected skill must NEVER automatically become VERIFIED
    assert user_skill.verification_status == "CLAIMED"
    assert user_skill.score is None


def test_assessment_questions_sanitized(db_session, setup_verification_db):
    skill = setup_verification_db["skill"]

    assessment = get_assessment_for_skill(db_session, skill.id)
    assert assessment["skill_id"] == skill.id
    assert len(assessment["questions"]) == 10

    # Verify correct_option is NOT exposed to client
    for q in assessment["questions"]:
        assert "correct_option" not in q
        assert "options" in q
        assert len(q["options"]) == 4


def test_submit_assessment_passing_promotes_to_verified(db_session, setup_verification_db):
    user = setup_verification_db["user"]
    skill = setup_verification_db["skill"]
    q1 = setup_verification_db["q1"]
    q2 = setup_verification_db["q2"]

    # Claim teach skill
    user_skill = assign_skill_to_user(db_session, user.id, skill.id, "teach")

    # Submit correct answers for both questions (100% score)
    answers = [
        {"question_id": q1.id, "selected_option": q1.correct_option},
        {"question_id": q2.id, "selected_option": q2.correct_option},
    ]

    result = evaluate_and_submit_assessment(
        db=db_session,
        user_id=user.id,
        skill_id=skill.id,
        answers=answers
    )

    assert result["passed"] is True
    assert result["score"] == 100.0
    assert result["new_verification_status"] == "VERIFIED"

    # Verify persistent UserSkill model updated
    db_session.refresh(user_skill)
    assert user_skill.verification_status == "VERIFIED"
    assert user_skill.score == 100.0
    assert user_skill.verified_at is not None


def test_submit_assessment_failing_sets_assessed(db_session, setup_verification_db):
    user = setup_verification_db["user"]
    skill = setup_verification_db["skill"]
    q1 = setup_verification_db["q1"]
    q2 = setup_verification_db["q2"]

    user_skill = assign_skill_to_user(db_session, user.id, skill.id, "teach")

    # Submit wrong answers (0% score)
    answers = [
        {"question_id": q1.id, "selected_option": 0},
        {"question_id": q2.id, "selected_option": 0},
    ]

    result = evaluate_and_submit_assessment(
        db=db_session,
        user_id=user.id,
        skill_id=skill.id,
        answers=answers
    )

    assert result["passed"] is False
    assert result["score"] == 0.0
    assert result["new_verification_status"] == "ASSESSED"

    db_session.refresh(user_skill)
    assert user_skill.verification_status == "ASSESSED"
    assert user_skill.score == 0.0


def test_evidence_based_credibility_calculation(db_session, setup_verification_db):
    user = setup_verification_db["user"]
    skill = setup_verification_db["skill"]

    assign_skill_to_user(db_session, user.id, skill.id, "teach")

    # Initial credibility breakdown
    breakdown = get_skill_credibility_breakdown(db_session, user.id, skill.id)
    assert breakdown["verification_status"] == "CLAIMED"
    assert breakdown["signals"]["completed_teaching_sessions"] == 0
    assert breakdown["signals"]["feedback_count"] == 0

    # Create real learner user
    learner = User(
        name="Test Learner User",
        email=f"learner_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_pw"
    )
    db_session.add(learner)
    db_session.commit()
    db_session.refresh(learner)

    # Add real completed teaching session
    session = SessionModel(
        requester_id=learner.id,
        mentor_id=user.id,
        skill_id=skill.id,
        scheduled_at=datetime.utcnow(),
        meeting_link="https://meet.jit.si/test",
        status="completed"
    )
    db_session.add(session)
    db_session.commit()

    # Add real learner feedback
    feedback = Feedback(
        session_id=session.id,
        reviewer_id=learner.id,
        reviewee_id=user.id,
        rating=5,
        comment="Great mentor!"
    )

    db_session.add(feedback)
    db_session.commit()

    # Re-check credibility breakdown
    updated_breakdown = get_skill_credibility_breakdown(db_session, user.id, skill.id)
    assert updated_breakdown["signals"]["completed_teaching_sessions"] == 1
    assert updated_breakdown["signals"]["feedback_count"] == 1
    assert updated_breakdown["signals"]["average_rating"] == 5.0

    overall = get_user_overall_credibility(db_session, user.id)
    assert overall["total_completed_sessions"] == 1
    assert overall["overall_average_rating"] == 5.0
