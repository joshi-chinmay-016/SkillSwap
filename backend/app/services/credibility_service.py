from datetime import datetime
from sqlalchemy.orm import Session

from app.repositories.verification_repository import (
    get_completed_sessions_count_for_mentor,
    get_feedback_summary_for_mentor,
    get_repeat_learners_count,
    get_assessment_results_for_user_skill,
    get_user_skill_by_user_and_skill,
    update_user_skill_verification,
    get_user_skill_by_id
)
from app.repositories.skill_repository import get_user_skills


def calculate_credibility_score(
    verification_status: str,
    assessment_score: float | None,
    completed_sessions: int,
    avg_rating: float,
    feedback_count: int,
    repeat_learners: int
) -> float:
    """
    Derives a transparent 0-100 credibility score based strictly on real evidence:
    - Base status tier: CLAIMED=20, ASSESSED=40, VERIFIED=70, TRUSTED=90
    - Assessment score component (up to 20 pts)
    - Session history component (up to 20 pts, 2 pts per completed session max 20)
    - Rating & feedback component (up to 15 pts)
    - Repeat learners component (up to 5 pts)
    Capped at 100.
    """
    status_weights = {
        "CLAIMED": 20.0,
        "ASSESSED": 40.0,
        "VERIFIED": 70.0,
        "TRUSTED": 90.0,
    }
    score = status_weights.get(verification_status, 20.0)

    # Assessment bonus
    if assessment_score is not None:
        score += (assessment_score / 100.0) * 15.0

    # Session bonus: 2 points per completed session up to 20
    score += min(completed_sessions * 2.0, 20.0)

    # Rating bonus if feedback exists
    if feedback_count > 0:
        score += (avg_rating / 5.0) * 10.0 + min(feedback_count * 0.5, 5.0)

    # Repeat learners bonus
    score += min(repeat_learners * 2.5, 5.0)

    return round(min(score, 100.0), 1)


def evaluate_credibility_tier_progression(
    verification_status: str,
    assessment_score: float | None,
    completed_sessions: int,
    avg_rating: float,
    feedback_count: int
) -> str:
    """
    Determines if user skill status should progress to TRUSTED based on real evidence.
    Note: CLAIMED -> ASSESSED -> VERIFIED happens through assessment passing,
    VERIFIED -> TRUSTED happens when mentor builds high real-world credibility.
    """
    if verification_status == "VERIFIED":
        # Requires at least 3 completed teaching sessions and avg_rating >= 4.5
        if completed_sessions >= 3 and feedback_count >= 2 and avg_rating >= 4.5:
            return "TRUSTED"
    return verification_status


def get_skill_credibility_breakdown(
    db: Session,
    user_id: int,
    skill_id: int
) -> dict:
    user_skill = get_user_skill_by_user_and_skill(db, user_id, skill_id, skill_type="teach")
    
    # If not a teach skill explicitly, check any skill entry for user
    if not user_skill:
        user_skill = get_user_skill_by_user_and_skill(db, user_id, skill_id)

    verification_status = user_skill.verification_status if user_skill else "UNCLAIMED"
    score_recorded = user_skill.score if user_skill else None
    claimed_at = user_skill.claimed_at.isoformat() if user_skill and user_skill.claimed_at else None
    verified_at = user_skill.verified_at.isoformat() if user_skill and user_skill.verified_at else None

    # Real evidence signals
    completed_sessions = get_completed_sessions_count_for_mentor(db, user_id, skill_id)
    feedback_summary = get_feedback_summary_for_mentor(db, user_id)
    repeat_learners = get_repeat_learners_count(db, user_id)
    
    assessment_results = get_assessment_results_for_user_skill(db, user_id, skill_id)
    latest_result = assessment_results[0] if assessment_results else None

    latest_assessment_score = latest_result.score if latest_result else score_recorded
    assessment_passed = latest_result.passed if latest_result else (score_recorded is not None and score_recorded >= 70.0)

    # Check for tier promotion (VERIFIED -> TRUSTED)
    if user_skill and verification_status == "VERIFIED":
        new_status = evaluate_credibility_tier_progression(
            verification_status,
            latest_assessment_score,
            completed_sessions,
            feedback_summary["average_rating"],
            feedback_summary["count"]
        )
        if new_status != verification_status:
            update_user_skill_verification(db, user_skill.id, new_status, verified_at=datetime.utcnow())
            verification_status = new_status

    credibility_score = calculate_credibility_score(
        verification_status,
        latest_assessment_score,
        completed_sessions,
        feedback_summary["average_rating"],
        feedback_summary["count"],
        repeat_learners
    )

    # Build human-readable, transparent explanations
    explanations = []
    if verification_status == "CLAIMED":
        explanations.append("Skill claimed by user. Assessment required to achieve VERIFIED status.")
    elif verification_status == "ASSESSED":
        explanations.append(f"Assessment completed with score {latest_assessment_score}%. Re-evaluate or complete session history for verification.")
    elif verification_status == "VERIFIED":
        explanations.append("Skill verified via successful assessment demonstration.")
    elif verification_status == "TRUSTED":
        explanations.append("Top-tier mentor status earned through high assessment scores, completed sessions, and strong learner feedback.")

    if completed_sessions > 0:
        explanations.append(f"Completed {completed_sessions} real teaching session(s).")
    else:
        explanations.append("No completed teaching sessions recorded yet.")

    if feedback_summary["count"] > 0:
        explanations.append(f"Received {feedback_summary['count']} rating(s) with an average of {feedback_summary['average_rating']}/5.0.")
    else:
        explanations.append("No learner feedback ratings recorded yet.")

    if repeat_learners > 0:
        explanations.append(f"{repeat_learners} learner(s) booked multiple sessions.")

    return {
        "user_id": user_id,
        "skill_id": skill_id,
        "user_skill_id": user_skill.id if user_skill else None,
        "verification_status": verification_status,
        "credibility_score": credibility_score,
        "claimed_at": claimed_at,
        "verified_at": verified_at,
        "assessment": {
            "attempted": latest_result is not None or score_recorded is not None,
            "latest_score": latest_assessment_score,
            "passed": assessment_passed,
            "total_attempts": len(assessment_results)
        },
        "signals": {
            "completed_teaching_sessions": completed_sessions,
            "feedback_count": feedback_summary["count"],
            "average_rating": feedback_summary["average_rating"],
            "repeat_learners_count": repeat_learners
        },
        "explanations": explanations
    }


def get_user_overall_credibility(
    db: Session,
    user_id: int
) -> dict:
    all_user_skills = get_user_skills(db, user_id)
    teach_skills = [s for s in all_user_skills if s.type == "teach"]

    skills_breakdown = []
    total_score = 0.0

    for s in teach_skills:
        breakdown = get_skill_credibility_breakdown(db, user_id, s.skill_id)
        skills_breakdown.append({
            "skill_id": s.skill_id,
            "skill_name": s.skill.name if s.skill else None,
            "verification_status": breakdown["verification_status"],
            "credibility_score": breakdown["credibility_score"],
            "assessment_score": breakdown["assessment"]["latest_score"]
        })
        total_score += breakdown["credibility_score"]

    avg_credibility = round(total_score / len(teach_skills), 1) if teach_skills else 0.0

    # Overall feedback & sessions summary
    feedback_summary = get_feedback_summary_for_mentor(db, user_id)
    completed_sessions = get_completed_sessions_count_for_mentor(db, user_id)

    return {
        "user_id": user_id,
        "overall_credibility_score": avg_credibility,
        "total_teach_skills": len(teach_skills),
        "verified_skills_count": sum(1 for sb in skills_breakdown if sb["verification_status"] in ["VERIFIED", "TRUSTED"]),
        "total_completed_sessions": completed_sessions,
        "overall_average_rating": feedback_summary["average_rating"],
        "total_feedback_count": feedback_summary["count"],
        "skills": skills_breakdown
    }
