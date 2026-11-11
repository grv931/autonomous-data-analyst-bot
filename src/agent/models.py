import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import settings

class LLMClient:
    """
    Unified LLM Client supporting OpenAI, TDS AI Pipe, Gemini, and Ollama.
    Handles legacy and modern reasoning models (gpt-5-mini, o1, o3) with parameter normalization.
    """
    def __init__(self):
        self.client = self._init_client()

    def _init_client(self) -> Optional[OpenAI]:
        # Priority 1: TDS AI Pipe token
        aipipe_tok = settings.aipipe_token or os.getenv("AIPIPE_TOKEN", "")
        if aipipe_tok and aipipe_tok != "your_aipipe_jwt_token_here":
            return OpenAI(
                base_url="https://aipipe.org/openai/v1",
                api_key=aipipe_tok,
            )
        # Priority 2: Direct OpenAI / Custom base URL
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        if api_key and api_key != "your_openai_api_key_here":
            return OpenAI(
                base_url=settings.openai_base_url,
                api_key=api_key,
            )
        # Fallback: check if local Ollama or similar without key
        base_url = settings.openai_base_url
        if "localhost" in base_url or "127.0.0.1" in base_url:
            return OpenAI(base_url=base_url, api_key="ollama")

        return None

    def get_model_name(self) -> str:
        aipipe_tok = settings.aipipe_token or os.getenv("AIPIPE_TOKEN", "")
        if aipipe_tok and aipipe_tok != "your_aipipe_jwt_token_here":
            return os.getenv("AIPIPE_MODEL", settings.aipipe_model or "gpt-5-mini")
        return settings.openai_model

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: int = 1500,
    ) -> str:
        if self.client is None:
            self.client = self._init_client()

        if self.client is None:
            raise RuntimeError(
                "No valid AI API Key found! Please set either AIPIPE_TOKEN or OPENAI_API_KEY in your .env file."
            )

        model = self.get_model_name()
        is_reasoning_or_gpt5 = any(m in model.lower() for m in ["gpt-5", "o1", "o3"])

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if is_reasoning_or_gpt5:
            kwargs["max_completion_tokens"] = max_tokens
            # gpt-5-mini only allows default temperature (1.0 or omitted)
        else:
            kwargs["max_tokens"] = max_tokens
            if temperature is not None:
                kwargs["temperature"] = temperature

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Self-healing parameter fallback for API mismatches
            err_str = str(e)
            if "max_tokens" in err_str or "temperature" in err_str:
                kwargs.pop("max_tokens", None)
                kwargs.pop("temperature", None)
                kwargs["max_completion_tokens"] = max_tokens
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content.strip()
            raise e

llm_client = LLMClient()
