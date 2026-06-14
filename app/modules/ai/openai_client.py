from __future__ import annotations

import os

from openai import AsyncOpenAI

from app.core.config import settings


def create_openai_client() -> AsyncOpenAI:
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for AI features")
    return AsyncOpenAI(api_key=api_key, timeout=settings.openai_request_timeout_seconds)
