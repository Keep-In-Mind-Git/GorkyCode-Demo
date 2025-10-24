"""Geocoding helpers."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional, Tuple

from geopy.geocoders import Nominatim


DEFAULT_COORDS = (56.326887, 44.005986)  # Central Nizhny Novgorod
CITY_HINTS = ("нижний", "nizhny", "nn", "г. нижний")
COORDINATE_RE = re.compile(
    r"^\s*[+-]?\d{1,3}(\.\d+)?\s*[,;\s]\s*[+-]?\d{1,3}(\.\d+)?\s*$"
)


class GeocodingError(Exception):
    """Raised when geocoding fails."""


def _normalize_query(query: str) -> str:
    raw = (query or "").strip()
    if not raw:
        return "Нижний Новгород"

    if COORDINATE_RE.match(raw):
        parts = re.split(r"[,;\s]+", raw.strip())
        if len(parts) >= 2:
            return f"{parts[0]},{parts[1]}"
        return raw

    lowered = raw.lower()
    if any(hint in lowered for hint in CITY_HINTS):
        return raw

    return f"{raw}, Нижний Новгород"


@lru_cache(maxsize=128)
def geocode_location(query: str) -> Tuple[float, float]:
    geocoder = Nominatim(user_agent="ai-tourist-assistant")
    normalized = _normalize_query(query)
    result = geocoder.geocode(normalized, language="ru", exactly_one=True, timeout=10)
    if result is None:
        raise GeocodingError(f"Не удалось определить координаты для '{query}'")
    return result.latitude, result.longitude


def resolve_location(query: str) -> tuple[Tuple[float, float], Optional[str]]:
    try:
        coords = geocode_location(query)
        normalized = _normalize_query(query)
        if normalized != (query or "").strip():
            hint = "Интерпретируем местоположение как '" f"{normalized}'."
        else:
            hint = None
        return coords, hint
    except GeocodingError as exc:
        warning = f"{exc}. Используем центр Нижнего Новгорода как отправную точку."
        return DEFAULT_COORDS, warning
    except Exception:
        warning = (
            "Геокодер временно недоступен. Используем центр города как отправную точку."
        )
        return DEFAULT_COORDS, warning
