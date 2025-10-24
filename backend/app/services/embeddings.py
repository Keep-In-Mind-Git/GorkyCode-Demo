from __future__ import annotations

import math
import os
from functools import lru_cache
from typing import Iterable, Optional, Sequence, Tuple

from mistralai import Mistral

from ..models import Place


EmbeddingVector = Tuple[float, ...]


class EmbeddingProvider:
    def __init__(self) -> None:
        api_key = os.getenv("MISTRAL_API_KEY")
        self._model = os.getenv("MISTRAL_EMBED_MODEL", "mistral-embed")
        self._client: Optional[Mistral] = Mistral(api_key=api_key) if api_key else None

    def embed_interests(self, interests: Iterable[str]) -> Optional[EmbeddingVector]:
        joined = ", ".join(sorted(set(filter(None, interests)))).strip()
        if not joined:
            return None
        return self._embed_text(joined)

    def semantic_similarity(
        self, interest_vector: Optional[EmbeddingVector], place: Place
    ) -> float:
        if not interest_vector:
            return 0.0
        place_vector = self.embed_place(place)
        if not place_vector:
            return 0.0
        return sum(a * b for a, b in zip(interest_vector, place_vector))

    @lru_cache(maxsize=128)
    def embed_place(self, place: Place) -> Optional[EmbeddingVector]:
        parts = [
            place.title,
            place.description or "",
            place.address,
            ", ".join(place.tags),
        ]
        text = " | ".join(part for part in parts if part).strip()
        if not text:
            return None
        return self._embed_text(text)

    @lru_cache(maxsize=2048)
    def _embed_text(self, text: str) -> Optional[EmbeddingVector]:
        if not self._client:
            return None
        try:
            response = self._client.embeddings.create(inputs=[text], model=self._model)
        except Exception:
            return None
        if not response or not response.data or not response.data[0].embedding:
            return None
        raw_vector = response.data[0].embedding
        return self._normalize(raw_vector)

    @staticmethod
    def _normalize(vector: Sequence[float]) -> Optional[EmbeddingVector]:
        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0:
            return None
        return tuple(component / norm for component in vector)
