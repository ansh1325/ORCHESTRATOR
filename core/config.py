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
    
    # Meta Llama & High-Capacity Models
    META_MODEL_ORCHESTRATOR: str = os.getenv("META_MODEL_ORCHESTRATOR", "openai/gpt-oss-120b")
    META_MODEL_WORKER: str = os.getenv("META_MODEL_WORKER", "openai/gpt-oss-120b")
    
    # Workspaces
    WORKSPACE_DIR: Path = Path(os.getenv("WORKSPACE_DIR", str(BASE_DIR / "workspaces"))).resolve()
    
    # Execution & Simulation
    _raw_mock = os.getenv("MOCK_MODE", "").strip().lower()
    FORCE_MOCK: bool = _raw_mock in ("true", "1", "yes")
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    @classmethod
    def has_active_api_key(cls) -> bool:
        """Checks if any supported LLM provider API key is provided and non-placeholder."""
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
            if cls.GROQ_API_KEY and not cls.GROQ_API_KEY.startswith("your_"):
                return OpenAI(api_key=cls.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
            if cls.FIREWORKS_API_KEY and not cls.FIREWORKS_API_KEY.startswith("your_"):
                return OpenAI(api_key=cls.FIREWORKS_API_KEY, base_url="https://api.fireworks.ai/inference/v1")
            if cls.OPENAI_API_KEY and not cls.OPENAI_API_KEY.startswith("your_"):
                return OpenAI(api_key=cls.OPENAI_API_KEY, base_url=cls.OPENAI_BASE_URL or None)
        except Exception:
            return None
        return None

# Singleton instance
settings = Settings()
