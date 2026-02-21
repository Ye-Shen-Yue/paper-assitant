from openai import OpenAI
from typing import Optional
import json

from app.config import settings


class LLMClient:
    """LLM API client using OpenAI-compatible interface (Kimi)."""

    def __init__(self):
        # Use llm_api_key first, fallback to qwen_api_key for backward compatibility
        api_key = settings.llm_api_key or settings.qwen_api_key
        base_url = settings.llm_base_url if settings.llm_api_key else settings.qwen_base_url
        model = settings.llm_model if settings.llm_api_key else settings.qwen_model

        if not api_key or api_key == "your_api_key_here":
            raise ValueError(
                "LLM API key not configured. "
                "Please set LLM_API_KEY in backend/.env file. "
                "Get your key from https://platform.moonshot.cn/"
            )
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=120.0,
        )
        self.model = model

    def chat(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful scientific paper analysis assistant.",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> str:
        """Send a chat completion request to Qwen."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg or "invalid" in error_msg.lower():
                raise ValueError(f"LLM API authentication failed. Check your LLM_API_KEY in .env. Error: {error_msg}")
            raise

    def chat_json(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful scientific paper analysis assistant. Always respond with valid JSON.",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict:
        """Send a chat request and parse JSON response."""
        raw = self.chat(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Try to extract JSON from the response
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
            raise


# Singleton instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
