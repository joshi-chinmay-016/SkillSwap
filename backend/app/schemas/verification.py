from pydantic import BaseModel, ConfigDict
from typing import Any


class AssessmentQuestionResponse(BaseModel):
    id: int
    skill_id: int
    question_text: str
    options: list[str]
    difficulty: str


class AssessmentDetailResponse(BaseModel):
    skill_id: int
    skill_name: str
    total_questions: int
    passing_threshold_percent: float = 70.0
    questions: list[AssessmentQuestionResponse]


class AssessmentAnswerItem(BaseModel):
    question_id: int
    selected_option: int


class AssessmentSubmissionRequest(BaseModel):
    answers: list[AssessmentAnswerItem]


class AssessmentSubmissionResultResponse(BaseModel):
    assessment_id: int
    user_id: int
    skill_id: int
    user_skill_id: int
    score: float
    passed: bool
    total_questions: int
    correct_answers: int
    new_verification_status: str
    details: list[dict[str, Any]]


class CredibilitySignalSummary(BaseModel):
    completed_teaching_sessions: int
    feedback_count: int
    average_rating: float
    repeat_learners_count: int


class SkillCredibilityResponse(BaseModel):
    user_id: int
    skill_id: int
    user_skill_id: int | None
    verification_status: str
    credibility_score: float
    claimed_at: str | None
    verified_at: str | None
    assessment: dict[str, Any]
    signals: CredibilitySignalSummary
    explanations: list[str]


class UserOverallCredibilityResponse(BaseModel):
    user_id: int
    overall_credibility_score: float
    total_teach_skills: int
    verified_skills_count: int
    total_completed_sessions: int
    overall_average_rating: float
    total_feedback_count: int
    skills: list[dict[str, Any]]
