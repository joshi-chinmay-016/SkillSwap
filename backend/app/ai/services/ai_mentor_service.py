"""
AIMentorService — orchestrates the context-aware AI Mentor pipeline.

Pipeline:
    1. Fetch AIContext for the authenticated user (app.services.ai_context_service)
    2. Analyze profile → PersonalizationMeta  (MentorIntelligenceEngine)
    3. Build prompts                           (MentorPromptBuilder)
    4. Generate LLM response                  (LLMService — reused, no new client)
    5. Validate + parse JSON response
    6. Retry once on validation failure
    7. Graceful plain-text fallback if JSON parsing fails twice
    8. Return MentorChatResponse
"""
import json
import logging
import time
from typing import Optional

from sqlalchemy.orm import Session

from app.ai.services.llm_service import LLMService
from app.ai.services.mentor_intelligence_engine import MentorIntelligenceEngine
from app.ai.prompts.mentor_prompt_builder import MentorPromptBuilder
from app.ai.prompts.system_prompts import MENTOR_SYSTEM_PROMPT
from app.ai.schemas.mentor import MentorChatResponse, PersonalizationMeta
from app.ai.utils import parse_json_response
from app.services.ai_context_service import get_user_ai_context
from app.ai.services.intent_classification_service import IntentClassificationService
from app.ai.tools.tool_dispatcher import ToolDispatcher
from app.ai.models.mentor_intent import MentorIntent, IntentResult
from app.ai.tools.mentor_tool import ToolResult
from app.ai.services.memory_retrieval_service import MemoryRetrievalService
from app.ai.services.memory_update_service import MemoryUpdateService

logger = logging.getLogger(__name__)

_MIN_RESPONSE_LENGTH = 50


class AIMentorService:
    """
    Context-aware AI Mentor service.

    Does NOT manage conversation history (that belongs to Day 63).
    Every call is stateless at this layer.

    Day 65 additions:
        - MemoryRetrievalService: fetches relevant long-term memories before prompt building
        - MemoryUpdateService: refreshes last_used_at after response generation
    """

    def __init__(
        self,
        llm_service: LLMService,
        intent_service: Optional[IntentClassificationService] = None,
        dispatcher: Optional[ToolDispatcher] = None,
        memory_retrieval: Optional[MemoryRetrievalService] = None,
        memory_update: Optional[MemoryUpdateService] = None,
    ):
        self.llm = llm_service
        self.intelligence = MentorIntelligenceEngine()
        self.prompt_builder = MentorPromptBuilder()
        self.intent_service = intent_service or IntentClassificationService()
        self.dispatcher = dispatcher
        self.memory_retrieval = memory_retrieval or MemoryRetrievalService()
        self.memory_update = memory_update or MemoryUpdateService()

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def chat(
        self,
        db: Session,
        user_id: int,
        question: str,
    ) -> MentorChatResponse:
        """
        Main entry point.

        Parameters
        ----------
        db       : SQLAlchemy session
        user_id  : authenticated user's ID — only their own context is accessed
        question : the learner's message

        Returns
        -------
        MentorChatResponse with response text, recommended_topics, difficulty_level
        """
        logger.info("AIMentorService.chat: user_id=%d", user_id)

        # ── 0. Classify Intent ───────────────────────────────────────────────
        intent_result = self._classify_intent(user_id, None, question)

        # ── 1. Fetch AI Context ───────────────────────────────────────────────
        context = get_user_ai_context(db, user_id)
        if context:
            logger.info(
                "AIMentorService: context loaded — sessions=%d version=%d",
                context.completed_sessions,
                context.context_version,
            )
        else:
            logger.info("AIMentorService: no AI context found — using generic mentor")

        # ── 2. Dispatch Tool (if applicable) ──────────────────────────────────
        tool_results = self._dispatch_tool(db, user_id, intent_result)

        # ── 3. Analyze profile ────────────────────────────────────────────────
        meta: PersonalizationMeta = self.intelligence.analyze(context, question)
        logger.info(
            "AIMentorService: difficulty=%s weak=%s strong=%s",
            meta.difficulty_level,
            meta.topic_is_weak,
            meta.topic_is_strong,
        )

        # ── 4. Build prompt ───────────────────────────────────────────────────
        user_prompt = self.prompt_builder.build(
            question=question,
            context=context,
            meta=meta,
            tool_results=tool_results,
        )

        # ── 5. First LLM call ─────────────────────────────────────────────────
        t0 = time.perf_counter()
        raw = self.llm.generate(
            prompt=user_prompt,
            system_prompt=MENTOR_SYSTEM_PROMPT,
            temperature=0.65,
        )
        elapsed = time.perf_counter() - t0
        logger.info("AIMentorService: LLM latency=%.2fs", elapsed)

        # ── 6. Validate + parse ───────────────────────────────────────────────
        parsed = self._try_parse(raw)
        if parsed is None:
            # ── 7. Retry once with slightly lower temperature ─────────────────
            logger.warning("AIMentorService: first response failed validation — retrying")
            raw = self.llm.generate(
                prompt=user_prompt,
                system_prompt=MENTOR_SYSTEM_PROMPT,
                temperature=0.45,
            )
            parsed = self._try_parse(raw)

        # ── 8. Graceful fallback if both attempts fail ────────────────────────
        tool_meta = self._extract_tool_meta(tool_results)
        if parsed is None:
            logger.error("AIMentorService: both LLM attempts failed validation — using plain text fallback")
            return MentorChatResponse(
                response=self._sanitize_text(raw),
                recommended_topics=meta.recommended_topics,
                difficulty_level=meta.difficulty_level,
                **tool_meta,
            )

        # ── 9. Return structured response ─────────────────────────────────────
        logger.info("AIMentorService: response generated successfully")
        return MentorChatResponse(
            response=parsed.get("response", ""),
            recommended_topics=parsed.get("recommended_topics", meta.recommended_topics),
            difficulty_level=parsed.get("difficulty_level", meta.difficulty_level),
            **tool_meta,
        )

    def chat_in_conversation(
        self,
        db: Session,
        user_id: int,
        question: str,
        history: list,
    ) -> MentorChatResponse:
        """
        Multi-turn entry point for persistent conversations.

        Parameters
        ----------
        db       : SQLAlchemy session
        user_id  : authenticated user's ID
        question : current user message
        history  : list of previous MentorMessage instances (ordered asc)

        Returns
        -------
        MentorChatResponse
        """
        logger.info(
            "AIMentorService.chat_in_conversation: user_id=%d history_len=%d",
            user_id,
            len(history),
        )

        # ── 0. Classify Intent ───────────────────────────────────────────────
        intent_result = self._classify_intent(user_id, None, question)

        # ── 1. Fetch AI Context ───────────────────────────────────────────────
        context = get_user_ai_context(db, user_id)

        # ── 2. Dispatch Tool (if applicable) ──────────────────────────────────
        tool_results = self._dispatch_tool(db, user_id, intent_result)

        # ── 3. Analyze profile ────────────────────────────────────────────────
        meta: PersonalizationMeta = self.intelligence.analyze(context, question)

        # ── 4. Build multi-turn prompt ────────────────────────────────────────
        user_prompt = self.prompt_builder.build_conversation_prompt(
            question=question,
            history=history,
            context=context,
            meta=meta,
            tool_results=tool_results,
        )

        # ── 5. Generate LLM response ──────────────────────────────────────────
        t0 = time.perf_counter()
        raw = self.llm.generate(
            prompt=user_prompt,
            system_prompt=MENTOR_SYSTEM_PROMPT,
            temperature=0.65,
        )
        elapsed = time.perf_counter() - t0
        logger.info("AIMentorService: LLM latency=%.2fs", elapsed)

        # ── 6. Validate + parse ───────────────────────────────────────────────
        parsed = self._try_parse(raw)
        if parsed is None:
            logger.warning("AIMentorService: first response failed validation — retrying")
            raw = self.llm.generate(
                prompt=user_prompt,
                system_prompt=MENTOR_SYSTEM_PROMPT,
                temperature=0.45,
            )
            parsed = self._try_parse(raw)

        tool_meta = self._extract_tool_meta(tool_results)

        if parsed is None:
            logger.error("AIMentorService: both LLM attempts failed validation — using plain text fallback")
            return MentorChatResponse(
                response=self._sanitize_text(raw),
                recommended_topics=meta.recommended_topics,
                difficulty_level=meta.difficulty_level,
                **tool_meta,
            )

        return MentorChatResponse(
            response=parsed.get("response", ""),
            recommended_topics=parsed.get("recommended_topics", meta.recommended_topics),
            difficulty_level=parsed.get("difficulty_level", meta.difficulty_level),
            **tool_meta,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _classify_intent(
        self,
        user_id: int,
        conversation_id: Optional[int],
        question: str,
    ) -> IntentResult:
        """Classify user intent safely with fallback to UNKNOWN."""
        if not self.intent_service:
            return IntentResult(
                intent=MentorIntent.UNKNOWN,
                confidence=0.0,
                reason="Intent classification service not configured.",
            )
        try:
            return self.intent_service.classify(user_id, conversation_id, question)
        except Exception as exc:
            logger.error("AIMentorService: intent classification failed: %s", str(exc))
            return IntentResult(
                intent=MentorIntent.UNKNOWN,
                confidence=0.0,
                reason=f"Error: {str(exc)}",
            )

    def _dispatch_tool(
        self,
        db: Session,
        user_id: int,
        intent_result: IntentResult,
    ) -> Optional[list[ToolResult]]:
        """Dispatch registered tool for classified intent."""
        if not self.dispatcher:
            return None
        try:
            result = self.dispatcher.dispatch(db=db, user_id=user_id, intent_result=intent_result)
            return [result] if result else None
        except Exception as exc:
            logger.error("AIMentorService: tool dispatch failed: %s", str(exc))
            return None

    def _retrieve_memories(
        self,
        db: Session,
        user_id: int,
        question: str,
    ) -> list:
        """Retrieve relevant active memories for the current question. Fails safe."""
        try:
            return self.memory_retrieval.retrieve(db=db, user_id=user_id, question=question)
        except Exception as exc:
            logger.error("AIMentorService: memory retrieval failed: %s", str(exc))
            return []


    @staticmethod
    def _extract_tool_meta(tool_results: Optional[list[ToolResult]]) -> dict:
        if not tool_results:
            return {}
        first = tool_results[0]
        if not first:
            return {}
        return {
            "tool_used": first.tool,
            "tool_success": first.success,
            "tool_execution_time": round(first.execution_time_ms) if first.execution_time_ms else 0,
            "tool_data": first.data if first.success else None,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _try_parse(self, raw: str) -> Optional[dict]:
        """
        Attempt to parse and validate an LLM response.
        Returns a dict on success, None on any failure.
        """
        if not raw or not raw.strip():
            return None
        try:
            data = parse_json_response(raw)
        except (json.JSONDecodeError, ValueError):
            return None

        if not isinstance(data, dict):
            return None

        response_text = data.get("response", "")
        if not isinstance(response_text, str):
            return None
        if len(response_text.strip()) < _MIN_RESPONSE_LENGTH:
            return None
        if not self._is_valid_utf8(response_text):
            return None

        # Hallucination / prompt-leak guard
        if self._leaks_system_prompt(response_text):
            logger.warning("AIMentorService: response appears to leak system prompt — discarding")
            return None

        return data

    @staticmethod
    def _is_valid_utf8(text: str) -> bool:
        try:
            text.encode("utf-8").decode("utf-8")
            return True
        except (UnicodeEncodeError, UnicodeDecodeError):
            return False

    @staticmethod
    def _leaks_system_prompt(text: str) -> bool:
        """Detect if the response accidentally echoes internal instructions."""
        forbidden_phrases = [
            "behavioral rules",
            "output format",
            "do not wrap in markdown code fences",
            "mentor mode:",
            "learner profile]",
            "personalization guidance",
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in forbidden_phrases)

    @staticmethod
    def _sanitize_text(raw: str) -> str:
        """Strip markdown code fences from plain-text fallback."""
        text = raw.strip()
        for fence in ("```json", "```"):
            if text.startswith(fence):
                text = text[len(fence):].strip()
            if text.endswith("```"):
                text = text[:-3].strip()
        return text or "I was unable to generate a response. Please try again."
