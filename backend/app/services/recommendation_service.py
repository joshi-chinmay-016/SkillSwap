import json
import math
import re
from collections import Counter
from sqlalchemy.orm import Session

from app.core.redis import redis_client
from app.repositories.recommendation_repository import (
    get_user_skills_by_type,
    get_all_candidate_teach_skills,
    get_profile_by_user_id,
    get_user_active_journeys,
    get_average_rating,
    get_completed_sessions,
    get_feedback_count,
    has_availability,
    get_user_name,
)
from app.services.credibility_service import get_skill_credibility_breakdown


# ──────────────────────────────────────────────────────────────────────────────
# HYBRID SEARCH ENGINE (BM25 + SUB-WORD SEMANTIC VECTOR SIMILARITY)
# ──────────────────────────────────────────────────────────────────────────────

def tokenize_text(text: str) -> list[str]:
    return [w for w in re.findall(r'\b[a-zA-Z0-9+#]+\b', text.lower()) if len(w) > 1]


def compute_bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    avg_doc_len: float,
    doc_freqs: dict[str, int],
    total_docs: int,
    k1: float = 1.5,
    b: float = 0.75
) -> float:
    """
    Computes Okapi BM25 Term Relevance score.
    """
    if not doc_tokens or not query_tokens:
        return 0.0

    score = 0.0
    doc_len = len(doc_tokens)
    doc_counter = Counter(doc_tokens)

    for q in query_tokens:
        if q not in doc_counter:
            continue
        freq = doc_counter[q]
        df = doc_freqs.get(q, 1)

        # Okapi BM25 IDF formula
        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
        num = freq * (k1 + 1.0)
        den = freq + k1 * (1.0 - b + b * (doc_len / (avg_doc_len or 1.0)))
        score += idf * (num / den)

    return score


def compute_semantic_vector_similarity(query_text: str, doc_text: str) -> float:
    """
    Computes sub-word character n-gram cosine similarity (semantic vector matching).
    Includes universal collision protection (e.g., 'java' vs 'javascript', 'c' vs 'c++').
    """
    q_norm = query_text.lower().strip()
    d_norm = doc_text.lower().strip()

    if q_norm == d_norm:
        return 1.0

    q_tokens = set(re.findall(r'[a-z0-9+#]+', q_norm))
    d_tokens = set(re.findall(r'[a-z0-9+#]+', d_norm))

    # Universal Collision Protection Rules
    if ("java" in q_tokens and "javascript" in d_tokens) or ("java" in d_tokens and "javascript" in q_tokens):
        return 0.05
    if ("c" in q_tokens and ("c++" in d_tokens or "c#" in d_tokens)) or ("c" in d_tokens and ("c++" in q_tokens or "c#" in q_tokens)):
        return 0.05
    if ("html" in q_tokens and "html5" in d_tokens) or ("html" in d_tokens and "html5" in q_tokens):
        return 0.95

    def get_ngrams(text, n=3):
        padded = f" {text} "
        return [padded[i:i+n] for i in range(len(padded)-n+1)]

    q_vec = Counter(get_ngrams(q_norm))
    d_vec = Counter(get_ngrams(d_norm))

    intersection = set(q_vec.keys()) & set(d_vec.keys())
    if not intersection:
        return 0.0

    dot = sum(q_vec[k] * d_vec[k] for k in intersection)
    q_mag = math.sqrt(sum(v*v for v in q_vec.values()))
    d_mag = math.sqrt(sum(v*v for v in d_vec.values()))

    if not q_mag or not d_mag:
        return 0.0

    return dot / (q_mag * d_mag)



# ──────────────────────────────────────────────────────────────────────────────
# MULTI-SIGNAL RECOMMENDATION EVALUATION
# ──────────────────────────────────────────────────────────────────────────────

def calculate_candidate_score_and_reasons(
    db: Session,
    current_user_id: int,
    candidate_id: int,
    candidate_user_skill,
    user_learn_skills_map: dict,
    user_teach_skill_ids: set,
    active_journey_targets: list[str],
    avg_doc_len: float,
    doc_freqs: dict[str, int],
    total_docs: int
) -> dict | None:
    """
    Computes a deterministic, explainable compatibility score (0-100) using:
    - Hybrid Search (BM25 Keyword Scoring + Sub-word Semantic Similarity)
    - Mutual Skill Swap Direction
    - Day 78 Part A Credibility Signal
    - Learner Reputation & Feedback
    - Availability Compatibility
    - Session History
    """
    skill = candidate_user_skill.skill
    skill_id = candidate_user_skill.skill_id
    skill_name = skill.name if skill else f"Skill #{skill_id}"
    skill_cat = skill.category if skill and skill.category else ""

    doc_text = f"{skill_name} {skill_cat}"
    doc_tokens = tokenize_text(doc_text)

    # 1. Compute BM25 + Semantic Vector Similarity across user learn skills
    best_semantic_sim = 0.0
    best_matched_learn_name = ""
    best_bm25_score = 0.0

    query_all_tokens = []
    for l_id, l_name in user_learn_skills_map.items():
        l_tokens = tokenize_text(l_name)
        query_all_tokens.extend(l_tokens)

        sim = compute_semantic_vector_similarity(l_name, skill_name)
        if sim > best_semantic_sim:
            best_semantic_sim = sim
            best_matched_learn_name = l_name

    best_bm25_score = compute_bm25_score(
        query_tokens=query_all_tokens,
        doc_tokens=doc_tokens,
        avg_doc_len=avg_doc_len,
        doc_freqs=doc_freqs,
        total_docs=total_docs
    )

    # Hybrid Search Threshold: Require either direct ID match, BM25 score > 0.5, or Semantic Sim > 0.35
    is_direct_id_match = skill_id in user_learn_skills_map
    if not (is_direct_id_match or best_bm25_score > 0.5 or best_semantic_sim > 0.35):
        return None

    # Base Hybrid Score (up to 40 pts)
    score = 20.0
    if is_direct_id_match or best_semantic_sim >= 0.9:
        score += 20.0
    else:
        score += (best_semantic_sim * 15.0) + min(best_bm25_score * 3.0, 5.0)

    matched_skills = [skill_name]
    reasons = []

    # Reason 1: Hybrid BM25 & Semantic Match Explanation
    if is_direct_id_match or best_semantic_sim >= 0.9:
        reasons.append(f"Can teach {skill_name}, which you want to learn.")
    else:
        reasons.append(f"Semantic Match: Teaches {skill_name} (aligns with '{best_matched_learn_name}').")

    # Mutual Skill Swap Check
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

    # 4. Availability Signal
    avail = has_availability(db, candidate_id)
    if avail:
        score += 10.0
        reasons.append("Has open availability slots for booking.")

    # 5. Learning Journey / Goal Alignment Signal
    for journey_title in active_journey_targets:
        journey_sim = compute_semantic_vector_similarity(journey_title, skill_name)
        if journey_sim >= 0.4:
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


def invalidate_user_recommendations_cache(user_id: int):
    """
    Invalidates cached recommendations for a specific user.
    """
    try:
        keys = redis_client.keys(f"recommendations:*:user:{user_id}:*")
        for k in keys:
            redis_client.delete(k)
    except Exception:
        pass


def get_recommendations(
    db: Session,
    current_user_id: int,
    limit: int = 10
) -> list[dict]:
    """
    Generate explainable peer mentor recommendations using Hybrid BM25 + Semantic Vector Search
    with intelligent fallback to top verified mentors when the user hasn't specified learn skills yet.
    """
    cache_key = f"recommendations:v3:user:{current_user_id}:limit:{limit}"
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
    user_teach_skills = get_user_skills_by_type(db, current_user_id, "teach")
    user_teach_ids = {s.skill_id for s in user_teach_skills} if user_teach_skills else set()

    # 2. Fetch active learning journey targets
    active_journeys = get_user_active_journeys(db, current_user_id)
    journey_targets = [j.title for j in active_journeys]

    # 3. Retrieve all candidate teach skills
    all_candidates = get_all_candidate_teach_skills(db, current_user_id)
    if not all_candidates:
        return []

    # Calculate corpus document statistics for BM25
    doc_freqs = Counter()
    total_doc_len = 0
    total_docs = len(all_candidates)

    for cand in all_candidates:
        sk_name = cand.skill.name if cand.skill else ""
        sk_cat = cand.skill.category if cand.skill and cand.skill.category else ""
        tokens = tokenize_text(f"{sk_name} {sk_cat}")
        total_doc_len += len(tokens)
        for t in set(tokens):
            doc_freqs[t] += 1

    avg_doc_len = total_doc_len / (total_docs or 1.0)

    recommendations = []
    seen_mentor_ids = set()

    # Priority 1: Match with learn skills & active journeys
    if user_learn_map:
        for cand_skill in all_candidates:
            mentor_id = cand_skill.user_id
            if mentor_id in seen_mentor_ids or mentor_id == current_user_id:
                continue

            item = calculate_candidate_score_and_reasons(
                db=db,
                current_user_id=current_user_id,
                candidate_id=mentor_id,
                candidate_user_skill=cand_skill,
                user_learn_skills_map=user_learn_map,
                user_teach_skill_ids=user_teach_ids,
                active_journey_targets=journey_targets,
                avg_doc_len=avg_doc_len,
                doc_freqs=doc_freqs,
                total_docs=total_docs
            )

            if item is not None:
                profile = get_profile_by_user_id(db, mentor_id)
                item["avatar_url"] = profile.avatar_url if profile else None
                item["department"] = profile.department if profile else None
                item["year"] = profile.year if profile else None

                recommendations.append(item)
                seen_mentor_ids.add(mentor_id)

    # Priority 2: Fallback / Populate remaining slots with Top Verified Community Mentors
    if len(recommendations) < limit:
        for cand_skill in all_candidates:
            mentor_id = cand_skill.user_id
            if mentor_id in seen_mentor_ids or mentor_id == current_user_id:
                continue

            skill = cand_skill.skill
            skill_name = skill.name if skill else "Peer Mentoring"
            credibility_info = get_skill_credibility_breakdown(db, mentor_id, cand_skill.skill_id)
            v_status = credibility_info.get("verification_status", "CLAIMED")
            c_score = credibility_info.get("credibility_score", 0.0)
            avg_rating = get_average_rating(db, mentor_id)
            feedback_cnt = get_feedback_count(db, mentor_id)
            avail = has_availability(db, mentor_id)
            completed_sess = get_completed_sessions(db, mentor_id)

            # Calculate baseline popularity/credibility score
            base_score = 50.0
            if v_status == "TRUSTED":
                base_score += 25.0
            elif v_status == "VERIFIED":
                base_score += 20.0
            elif v_status == "ASSESSED":
                base_score += 10.0

            if avail:
                base_score += 10.0
            if feedback_cnt > 0:
                base_score += (avg_rating / 5.0) * 10.0

            reasons = [f"Teaches {skill_name} on SkillSwap Arena."]
            if v_status in ("VERIFIED", "TRUSTED"):
                reasons.append(f"Verified expertise in {skill_name}.")
            if avail:
                reasons.append("Open availability for peer sessions.")

            profile = get_profile_by_user_id(db, mentor_id)
            recommendations.append({
                "mentor_id": mentor_id,
                "mentor_name": cand_skill.user.name if cand_skill.user else get_user_name(db, mentor_id),
                "compatibility_score": round(min(base_score, 100.0), 1),
                "mentor_score": round(c_score, 1),
                "availability": avail,
                "average_rating": round(avg_rating, 2),
                "completed_sessions": completed_sess,
                "feedback_count": feedback_cnt,
                "verification_status": v_status,
                "credibility_score": c_score,
                "matched_skills": [skill_name],
                "reasons": reasons,
                "avatar_url": profile.avatar_url if profile else None,
                "department": profile.department if profile else None,
                "year": profile.year if profile else None,
            })
            seen_mentor_ids.add(mentor_id)

    # Sort deterministically by compatibility_score (descending)
    recommendations.sort(key=lambda x: x["compatibility_score"], reverse=True)
    results = recommendations[:limit]

    try:
        redis_client.set(cache_key, json.dumps(results), ex=120)
    except Exception:
        pass

    return results