"""Загрузка подготовленного набора локаций."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List

from ..models import Place


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "places.json"


@lru_cache(maxsize=1)
def load_places() -> List[Place]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Не найден подготовленный датасет по пути {DATA_PATH}")
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return [
        Place(
            id=item["id"],
            title=item["title"],
            description=item.get("description", ""),
            address=item.get("address", ""),
            latitude=item["latitude"],
            longitude=item["longitude"],
            category_id=item.get("category_id"),
            tags=item.get("tags", []),
            estimated_visit_minutes=item.get("estimated_visit_minutes", 60),
            source_url=item.get("source_url"),
        )
        for item in raw
    ]
