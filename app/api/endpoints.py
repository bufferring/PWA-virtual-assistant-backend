import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.core.schemas import ChatCompletionRequest
from app.core.config import get_settings
from app.services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Endpoint principal para chat completions
    Soporta streaming y respuestas completas
    """
    llm_service = LLMService()

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
            return response

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

    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.LLAMA_SERVER_URL}/v1/models")
            return response.json()
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list models")


@router.get("/health")
async def health_check():
    """
    Health check para Caddy
    """

    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.LLAMA_SERVER_URL}/health")
            if response.status_code == 200:
                return {"status": "healthy", "llm_server": "connected"}
    except (httpx.HTTPError, OSError):
        pass

    return {"status": "unhealthy", "llm_server": "disconnected"}
