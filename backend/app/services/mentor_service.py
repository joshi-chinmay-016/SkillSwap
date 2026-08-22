from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.repositories.mentor_repository import (
    get_teaching_users,
    get_teaching_users_by_skill
)

from app.repositories.recommendation_repository import (
    get_average_rating,
    get_completed_sessions
)


def discover_mentors(
    db: Session,
    skill: Optional[str] = None,
    min_rating: Optional[float] = None,
    page: int = 1,
    size: int = 50,
    exclude_user_id: Optional[int] = None
) -> List[Dict[str, Any]]:

    if skill and skill.strip():
        mentors = get_teaching_users_by_skill(
            db,
            skill.strip(),
            exclude_user_id=exclude_user_id
        )
    else:
        mentors = get_teaching_users(
            db,
            exclude_user_id=exclude_user_id
        )

    results = []

    for mentor in mentors:
        rating = get_average_rating(
            db,
            mentor.id
        )
        rating = float(rating or 0)

        completed_sessions = get_completed_sessions(
            db,
            mentor.id
        )

        if min_rating is not None and rating < min_rating:
            continue

        teach_skills = [
            us.skill.name
            for us in getattr(mentor, "user_skills", [])
            if (us.type or "").lower() == "teach" and getattr(us, "skill", None)
        ]

        # Determine highest credibility status among teaching skills
        statuses = [
            getattr(us, "verification_status", "CLAIMED") or "CLAIMED"
            for us in getattr(mentor, "user_skills", [])
            if (us.type or "").lower() == "teach"
        ]
        if "VERIFIED" in statuses:
            best_status = "VERIFIED"
        elif "ASSESSED" in statuses:
            best_status = "ASSESSED"
        else:
            best_status = "CLAIMED"

        profile = getattr(mentor, "profile", None)
        email = (mentor.email or "").lower()
        is_real = not any(pat in email for pat in ["@example.com", "verify_test", "test_pipeline"])

        results.append(
            {
                "id": mentor.id,
                "mentor_id": mentor.id,
                "name": mentor.name,
                "mentor_name": mentor.name,
                "avatar_url": getattr(profile, "avatar_url", None),
                "department": getattr(profile, "department", None),
                "year": getattr(profile, "year", None),
                "average_rating": round(rating, 2),
                "rating": round(rating, 2),
                "completed_sessions": completed_sessions,
                "skills": teach_skills,
                "matched_skills": teach_skills,
                "verification_status": best_status,
                "is_real": is_real
            }
        )

    # Prioritize real users, verified status, high rating, and recency (newly registered users)
    results.sort(
        key=lambda x: (
            1 if x.get("is_real", True) else 0,
            2 if x["verification_status"] == "VERIFIED" else (1 if x["verification_status"] == "ASSESSED" else 0),
            x["average_rating"] if x["average_rating"] > 0 else 0,
            x["completed_sessions"],
            x["id"]
        ),
        reverse=True
    )

    start = (page - 1) * size
    end = start + size

    return results[start:end]