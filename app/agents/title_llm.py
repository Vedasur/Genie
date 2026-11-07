"""Dedicated LLM client for conversation title generation.

Pinned to Luna (or TITLE_MODEL_NAME) and independent of the agent graph / request model.
"""

from langchain_openai import ChatOpenAI

from core.config import Settings

settings = Settings()
title_llm = ChatOpenAI(model=settings.title_model_name)
