from typing import Any
"""
LlamaOrchestrator Configuration Module
Handles environment variables, model routing, and creator identity.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    BASE_DIR: Path = BASE_DIR
    # Creator & Identity
    CREATOR_NAME: str = "Ansh Tiwari"
    CREATOR_ROLE: str = "Creator & Chief Systems Architect"
    SYSTEM_NAME: str = "LlamaOrchestrator"
    SYSTEM_TAGLINE: str = "Autonomous Hierarchical Multi-Agent Engine & AI Partner"
    
    # API Keys & Endpoints
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    FIREWORKS_API_KEY: str | None = os.getenv("FIREWORKS_API_KEY")
    BASETEN_API_KEY: str | None = os.getenv("BASETEN_API_KEY")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")
    LOCAL_LLM_URL: str | None = os.getenv("LOCAL_LLM_URL") or os.getenv("OLLAMA_BASE_URL")
    
    # Meta Llama & High-Capacity Models
    META_MODEL_ORCHESTRATOR: str = os.getenv("META_MODEL_ORCHESTRATOR", "openai/gpt-oss-120b")
    META_MODEL_WORKER: str = os.getenv("META_MODEL_WORKER", "openai/gpt-oss-120b")
    
    # Workspaces
    WORKSPACE_DIR: Path = Path(os.getenv("WORKSPACE_DIR", str(BASE_DIR / "workspaces"))).resolve()
    
    # Execution & Simulation
    _raw_mock = os.getenv("MOCK_MODE", "").strip().lower()
    FORCE_MOCK: bool = _raw_mock in ("true", "1", "yes")
    
    # Server configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    @classmethod
    def has_active_api_key(cls) -> bool:
        """Checks if any supported LLM provider API key or local model endpoint is provided."""
        if cls.LOCAL_LLM_URL and len(cls.LOCAL_LLM_URL.strip()) > 5:
            return True
        keys = [cls.GROQ_API_KEY, cls.FIREWORKS_API_KEY, cls.BASETEN_API_KEY, cls.OPENAI_API_KEY]
        for key in keys:
            if key and not key.startswith("your_") and len(key.strip()) > 8:
                return True
        return False

    @classmethod
    def is_mock(cls) -> bool:
        """Determines if the system operates in high-fidelity mock/simulation mode."""
        if cls.FORCE_MOCK:
            return True
        return not cls.has_active_api_key()

    @classmethod
    def get_llm_client(cls):
        """Returns an OpenAI-compatible client initialized with the primary provider."""
        if cls.is_mock():
            return None
            
        try:
            from openai import OpenAI
            # 0. Local Model Endpoint (Ollama, vLLM, LM Studio) - Zero Token Limits, Unlimited Swarms
            if cls.LOCAL_LLM_URL:
                local_key = os.getenv("LOCAL_LLM_KEY", "local_jarvis")
                return OpenAI(api_key=local_key, base_url=cls.LOCAL_LLM_URL.rstrip("/"), max_retries=1, timeout=60.0)
            if cls.GROQ_API_KEY and not cls.GROQ_API_KEY.startswith("your_"):
                return OpenAI(api_key=cls.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1", max_retries=0, timeout=12.0)
            if cls.FIREWORKS_API_KEY and not cls.FIREWORKS_API_KEY.startswith("your_"):
                return OpenAI(api_key=cls.FIREWORKS_API_KEY, base_url="https://api.fireworks.ai/inference/v1", max_retries=0, timeout=12.0)
            if cls.OPENAI_API_KEY and not cls.OPENAI_API_KEY.startswith("your_"):
                return OpenAI(api_key=cls.OPENAI_API_KEY, base_url=cls.OPENAI_BASE_URL or None, max_retries=0, timeout=12.0)
        except Exception:
            return None
        return None

    @classmethod
    def get_fallback_models(cls) -> list[str]:
        """Returns priority order of operational models with dynamic quota failover."""
        candidates = [cls.META_MODEL_ORCHESTRATOR, "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
        seen: set[str] = set()
        res: list[str] = []
        for c in candidates:
            if c and c not in seen:
                seen.add(c)
                res.append(c)
        return res

    @classmethod
    def create_chat_completion(
        cls,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 3000,
        response_format: dict[str, str] | None = None
    ) -> Any:
        """
        Executes chat completion with automatic quota/429 fallback across available models.
        """
        client = cls.get_llm_client()
        if not client:
            return None

        last_err: Exception | None = None
        for model in cls.get_fallback_models():
            try:
                actual_tokens = max(max_tokens, 2500) if any(k in str(model).lower() for k in ["120b", "reason", "r1", "oss"]) else max_tokens
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": actual_tokens
                }
                if response_format:
                    kwargs["response_format"] = response_format
                return client.chat.completions.create(**kwargs)
            except Exception as e:
                err_str = str(e).lower()
                last_err = e

                # If JSON object mode validation failed on reasoning model (e.g. Groq 400 'Failed to validate JSON'),
                # seamlessly retry without response_format parameter so the model can output JSON naturally
                if response_format and ("failed to validate json" in err_str or "response_format" in err_str or ("400" in err_str and "json" in err_str)):
                    try:
                        kwargs_no_rf = dict(kwargs)
                        kwargs_no_rf.pop("response_format", None)
                        return client.chat.completions.create(**kwargs_no_rf)
                    except Exception as e2:
                        err_str = str(e2).lower()
                        last_err = e2

                if any(x in err_str for x in ["429", "rate_limit", "quota", "tokens per day", "decommissioned", "does not exist", "404", "not_found", "model_not_found"]):
                    continue
                raise e
        if last_err:
            raise last_err
        return None

# Singleton instance
settings = Settings()
