"""
MentorPromptBuilder — constructs all prompts for the AI Mentor.

All prompt engineering is isolated here so services remain clean.
New mentor modes (Interview, Revision, Debugging) can be added without
touching AIMentorService or MentorIntelligenceEngine.
"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.ai_context import AIContext
    from app.ai.schemas.mentor import PersonalizationMeta


# ---------------------------------------------------------------------------
# Mentor mode registry
# Future modes: "interview", "revision", "debugging", "code_review"
# ---------------------------------------------------------------------------
MENTOR_MODES = {
    "teaching": "Teaching Mode — explain concepts clearly and build understanding step by step.",
    "interview": "Interview Mode — ask probing questions and evaluate answers critically.",
    "revision": "Revision Mode — summarise and reinforce previously covered concepts.",
    "debugging": "Debugging Mode — help the learner diagnose and fix code issues.",
}


class MentorPromptBuilder:
    """
    Builds structured prompts for the AI Mentor.

    Prompt order (required):
        1. Mode header
        2. Learner profile (injected from AIContext)
        3. Personalization metadata
        4. User question
    """

    def build(
        self,
        question: str,
        context: Optional["AIContext"],
        meta: "PersonalizationMeta",
    ) -> str:
        """
        Compose the full user-turn prompt that is sent to the LLM.
        The system prompt is passed separately via LLMService.generate().
        """
        sections: list[str] = []

        # ── 1. Mode header ──────────────────────────────────────────────────
        mode_description = MENTOR_MODES.get(
            meta.mode, MENTOR_MODES["teaching"]
        )
        sections.append(f"[Mentor Mode: {meta.mode.title()}]\n{mode_description}")

        # ── 2. Learner profile ───────────────────────────────────────────────
        sections.append(self._build_learner_profile(context))

        # ── 3. Personalization guidance ──────────────────────────────────────
        sections.append(self._build_personalization_block(meta))

        # ── 4. User question ─────────────────────────────────────────────────
        sections.append(f"[Learner Question]\n{question.strip()}")

        return "\n\n".join(sections)

    def build_conversation_prompt(
        self,
        question: str,
        history: list,
        context: Optional["AIContext"],
        meta: "PersonalizationMeta",
    ) -> str:
        """
        Compose a user-turn prompt that includes recent conversation history.

        Prompt order:
            1. Mode header
            2. Learner profile
            3. Personalization metadata
            4. Recent conversation history
            5. Current user question
        """
        sections: list[str] = []

        # ── 1. Mode header ──────────────────────────────────────────────────
        mode_description = MENTOR_MODES.get(
            meta.mode, MENTOR_MODES["teaching"]
        )
        sections.append(f"[Mentor Mode: {meta.mode.title()}]\n{mode_description}")

        # ── 2. Learner profile ───────────────────────────────────────────────
        sections.append(self._build_learner_profile(context))

        # ── 3. Personalization guidance ──────────────────────────────────────
        sections.append(self._build_personalization_block(meta))

        # ── 4. Conversation History ──────────────────────────────────────────
        if history:
            history_lines = ["[Recent Conversation History]"]
            for msg in history:
                role_label = "Learner" if msg.role.upper() == "USER" else "AI Mentor"
                history_lines.append(f"{role_label}: {msg.content}")
            sections.append("\n\n".join(history_lines))

        # ── 5. Current User question ──────────────────────────────────────────
        sections.append(f"[Current Learner Question]\n{question.strip()}")

        return "\n\n".join(sections)

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _build_learner_profile(self, context: Optional["AIContext"]) -> str:
        if not context:
            return (
                "[Learner Profile]\n"
                "No persistent profile available. Treat this as a general learner "
                "at an intermediate level and provide a well-structured explanation."
            )

        lines = ["[Learner Profile]"]

        if context.completed_sessions:
            lines.append(
                f"Completed Sessions: {context.completed_sessions}"
            )

        if context.overall_summary:
            lines.append(
                f"\nOverall Progress:\n{context.overall_summary.strip()}"
            )

        if context.strong_topics:
            lines.append(
                "Strong Topics (already mastered — do not over-explain):\n"
                + ", ".join(context.strong_topics)
            )

        if context.weak_topics:
            lines.append(
                "Areas for Improvement (build carefully, use analogies):\n"
                + ", ".join(context.weak_topics)
            )

        if context.learning_interests:
            lines.append(
                "Learning Interests:\n"
                + ", ".join(context.learning_interests)
            )

        if context.recommended_topics:
            lines.append(
                "Topics Recommended by AI Profile:\n"
                + ", ".join(context.recommended_topics)
            )

        if context.learning_style:
            lines.append(
                f"Learning Style:\n{context.learning_style.strip()}"
            )

        return "\n\n".join(lines)

    def _build_personalization_block(self, meta: "PersonalizationMeta") -> str:
        lines = [f"[Personalization Guidance — Difficulty: {meta.difficulty_level}]"]

        if meta.topic_is_weak:
            lines.append(
                "⚠ This topic is identified as a knowledge gap for the learner.\n"
                "Build from first principles. Use real-world analogies. "
                "Provide step-by-step examples. Do not assume prior mastery."
            )
        elif meta.topic_is_strong:
            lines.append(
                "✓ The learner has demonstrated strength in this topic area.\n"
                "Skip foundational explanations. Focus on optimizations, trade-offs, "
                "edge cases, and advanced variants."
            )

        if meta.build_prerequisites:
            lines.append(
                "Build prerequisite knowledge before tackling the main concept."
            )

        if meta.use_analogies:
            lines.append(
                "Use real-world analogies to illustrate abstract concepts."
            )

        if meta.skip_basics:
            lines.append(
                "The learner already understands the basics — move directly to depth."
            )

        if meta.style_instruction:
            lines.append(f"Learning Style Instruction:\n{meta.style_instruction}")

        if meta.recommended_topics:
            lines.append(
                "Profile-Recommended Follow-up Topics (weave into your recommendations):\n"
                + ", ".join(meta.recommended_topics[:6])
            )

        return "\n\n".join(lines)
