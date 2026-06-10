import httpx
from typing import AsyncGenerator
from app.core.config import get_settings
from app.core.schemas import ChatCompletionRequest


class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self.llama_url = f"{self.settings.LLAMA_SERVER_URL}/v1/chat/completions"
        self.timeout = self.settings.LLAMA_TIMEOUT

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncGenerator[bytes, None]:
        """
        Hace streaming de la respuesta del LLM
        """
        payload = {
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content} for m in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", self.llama_url, json=payload) as response:
                if response.status_code != 200:
                    error_msg = await response.aread()
                    raise Exception(f"LLM server error: {error_msg.decode()}")

                async for chunk in response.aiter_bytes():
                    yield chunk

    async def chat_completion(self, request: ChatCompletionRequest) -> dict:
        """
        Respuesta completa (sin streaming)
        """
        payload = {
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content} for m in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.llama_url, json=payload)
            response.raise_for_status()
            return response.json()
