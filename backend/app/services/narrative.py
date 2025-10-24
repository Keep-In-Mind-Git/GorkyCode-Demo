"""Narrative generation powered by LLMs with graceful fallback."""

from __future__ import annotations

import os
from typing import Iterable, Optional

from mistralai import Mistral

from ..models import ItineraryStop


class NarrativeGenerator:
    """Produces natural-language summaries for itineraries."""

    def __init__(self) -> None:
        api_key = os.getenv("MISTRAL_API_KEY")
        model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        self._client: Optional[Mistral] = None
        self._model = model
        if api_key:
            self._client = Mistral(api_key=api_key)

    def generate_summary(
        self,
        stops: Iterable[ItineraryStop],
        interests: Iterable[str],
        available_hours: float,
        location: str,
    ) -> Optional[str]:
        if not self._client:
            return None

        messages = self._build_prompt(stops, interests, available_hours, location)
        completion = self._safe_complete(messages)
        return self._extract_text(completion)

    def _build_prompt(
        self,
        stops: Iterable[ItineraryStop],
        interests: Iterable[str],
        available_hours: float,
        location: str,
    ) -> list[dict[str, str]]:
        stops_lines = [
            f"{idx}. {stop.name} — {stop.reason}"
            for idx, stop in enumerate(stops, start=1)
        ]
        interests_text = (
            ", ".join(interests) if interests else "универсальные впечатления"
        )
        input_text = (
            "Сформируй краткое, тёплое описание маршрута по Нижнему Новгороду. "
            "Обязательно упомяни, почему маршрут подходит пользователю, "
            "и подчеркни разнообразие точек. Ответ на 2-3 предложения."
        )
        user_payload = (
            f"Локация старта: {location}. Доступное время: {available_hours:.1f} ч. "
            f"Интересы пользователя: {interests_text}. "
            "Остановки с причинами:\n" + "\n".join(stops_lines)
        )
        return [
            {
                "role": "system",
                "content": "Ты дружелюбный локальный гид по Нижнему Новгороду. Пиши по-русски.",
            },
            {"role": "user", "content": input_text},
            {"role": "user", "content": user_payload},
        ]

    def _safe_complete(self, messages: list[dict[str, str]]):
        try:
            return self._client.chat.complete(  # type: ignore[union-attr]
                model=self._model,
                temperature=0.6,
                max_tokens=220,
                messages=messages,
            )
        except Exception:
            return None

    @staticmethod
    def _extract_text(completion) -> Optional[str]:
        if not completion or not completion.choices:
            return None
        first_choice = completion.choices[0]
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None)
        if not content:
            return None
        text_parts = [part.text for part in content if getattr(part, "text", None)]
        result = "".join(text_parts).strip()
        return result or None
