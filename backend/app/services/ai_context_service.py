"""
AI Context Service — builds, retrieves, and updates the user's
persistent Learning AI Profile.

The profile is an aggregation of:
  - Completed session count
  - Session summary strengths → strong_topics
  - Session summary weaknesses → weak_topics
  - Session summary follow_up_topics → recommended_topics
  - Active learning journey target roles → learning_interests
  - Deterministic overall_summary narrative
  - Inferred learning_style from session patterns
"""
import logging
from collections import Counter
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.ai_context import AIContext
from app.models.learning_session import LearningSession
from app.models.session_summary import SessionSummary
from app.models.journey import LearningJourney
from app.schemas.ai_context import AIContextUpdate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_user_ai_context(db: Session, user_id: int) -> Optional[AIContext]:
    """
    Retrieve the persistent AI Context for a given user_id.
    Returns None if no context exists yet.
    """
    try:
        return (
            db.query(AIContext)
            .filter(AIContext.user_id == user_id)
            .first()
        )
    except Exception as exc:
        logger.error("Failed to fetch AIContext for user_id=%d: %s", user_id, str(exc))
        return None


# ---------------------------------------------------------------------------
# Rebuild (aggregation engine)
# ---------------------------------------------------------------------------

def rebuild_user_ai_context(db: Session, user_id: int) -> Optional[AIContext]:
    """
    Rebuild the user's Learning AI Profile from scratch by aggregating
    all completed sessions, session summaries, and active learning journeys.

    Creates the AIContext row if it doesn't exist, or updates it in-place.
    Does NOT commit — caller owns the transaction.

    Returns the updated AIContext, or None on error.
    """
    try:
        # ── 1. Completed sessions ────────────────────────────────────────
        completed_sessions = (
            db.query(LearningSession)
            .filter(
                LearningSession.user_id == user_id,
                LearningSession.status == "COMPLETED",
            )
            .all()
        )
        completed_count = len(completed_sessions)
        completed_ids = [s.id for s in completed_sessions]

        # ── 2. Session summaries for those sessions ──────────────────────
        summaries: list[SessionSummary] = []
        if completed_ids:
            summaries = (
                db.query(SessionSummary)
                .filter(SessionSummary.session_id.in_(completed_ids))
                .all()
            )

        # ── 3. Aggregate topics from summaries ───────────────────────────
        strong_topics = _aggregate_topics(
            [s.strengths for s in summaries if s.strengths]
        )
        weak_topics = _aggregate_topics(
            [s.weaknesses for s in summaries if s.weaknesses]
        )
        recommended_topics = _aggregate_topics(
            [s.follow_up_topics for s in summaries if s.follow_up_topics]
        )

        # ── 4. Learning interests from active journeys ───────────────────
        journeys = (
            db.query(LearningJourney)
            .filter(
                LearningJourney.user_id == user_id,
                LearningJourney.status == "active",
            )
            .all()
        )
        learning_interests = _extract_journey_interests(journeys)

        # ── 5. Build overall summary (deterministic template) ────────────
        overall_summary = _build_overall_summary(
            completed_count=completed_count,
            strong_topics=strong_topics,
            weak_topics=weak_topics,
            journeys=journeys,
        )

        # ── 6. Infer learning style ─────────────────────────────────────
        learning_style = _infer_learning_style(
            completed_count=completed_count,
            summaries=summaries,
            journeys=journeys,
        )

        # ── 7. Upsert AIContext ──────────────────────────────────────────
        context = (
            db.query(AIContext)
            .filter(AIContext.user_id == user_id)
            .first()
        )

        if context:
            context.overall_summary = overall_summary
            context.strong_topics = strong_topics
            context.weak_topics = weak_topics
            context.learning_interests = learning_interests
            context.recommended_topics = recommended_topics
            context.learning_style = learning_style
            context.completed_sessions = completed_count
            context.context_version = (context.context_version or 0) + 1
        else:
            context = AIContext(
                user_id=user_id,
                overall_summary=overall_summary,
                strong_topics=strong_topics,
                weak_topics=weak_topics,
                learning_interests=learning_interests,
                recommended_topics=recommended_topics,
                learning_style=learning_style,
                completed_sessions=completed_count,
                context_version=1,
            )
            db.add(context)

        db.flush()  # Ensure the row gets an id without committing
        logger.info(
            "AI Context rebuilt for user_id=%d: version=%d, sessions=%d, "
            "strong=%d, weak=%d, recommended=%d",
            user_id,
            context.context_version,
            completed_count,
            len(strong_topics),
            len(weak_topics),
            len(recommended_topics),
        )
        return context

    except Exception as exc:
        logger.error(
            "Failed to rebuild AI Context for user_id=%d: %s",
            user_id,
            str(exc),
        )
        return None


# ---------------------------------------------------------------------------
# Update (user-editable fields only)
# ---------------------------------------------------------------------------

def update_user_ai_context(
    db: Session,
    user_id: int,
    data: AIContextUpdate,
) -> Optional[AIContext]:
    """
    Update user-editable fields on the AI profile.
    Only learning_interests and learning_style can be manually overridden.

    Does NOT commit — caller owns the transaction.
    Returns updated AIContext or None if not found.
    """
    context = (
        db.query(AIContext)
        .filter(AIContext.user_id == user_id)
        .first()
    )

    if not context:
        return None

    if data.learning_interests is not None:
        context.learning_interests = data.learning_interests

    if data.learning_style is not None:
        context.learning_style = data.learning_style

    context.context_version = (context.context_version or 0) + 1
    db.flush()

    logger.info(
        "AI Context updated (manual) for user_id=%d: version=%d",
        user_id,
        context.context_version,
    )
    return context


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _aggregate_topics(topic_lists: list[list]) -> List[str]:
    """
    Flatten nested lists of topic strings, count frequency,
    and return deduplicated list sorted by frequency (most common first).
    Caps at 15 topics.
    """
    counter: Counter = Counter()
    for topics in topic_lists:
        for topic in topics:
            if isinstance(topic, str) and topic.strip():
                counter[topic.strip()] += 1

    # Return most common, capped at 15
    return [t for t, _ in counter.most_common(15)]


def _extract_journey_interests(journeys: list[LearningJourney]) -> List[str]:
    """
    Extract learning interests from active journeys:
    - Journey titles
    - Target roles
    Deduplicated, ordered by journey creation (most recent first).
    """
    seen: set[str] = set()
    interests: list[str] = []

    for j in sorted(journeys, key=lambda x: x.created_at, reverse=True):
        for value in [j.target_role, j.title]:
            if value and value.strip() and value.strip() not in seen:
                seen.add(value.strip())
                interests.append(value.strip())

    return interests[:10]  # Cap at 10


def _build_overall_summary(
    completed_count: int,
    strong_topics: List[str],
    weak_topics: List[str],
    journeys: list,
) -> str:
    """
    Build a deterministic narrative summary of the learner's profile.
    No LLM call — pure template logic.
    """
    parts: list[str] = []

    # Completion status
    if completed_count == 0:
        parts.append("This learner has not yet completed any sessions.")
    elif completed_count == 1:
        parts.append("This learner has completed 1 learning session.")
    else:
        parts.append(f"This learner has completed {completed_count} learning sessions.")

    # Strengths
    if strong_topics:
        top_strong = ", ".join(strong_topics[:5])
        parts.append(f"They have demonstrated strength in: {top_strong}.")

    # Weaknesses
    if weak_topics:
        top_weak = ", ".join(weak_topics[:5])
        parts.append(f"Areas that need improvement include: {top_weak}.")

    # Active journeys
    active_journey_count = len(journeys)
    if active_journey_count == 1:
        j = journeys[0]
        parts.append(
            f"They are currently pursuing \"{j.title}\" targeting the "
            f"\"{j.target_role}\" role at {j.progress_percentage:.0f}% progress."
        )
    elif active_journey_count > 1:
        titles = ", ".join(f'"{j.title}"' for j in journeys[:3])
        parts.append(
            f"They are actively working on {active_journey_count} learning "
            f"journeys: {titles}."
        )
    else:
        parts.append("They do not have any active learning journeys.")

    return " ".join(parts)


def _infer_learning_style(
    completed_count: int,
    summaries: list,
    journeys: list,
) -> str:
    """
    Infer a learning style description from session patterns.
    Deterministic heuristic — no LLM.
    """
    traits: list[str] = []

    # Session frequency pattern
    if completed_count >= 10:
        traits.append("Consistent and dedicated learner")
    elif completed_count >= 5:
        traits.append("Regular learner building momentum")
    elif completed_count >= 1:
        traits.append("Early-stage learner exploring topics")
    else:
        return "New learner — no sessions completed yet."

    # Topic diversity
    all_takeaways: list[str] = []
    for s in summaries:
        if s.key_takeaways:
            all_takeaways.extend(s.key_takeaways)
    unique_takeaways = len(set(all_takeaways))

    if unique_takeaways > 15:
        traits.append("broad learner exploring many topics")
    elif unique_takeaways > 5:
        traits.append("focused learner with moderate topic range")
    elif unique_takeaways >= 1:
        traits.append("deep-diver concentrating on specific areas")

    # Journey engagement
    if len(journeys) > 1:
        traits.append("pursues multiple learning paths simultaneously")
    elif len(journeys) == 1:
        traits.append("follows a structured single-journey approach")

    # Strengths vs weaknesses balance
    all_strengths = sum(1 for s in summaries if s.strengths and len(s.strengths) > 0)
    all_weaknesses = sum(1 for s in summaries if s.weaknesses and len(s.weaknesses) > 0)

    if all_strengths > all_weaknesses * 2:
        traits.append("demonstrates strong conceptual understanding")
    elif all_weaknesses > all_strengths:
        traits.append("benefits from step-by-step explanations and analogies")

    return ". ".join(t.capitalize() if i == 0 else t for i, t in enumerate(traits)) + "."
