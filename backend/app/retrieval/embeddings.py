from __future__ import annotations

from typing import List, Optional

from ..config import settings
from ..exceptions import ConfigurationError, DependencyUnavailableError


class OpenAIEmbeddingClient:
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.openai_embedding_model
        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for semantic embeddings.")
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:
            raise DependencyUnavailableError("Install the OpenAI Python SDK to create embeddings.") from exc
        self.client = OpenAI(api_key=settings.openai_api_key)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]
