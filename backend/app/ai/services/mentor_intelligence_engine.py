"""
MentorIntelligenceEngine — analyses the learner's AI Context and question
to produce a PersonalizationMeta struct.

This module contains NO LLM calls — it is pure deterministic logic.
The output feeds directly into MentorPromptBuilder.
"""
import re
import logging
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.ai_context import AIContext

from app.ai.schemas.mentor import PersonalizationMeta

logger = logging.getLogger(__name__)


class MentorIntelligenceEngine:
    """
    Analyses the stored AIContext and the learner's current question,
    then returns a PersonalizationMeta that drives prompt construction.

    Design principles:
    - Never invent data beyond what AIContext contains.
    - Falls back gracefully when context is None.
    - Pure logic — no side effects, no I/O.
    """

    # Threshold for "beginner" vs "intermediate" vs "advanced"
    BEGINNER_SESSION_THRESHOLD = 5
    ADVANCED_SESSION_THRESHOLD = 20

    def analyze(
        self,
        context: Optional["AIContext"],
        question: str,
    ) -> PersonalizationMeta:
        """
        Main entry point. Returns a PersonalizationMeta used by
        MentorPromptBuilder to personalise the mentor prompt.
        """
        if not context:
            logger.info("MentorIntelligenceEngine: no AI context — using generic profile")
            return self._generic_meta()

        question_lower = question.lower()

        topic_is_weak = self._topic_in_list(question_lower, context.weak_topics or [])
        topic_is_strong = self._topic_in_list(question_lower, context.strong_topics or [])

        difficulty = self._infer_difficulty(
            completed_sessions=context.completed_sessions or 0,
            topic_is_weak=topic_is_weak,
            topic_is_strong=topic_is_strong,
        )

        use_analogies = topic_is_weak or difficulty == "Beginner"
        skip_basics = topic_is_strong and difficulty in ("Intermediate", "Advanced")
        build_prerequisites = topic_is_weak

        style_instruction = self._parse_learning_style(context.learning_style or "")

        recommended = self._select_recommendations(
            question_lower=question_lower,
            profile_recommendations=context.recommended_topics or [],
        )

        logger.info(
            "MentorIntelligenceEngine: difficulty=%s weak=%s strong=%s recs=%d",
            difficulty,
            topic_is_weak,
            topic_is_strong,
            len(recommended),
        )

        return PersonalizationMeta(
            difficulty_level=difficulty,
            use_analogies=use_analogies,
            skip_basics=skip_basics,
            build_prerequisites=build_prerequisites,
            style_instruction=style_instruction,
            recommended_topics=recommended,
            topic_is_weak=topic_is_weak,
            topic_is_strong=topic_is_strong,
            mode="teaching",
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers — all deterministic, no LLM calls
    # ──────────────────────────────────────────────────────────────────────────

    def _topic_in_list(self, question_lower: str, topics: List[str]) -> bool:
        """Return True if any topic from the list appears in the question."""
        for topic in topics:
            # normalise: lower, strip, handle multi-word topics
            normalised = topic.lower().strip()
            if normalised and normalised in question_lower:
                return True
        return False

    def _infer_difficulty(
        self,
        completed_sessions: int,
        topic_is_weak: bool,
        topic_is_strong: bool,
    ) -> str:
        """
        Infer difficulty level from session count and topic standing.
        Topic standing takes priority over raw session count.
        """
        if topic_is_weak:
            # Weak topics should always be explained more carefully
            if completed_sessions < self.ADVANCED_SESSION_THRESHOLD:
                return "Beginner"
            return "Intermediate"

        if topic_is_strong:
            if completed_sessions >= self.ADVANCED_SESSION_THRESHOLD:
                return "Advanced"
            return "Intermediate"

        # Neutral: infer purely from session count
        if completed_sessions < self.BEGINNER_SESSION_THRESHOLD:
            return "Beginner"
        if completed_sessions < self.ADVANCED_SESSION_THRESHOLD:
            return "Intermediate"
        return "Advanced"

    def _parse_learning_style(self, learning_style: str) -> str:
        """
        Convert the stored learning style free-text into a concise
        instruction for the prompt builder.
        """
        if not learning_style:
            return ""

        style_lower = learning_style.lower()

        # Implementation-first / hands-on signals
        if any(kw in style_lower for kw in ("implement", "coding", "code", "exercise")):
            return (
                "This learner prefers implementation-first learning. "
                "Show code examples before or alongside theory."
            )

        # Explanation-first / theory signals
        if any(kw in style_lower for kw in ("explain", "concept", "theory", "understand")):
            return (
                "This learner prefers concept-first learning. "
                "Explain theory thoroughly before providing code."
            )

        # Analogy / visual signals
        if any(kw in style_lower for kw in ("analogy", "visual", "diagram", "flowchart")):
            return (
                "This learner benefits from visual analogies. "
                "Use diagrams, step-by-step breakdowns, and real-world comparisons."
            )

        # Practice / challenge signals
        if any(kw in style_lower for kw in ("practice", "challenge", "problem", "exercise")):
            return (
                "This learner is practice-oriented. "
                "Include challenge problems or exercises at the end of explanations."
            )

        # Iterative / feedback signals
        if any(kw in style_lower for kw in ("iterative", "feedback", "step", "gradual")):
            return (
                "This learner responds well to iterative feedback. "
                "Break explanations into small, incremental steps."
            )

        # Return first sentence of the stored learning style as the instruction
        sentences = re.split(r'[.!?]', learning_style.strip())
        if sentences:
            return sentences[0].strip() + "."
        return learning_style.strip()

    def _select_recommendations(
        self,
        question_lower: str,
        profile_recommendations: List[str],
    ) -> List[str]:
        """
        Select up to 4 recommendations from the profile, prioritising
        topics that have relevance to the current question.
        """
        if not profile_recommendations:
            return []

        # Prefer recommendations that appear nearby the question context
        prioritised: List[str] = []
        fallback: List[str] = []

        for topic in profile_recommendations:
            # A recommendation is "relevant" if it shares words with the question
            topic_words = set(re.findall(r'\w+', topic.lower()))
            question_words = set(re.findall(r'\w+', question_lower))
            if topic_words & question_words:
                prioritised.append(topic)
            else:
                fallback.append(topic)

        combined = prioritised + fallback
        return combined[:4]

    def _generic_meta(self) -> PersonalizationMeta:
        """Fallback when no AI Context is available."""
        return PersonalizationMeta(
            difficulty_level="Intermediate",
            use_analogies=True,
            skip_basics=False,
            build_prerequisites=False,
            style_instruction=(
                "No learner profile available. Provide a clear, "
                "well-structured explanation suitable for an intermediate learner."
            ),
            recommended_topics=[],
            topic_is_weak=False,
            topic_is_strong=False,
            mode="teaching",
        )
