import os
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import settings

class LLMClient:
    """
    Unified LLM Client supporting Google Gemini, TDS AI Pipe, OpenAI, and Ollama.
    Features automatic retry with backoff and multi-provider fallback on 429 rate limits or 503 errors.
    """
    def __init__(self):
        self.primary_client, self.primary_model = self._init_primary()
        self.fallback_client, self.fallback_model = self._init_fallback()

    def _init_primary(self) -> tuple[Optional[OpenAI], str]:
        # Priority 1: Google Gemini API Key
        raw_gemini = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        gemini_key = raw_gemini.strip().strip("'").strip('"') if raw_gemini else ""
        if gemini_key and gemini_key != "your_gemini_api_key_here":
            m = os.getenv("GEMINI_MODEL", settings.gemini_model or "gemini-3.5-flash")
            model = "gemini-3.5-flash" if ("1.5" in m or "2.5" in m) else m
            return (
                OpenAI(
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    api_key=gemini_key,
                ),
                model,
            )

        # Fallback to AI Pipe
        return self._init_fallback()

    def _init_fallback(self) -> tuple[Optional[OpenAI], str]:
        # Priority 2: TDS AI Pipe token
        raw_token = settings.aipipe_token or os.getenv("AIPIPE_TOKEN", "")
        aipipe_tok = raw_token.strip().strip("'").strip('"') if raw_token else ""
        if aipipe_tok and aipipe_tok != "your_aipipe_jwt_token_here":
            return (
                OpenAI(
                    base_url="https://aipipe.org/openai/v1",
                    api_key=aipipe_tok,
                ),
                os.getenv("AIPIPE_MODEL", settings.aipipe_model or "gpt-5-mini"),
            )

        # Priority 3: Direct OpenAI
        raw_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        api_key = raw_key.strip().strip("'").strip('"') if raw_key else ""
        if api_key and api_key != "your_openai_api_key_here":
            return (
                OpenAI(
                    base_url=settings.openai_base_url,
                    api_key=api_key,
                ),
                settings.openai_model,
            )

        return None, "gpt-4o-mini"

    def _build_kwargs(self, model: str, messages: List[Dict[str, str]], temperature: Optional[float], max_tokens: int) -> Dict[str, Any]:
        is_reasoning = any(m in model.lower() for m in ["gpt-5", "o1", "o3"])
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if is_reasoning:
            # Reasoning models spend tokens internally on thought chains; ensure plenty of headroom
            kwargs["max_completion_tokens"] = max(max_tokens, 3000)
        else:
            kwargs["max_tokens"] = max_tokens
            if temperature is not None:
                kwargs["temperature"] = temperature
        return kwargs

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: int = 2000,
    ) -> str:
        if not self.primary_client:
            self.primary_client, self.primary_model = self._init_primary()
            self.fallback_client, self.fallback_model = self._init_fallback()

        if not self.primary_client:
            raise RuntimeError("No valid AI API Key found! Set GEMINI_API_KEY or AIPIPE_TOKEN in .env.")

        # Try primary client with retry on rate limit
        primary_err = None
        for attempt in range(2):
            try:
                kwargs = self._build_kwargs(self.primary_model, messages, temperature, max_tokens)
                resp = self.primary_client.chat.completions.create(**kwargs)
                content = (resp.choices[0].message.content or "").strip()
                if content:
                    return content
            except Exception as e:
                primary_err = e
                err_str = str(e)
                # Self-healing parameter fallback
                if "max_tokens" in err_str or "temperature" in err_str:
                    kwargs.pop("max_tokens", None)
                    kwargs.pop("temperature", None)
                    kwargs["max_completion_tokens"] = max_tokens
                    try:
                        resp = self.primary_client.chat.completions.create(**kwargs)
                        content = (resp.choices[0].message.content or "").strip()
                        if content:
                            return content
                    except Exception as e2:
                        primary_err = e2

                if "429" in err_str or "503" in err_str:
                    time.sleep(1.5)
                    continue
                break

        # If primary failed (e.g. rate limit 429), seamlessly try fallback client
        if self.fallback_client and self.fallback_client != self.primary_client:
            try:
                fb_kwargs = self._build_kwargs(self.fallback_model, messages, temperature, max_tokens)
                resp = self.fallback_client.chat.completions.create(**fb_kwargs)
                fb_content = (resp.choices[0].message.content or "").strip()
                if fb_content:
                    return fb_content
            except Exception:
                pass

        if primary_err:
            raise primary_err
        return ""

llm_client = LLMClient()
