import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.models.assessment import AssessmentQuestion, SkillAssessmentResult
from app.models.learning_activity import LearningActivity
from app.models.journey import LearningJourney
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.seeds.seed_achievements import seed_initial_achievements
from app.services.skill_engine import (
    SkillEngine,
    SkillNormalizer,
    SkillProfiler,
    QuestionValidator,
    GeneratedQuestion,
    DomainQuestionBank
)
from app.services.question_generator_service import ensure_ten_questions_for_skill
from app.services.assessment_service import evaluate_and_submit_assessment

# SQLite in-memory test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TABLES = [
    User.__table__,
    Skill.__table__,
    UserSkill.__table__,
    AssessmentQuestion.__table__,
    SkillAssessmentResult.__table__,
    LearningJourney.__table__,
    LearningActivity.__table__,
    Achievement.__table__,
    UserAchievement.__table__,
]


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine, tables=TABLES)
    db = TestingSessionLocal()
    seed_initial_achievements(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine, tables=TABLES)


def test_skill_normalization():
    """Validates normalization and classification across tech, non-tech, and novel skills."""
    # Java
    java_norm = SkillNormalizer.normalize("core java")
    assert java_norm["canonical"] == "Java"
    assert java_norm["domain"] == "Technology"
    assert java_norm["category"] == "Programming Language"

    # DevOps
    devops_norm = SkillNormalizer.normalize("dev-ops")
    assert devops_norm["canonical"] == "DevOps"
    assert devops_norm["category"] == "DevOps & Cloud Infrastructure"

    # Public Speaking
    ps_norm = SkillNormalizer.normalize("public speaking")
    assert ps_norm["canonical"] == "Public Speaking"
    assert ps_norm["domain"] == "Professional Skills"

    # Problem Solving
    prob_norm = SkillNormalizer.normalize("critical problem solving")
    assert prob_norm["canonical"] == "Problem Solving"

    # Novel / Unknown Skill (e.g. Arecanut Farming)
    novel_norm = SkillNormalizer.normalize("Arecanut Farming")
    assert "Arecanut" in novel_norm["canonical"] or "Agriculture" in novel_norm["canonical"]
    assert len(novel_norm["knowledge_areas"]) >= 4


def test_question_validator_anti_contamination():
    """Ensures cross-skill contamination questions are strictly rejected."""
    java_profile = SkillProfiler.get_profile("Java")

    # Contaminated question (DOM in Java)
    bad_q = GeneratedQuestion(
        skill="Java",
        knowledge_area="OOP & Core Semantics",
        question_type="conceptual",
        difficulty="EASY",
        question_text="How does event bubbling in the DOM affect Java execution?",
        options=["It bubbles events", "It does nothing", "It crashes JVM", "None of above"],
        correct_option=0,
        explanation="DOM event bubbling.",
        expected_concepts=["DOM"]
    )
    result = QuestionValidator.validate_question(bad_q, java_profile)
    assert not result.is_valid
    assert "Cross-skill contamination rejected" in result.rejection_reason

    # Valid Java question
    good_q = GeneratedQuestion(
        skill="Java",
        knowledge_area="JVM Architecture & Memory Model",
        question_type="conceptual",
        difficulty="EASY",
        question_text="Which component of Java is responsible for executing bytecode at runtime?",
        options=["Java Virtual Machine (JVM)", "Java Development Kit (JDK)", "javac compiler", "javadoc tool"],
        correct_option=0,
        explanation="JVM executes bytecode.",
        expected_concepts=["JVM"]
    )
    good_result = QuestionValidator.validate_question(good_q, java_profile)
    assert good_result.is_valid


def test_ten_question_distribution_and_generation():
    """Verifies that SkillEngine produces exactly 10 questions with 3 Easy, 4 Intermediate, 3 Hard."""
    skills_to_test = ["Java", "DevOps", "Public Speaking", "Problem Solving", "Arecanut Farming"]

    for s_name in skills_to_test:
        questions = SkillEngine.generate_assessment_for_skill(s_name)
        assert len(questions) == 10, f"Expected 10 questions for {s_name}, got {len(questions)}"

        diffs = [q.difficulty.upper() for q in questions]
        easy_count = sum(1 for d in diffs if d in ["EASY", "BEGINNER"])
        inter_count = sum(1 for d in diffs if d in ["INTERMEDIATE", "MEDIUM"])
        hard_count = sum(1 for d in diffs if d in ["HARD", "ADVANCED"])

        assert easy_count == 3, f"Expected 3 Easy for {s_name}, got {easy_count}"
        assert inter_count == 4, f"Expected 4 Intermediate for {s_name}, got {inter_count}"
        assert hard_count == 3, f"Expected 3 Hard for {s_name}, got {hard_count}"

        # Ensure each question has 4 distinct options
        for q in questions:
            assert len(q.options) == 4
            assert 0 <= q.correct_option <= 3
            assert len(set(q.options)) == 4


def test_assessment_evaluation_and_verification_scoring():
    """Verifies real performance-based scoring and verified status progression."""
    db = TestingSessionLocal()
    try:
        # Create user and skill
        user = User(
            email="learner@test.com",
            password_hash="pw",
            name="Learner One"
        )
        db.add(user)
        skill = Skill(name="DevOps", category="Infrastructure")
        db.add(skill)
        db.flush()

        user_skill = UserSkill(
            user_id=user.id,
            skill_id=skill.id,
            type="teach",
            verification_status="CLAIMED"
        )
        db.add(user_skill)
        db.commit()

        # Generate questions
        questions = ensure_ten_questions_for_skill(db, skill)
        assert len(questions) == 10

        # Scenario 1: User fails assessment (score 50% < 70%)
        # Answer 5 correctly, 5 incorrectly
        fail_answers = []
        for idx, q in enumerate(questions):
            selected = q.correct_option if idx < 5 else (q.correct_option + 1) % 4
            fail_answers.append({"question_id": q.id, "selected_option": selected})

        res_fail = evaluate_and_submit_assessment(db, user.id, skill.id, fail_answers)
        assert res_fail["score"] == 50.0
        assert res_fail["passed"] is False
        assert res_fail["new_verification_status"] == "ASSESSED"

        # Scenario 2: User passes assessment (score 90% >= 70%)
        pass_answers = []
        for idx, q in enumerate(questions):
            selected = q.correct_option if idx < 9 else (q.correct_option + 1) % 4
            pass_answers.append({"question_id": q.id, "selected_option": selected})

        res_pass = evaluate_and_submit_assessment(db, user.id, skill.id, pass_answers)
        assert res_pass["score"] == 90.0
        assert res_pass["passed"] is True
        assert res_pass["new_verification_status"] == "VERIFIED"

        # Verify learning activity was persisted
        activity = (
            db.query(LearningActivity)
            .filter(LearningActivity.user_id == user.id, LearningActivity.activity_type == "skill_verified")
            .first()
        )
        assert activity is not None
        assert activity.activity_data["score"] == 90.0

    finally:
        db.close()
