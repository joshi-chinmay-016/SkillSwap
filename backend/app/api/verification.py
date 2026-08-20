from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.verification import (
    AssessmentDetailResponse,
    AssessmentSubmissionRequest,
    AssessmentSubmissionResultResponse,
    SkillCredibilityResponse,
    UserOverallCredibilityResponse,
)
from app.services.assessment_service import (
    get_assessment_for_skill,
    evaluate_and_submit_assessment,
    get_user_assessment_history,
)
from app.services.credibility_service import (
    get_skill_credibility_breakdown,
    get_user_overall_credibility,
)

router = APIRouter(
    prefix="/verification",
    tags=["Verification & Credibility"]
)


@router.get(
    "/skills/{skill_id}/assessment",
    response_model=AssessmentDetailResponse
)
def get_assessment_questions_endpoint(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get skill assessment questions. Answers are hidden from response.
    """
    return get_assessment_for_skill(db, skill_id)


@router.post(
    "/skills/{skill_id}/assessment",
    response_model=AssessmentSubmissionResultResponse
)
def submit_assessment_endpoint(
    skill_id: int,
    request: AssessmentSubmissionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit assessment answers. Evaluated server-side. Updates skill verification status.
    """
    answers = [a.model_dump() for a in request.answers]
    return evaluate_and_submit_assessment(
        db=db,
        user_id=current_user.id,
        skill_id=skill_id,
        answers=answers
    )


@router.get(
    "/skills/{skill_id}/assessment/results"
)
def get_assessment_results_endpoint(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    View user's assessment attempt history for a skill.
    """
    return get_user_assessment_history(
        db=db,
        user_id=current_user.id,
        skill_id=skill_id
    )


@router.get(
    "/credibility/me",
    response_model=UserOverallCredibilityResponse
)
def get_my_overall_credibility_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get authenticated user's overall credibility and skill verification summary.
    """
    return get_user_overall_credibility(
        db=db,
        user_id=current_user.id
    )


@router.get(
    "/credibility/user/{user_id}",
    response_model=UserOverallCredibilityResponse
)
def get_user_credibility_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get public credibility summary of any user (used on mentor profiles).
    """
    return get_user_overall_credibility(
        db=db,
        user_id=user_id
    )


@router.get(
    "/skills/{skill_id}/credibility",
    response_model=SkillCredibilityResponse
)
def get_skill_credibility_endpoint(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get detailed credibility breakdown for a specific skill of current user.
    """
    return get_skill_credibility_breakdown(
        db=db,
        user_id=current_user.id,
        skill_id=skill_id
    )
