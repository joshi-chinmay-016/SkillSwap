from fastapi import APIRouter, HTTPException

from app.ai.schemas.chat import (
    ChatRequest,
    ChatResponse
)

from app.ai.services.llm_service import LLMService

from app.ai.prompts.system_prompts import (
    GENERAL_CHAT_SYSTEM_PROMPT
)
from fastapi import Depends

from app.ai.dependencies import get_llm_service

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service)

):

    try:

        response = llm_service.generate(

            prompt=request.message,

            system_prompt=GENERAL_CHAT_SYSTEM_PROMPT

        )

        return ChatResponse(
            response=response
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Failed to generate AI response."
        )