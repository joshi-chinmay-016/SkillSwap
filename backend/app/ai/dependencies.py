from app.ai.services.llm_service import LLMService

_llm_service = LLMService()


def get_llm_service() -> LLMService:
    return _llm_service