from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse
)

from app.services.feedback_service import (
    submit_feedback,
    user_feedback,
    my_rating,
    feedback_stats,
    review_summary
)

from app.schemas.feedback_stats import (
    FeedbackStatsResponse
)
router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"]
)


@router.post(
    "",
    response_model=FeedbackResponse
)
def create_feedback(
    request: FeedbackCreate,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return submit_feedback(
        db,
        request.session_id,
        current_user.id,
        request.reviewee_id,
        request.rating,
        request.comment
    )


@router.get(
    "/user/{user_id}",
    response_model=list[
        FeedbackResponse
    ]
)
def get_feedback(
    user_id: int,
    db: Session = Depends(get_db)
):

    return user_feedback(
        db,
        user_id
    )


@router.get(
    "/my-rating"
)
def get_my_rating(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return {
        "rating": my_rating(
            db,
            current_user.id
        )
    }

@router.get(
    "/stats/{user_id}",
    response_model=FeedbackStatsResponse
)
def get_feedback_stats(
    user_id: int,
    db: Session = Depends(get_db)
):

    return feedback_stats(
        db,
        user_id
    )

@router.get(
    "/review-summary/{user_id}"
)
def get_review_summary(
    user_id: int,
    db: Session = Depends(get_db)
):

    return review_summary(
        db,
        user_id
    )