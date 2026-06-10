import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, ORJSONResponse
from app.core.schemas import ChatCompletionRequest
from app.services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

llm_service = LLMService()


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Endpoint principal para chat completions
    Soporta streaming y respuestas completas
    """
    try:
        if request.stream:
            # Streaming response
            return StreamingResponse(
                llm_service.chat_completion_stream(request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            # Respuesta completa
            response = await llm_service.chat_completion(request)
            return ORJSONResponse(content=response)

    except httpx.TimeoutException:
        logger.error("Timeout connecting to LLM server")
        raise HTTPException(status_code=504, detail="LLM server timeout")
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models():
    """
    Lista los modelos disponibles
    """
    try:
        return await llm_service.list_models()
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list models")


@router.get("/health")
async def health_check():
    """
    Health check para Caddy
    """
    return await llm_service.health_check()
