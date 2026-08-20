import pytest
import uuid
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.feedback import Feedback
from app.models.session import Session as SessionModel
from app.services.recommendation_service import get_recommendations
from app.repositories.recommendation_repository import get_candidate_mentors_for_skills


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def setup_recommendation_db(db_session: Session):
    test_id = uuid.uuid4().hex[:8]
    # Create test users with unique emails
    learner = User(name=f"Learner {test_id}", email=f"learner_{test_id}@example.com", password_hash="hashed")
    mentor1 = User(name=f"Mentor Alice {test_id}", email=f"alice_{test_id}@example.com", password_hash="hashed")
    mentor2 = User(name=f"Mentor Bob {test_id}", email=f"bob_{test_id}@example.com", password_hash="hashed")

    db_session.add_all([learner, mentor1, mentor2])
    db_session.commit()
    db_session.refresh(learner)
    db_session.refresh(mentor1)
    db_session.refresh(mentor2)

    # Create skills
    python_skill = Skill(name=f"Python_{test_id}", category="Programming")
    react_skill = Skill(name=f"React_{test_id}", category="Web Dev")

    db_session.add_all([python_skill, react_skill])
    db_session.commit()
    db_session.refresh(python_skill)
    db_session.refresh(react_skill)

    # Learner wants to learn Python
    us_learner = UserSkill(user_id=learner.id, skill_id=python_skill.id, type="learn")

    # Mentor1 teaches Python (Verified)
    us_m1 = UserSkill(
        user_id=mentor1.id,
        skill_id=python_skill.id,
        type="teach",
        verification_status="VERIFIED",
        score=90.0
    )

    # Mentor2 teaches Python (Claimed)
    us_m2 = UserSkill(
        user_id=mentor2.id,
        skill_id=python_skill.id,
        type="teach",
        verification_status="CLAIMED",
        score=0.0
    )

    db_session.add_all([us_learner, us_m1, us_m2])
    db_session.commit()

    # Feedback for Mentor1
    fb = Feedback(
        session_id=1,
        reviewer_id=learner.id,
        reviewee_id=mentor1.id,
        rating=5.0,
        comment="Awesome Python mentor!"
    )
    db_session.add(fb)
    db_session.commit()

    return {
        "learner": learner,
        "mentor1": mentor1,
        "mentor2": mentor2,
        "python_skill": python_skill,
        "react_skill": react_skill,
    }


def test_recommendations_excludes_current_user(db_session, setup_recommendation_db):
    learner = setup_recommendation_db["learner"]
    python_skill = setup_recommendation_db["python_skill"]

    # Also give learner a teaching skill in Python
    learner_teach = UserSkill(user_id=learner.id, skill_id=python_skill.id, type="teach")
    db_session.add(learner_teach)
    db_session.commit()

    recs = get_recommendations(db_session, current_user_id=learner.id)

    # Verify learner is excluded from candidates
    rec_ids = [r["mentor_id"] for r in recs]
    assert learner.id not in rec_ids


def test_recommendations_evidence_backed_reasons(db_session, setup_recommendation_db):
    learner = setup_recommendation_db["learner"]
    mentor1 = setup_recommendation_db["mentor1"]
    python_skill = setup_recommendation_db["python_skill"]

    recs = get_recommendations(db_session, current_user_id=learner.id)
    assert len(recs) >= 1

    # Mentor1 should be ranked higher due to VERIFIED status & 5.0 rating
    top_rec = recs[0]
    assert top_rec["mentor_id"] == mentor1.id
    assert top_rec["verification_status"] == "VERIFIED"
    assert top_rec["average_rating"] == 5.0

    # Verify reasons are non-empty and backed by database facts
    assert len(top_rec["reasons"]) > 0
    reasons_text = " ".join(top_rec["reasons"])
    assert python_skill.name in reasons_text
    assert "Verified skill" in reasons_text


def test_recommendations_empty_learn_skills(db_session, setup_recommendation_db):
    mentor1 = setup_recommendation_db["mentor1"]

    # Mentor1 has no learn skills
    recs = get_recommendations(db_session, current_user_id=mentor1.id)
    assert recs == []


def test_recommendations_privacy_filtering(db_session, setup_recommendation_db):
    learner = setup_recommendation_db["learner"]

    recs = get_recommendations(db_session, current_user_id=learner.id)
    for rec in recs:
        # Verify private fields like password_hash are never present
        assert "password_hash" not in rec
        assert "token" not in rec
        assert "mentor_id" in rec
        assert "mentor_name" in rec
        assert "reasons" in rec
