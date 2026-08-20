import json
from sqlalchemy.orm import Session

from app.core.redis import redis_client
from app.repositories.recommendation_repository import (
    get_user_skills_by_type,
    get_candidate_mentors_for_skills,
    get_profile_by_user_id,
    get_user_active_journeys,
    get_average_rating,
    get_completed_sessions,
    get_feedback_count,
    has_availability,
    get_user_name,
)
from app.services.credibility_service import get_skill_credibility_breakdown


def calculate_candidate_score_and_reasons(
    db: Session,
    current_user_id: int,
    candidate_id: int,
    candidate_user_skill,
    user_learn_skills_map: dict,
    user_teach_skill_ids: set,
    active_journey_targets: list[str]
) -> dict:
    """
    Computes a deterministic, explainable compatibility score (0-100) and evidence-backed
    reasons list strictly derived from real database facts.
    """
    skill = candidate_user_skill.skill
    skill_id = candidate_user_skill.skill_id
    skill_name = skill.name if skill else f"Skill #{skill_id}"

    # 1. Base Skill Compatibility
    score = 40.0
    matched_skills = [skill_name]
    reasons = []

    # Reason 1: Direct skill match
    reasons.append(f"Can teach {skill_name}, which you want to learn.")

    # Mutual Skill Swap Check: Check if candidate wants to learn something current user teaches
    candidate_learn_skills = get_user_skills_by_type(db, candidate_id, "learn")
    candidate_learn_ids = {s.skill_id for s in candidate_learn_skills}

    mutual_matches = candidate_learn_ids.intersection(user_teach_skill_ids)
    if mutual_matches:
        score += 15.0
        reasons.append("Perfect skill swap! Candidate wants to learn a skill you can teach.")

    # 2. Day 78 Part A Credibility Signal
    credibility_info = get_skill_credibility_breakdown(db, candidate_id, skill_id)
    v_status = credibility_info.get("verification_status", "CLAIMED")
    c_score = credibility_info.get("credibility_score", 0.0)
    assessment = credibility_info.get("assessment", {})

    if v_status == "TRUSTED":
        score += 20.0
        reasons.append("Earned Trusted Mentor status via exceptional rating & session history.")
    elif v_status == "VERIFIED":
        score += 15.0
        score_val = assessment.get("latest_score")
        if score_val is not None:
            reasons.append(f"Verified skill in {skill_name} via assessment (score: {score_val}%).")
        else:
            reasons.append(f"Verified skill in {skill_name}.")
    elif v_status == "ASSESSED":
        score += 5.0
        reasons.append(f"Completed skill assessment for {skill_name}.")

    # 3. Learner Reputation & Feedback Signal
    avg_rating = get_average_rating(db, candidate_id)
    feedback_cnt = get_feedback_count(db, candidate_id)

    if feedback_cnt > 0:
        score += (avg_rating / 5.0) * 10.0
        if avg_rating >= 4.5:
            reasons.append(f"Strong learner feedback: {avg_rating:.1f}/5.0 stars ({feedback_cnt} reviews).")
        else:
            reasons.append(f"Received {feedback_cnt} learner review(s) with an average of {avg_rating:.1f}/5.0.")

    # 4. Availability Compatibility Signal
    avail = has_availability(db, candidate_id)
    if avail:
        score += 10.0
        reasons.append("Has open availability slots for booking.")

    # 5. Learning Journey / Goal Alignment Signal
    for journey_title in active_journey_targets:
        if skill_name.lower() in journey_title.lower():
            score += 5.0
            reasons.append(f"Matches your active learning goal: '{journey_title}'.")
            break

    # 6. Completed Sessions Signal
    completed_sessions = get_completed_sessions(db, candidate_id)
    if completed_sessions > 0:
        score += min(completed_sessions * 1.0, 5.0)
        reasons.append(f"Completed {completed_sessions} successful teaching session(s).")

    final_score = round(min(score, 100.0), 1)

    return {
        "mentor_id": candidate_id,
        "mentor_name": candidate_user_skill.user.name if candidate_user_skill.user else get_user_name(db, candidate_id),
        "compatibility_score": final_score,
        "mentor_score": round(c_score, 1),
        "availability": avail,
        "average_rating": round(avg_rating, 2),
        "completed_sessions": completed_sessions,
        "feedback_count": feedback_cnt,
        "verification_status": v_status,
        "credibility_score": c_score,
        "matched_skills": matched_skills,
        "reasons": reasons
    }


def get_recommendations(
    db: Session,
    current_user_id: int,
    limit: int = 10
) -> list[dict]:
    """
    Generate explainable peer mentor recommendations based on real DB signals.
    """
    cache_key = f"recommendations:v2:user:{current_user_id}:limit:{limit}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception:
        pass

    # 1. Fetch current user's learn & teach skills
    user_learn_skills = get_user_skills_by_type(db, current_user_id, "learn")
    if not user_learn_skills:
        return []

    user_learn_map = {s.skill_id: s.skill.name if s.skill else "" for s in user_learn_skills}
    user_learn_ids = list(user_learn_map.keys())

    user_teach_skills = get_user_skills_by_type(db, current_user_id, "teach")
    user_teach_ids = {s.skill_id for s in user_teach_skills}

    # 2. Fetch active learning journey targets
    active_journeys = get_user_active_journeys(db, current_user_id)
    journey_targets = [j.title for j in active_journeys]

    # 3. Retrieve candidate mentor skill records from DB
    candidates = get_candidate_mentors_for_skills(db, current_user_id, user_learn_ids)

    recommendations = []
    seen_mentor_ids = set()

    for cand_skill in candidates:
        mentor_id = cand_skill.user_id
        if mentor_id in seen_mentor_ids or mentor_id == current_user_id:
            continue

        # Get profile data for candidate (privacy safe)
        profile = get_profile_by_user_id(db, mentor_id)
        avatar_url = profile.avatar_url if profile else None
        department = profile.department if profile else None
        year = profile.year if profile else None

        item = calculate_candidate_score_and_reasons(
            db=db,
            current_user_id=current_user_id,
            candidate_id=mentor_id,
            candidate_user_skill=cand_skill,
            user_learn_skills_map=user_learn_map,
            user_teach_skill_ids=user_teach_ids,
            active_journey_targets=journey_targets
        )

        item["avatar_url"] = avatar_url
        item["department"] = department
        item["year"] = year

        recommendations.append(item)
        seen_mentor_ids.add(mentor_id)

    # Sort deterministically by compatibility_score (descending)
    recommendations.sort(key=lambda x: x["compatibility_score"], reverse=True)
    results = recommendations[:limit]

    try:
        redis_client.setex(cache_key, 300, json.dumps(results))
    except Exception:
        pass

    return results