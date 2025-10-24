"""Utility script to convert the cultural objects spreadsheet into normalized JSON."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_PATH = ROOT / "cultural_objects_mnn.xlsx"
OUTPUT_PATH = Path(__file__).resolve().parent / "places.json"


CATEGORY_TAGS = {
    1: ["monument", "history", "landmark"],
    2: ["park", "nature", "relax"],
    3: ["exhibition", "history", "museum"],
    4: ["panorama", "riverfront", "walk"],
    5: ["architecture", "history", "streetscape"],
    6: ["culture_center", "events", "community"],
    7: ["museum", "art", "history"],
    8: ["theatre", "performing_arts", "evening"],
    9: ["culture_exchange", "international"],
    10: ["public_art", "mosaic", "art"],
}

CATEGORY_ESTIMATED_DURATION = {
    1: 30,
    2: 120,
    3: 45,
    4: 60,
    5: 75,
    6: 90,
    7: 120,
    8: 150,
    9: 60,
    10: 40,
}

KEYWORD_TAGS = {
    "коф": "coffee",
    "культура": "culture",
    "музей": "museum",
    "галере": "art",
    "театр": "theatre",
    "панора": "panorama",
    "истор": "history",
    "стрит": "street_art",
    "графф": "street_art",
    "дет": "family",
    "наука": "science",
    "планет": "science",
    "техн": "technology",
    "муз": "music",
    "филармон": "music",
}


def parse_point(value: str) -> tuple[float, float] | None:
    if not isinstance(value, str):
        return None
    match = re.match(r"POINT\s*\(([-\d\.]+)\s+([-\d\.]+)\)", value)
    if not match:
        return None
    lon, lat = map(float, match.groups())
    if math.isfinite(lat) and math.isfinite(lon):
        return lat, lon
    return None


def build_tags(*segments: Iterable[str]) -> list[str]:
    tags: set[str] = set()
    for segment in segments:
        for item in segment:
            if item:
                tags.add(item)
    return sorted(tags)


def keyword_enrichment(text: str) -> set[str]:
    text_lower = text.lower()
    enriched: set[str] = set()
    for needle, tag in KEYWORD_TAGS.items():
        if needle in text_lower:
            enriched.add(tag)
    return enriched


def main() -> None:
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {RAW_DATA_PATH}")

    df = pd.read_excel(RAW_DATA_PATH, sheet_name=0)

    records = []
    for row in df.itertuples():
        coords = parse_point(getattr(row, "coordinate", ""))
        if not coords:
            continue
        lat, lon = coords
        category = getattr(row, "category_id", None)
        title = str(getattr(row, "title", "")).strip()
        description = str(getattr(row, "description", "")).strip()
        address = str(getattr(row, "address", "")).strip()

        base_tags = CATEGORY_TAGS.get(category, [])
        keyword_tags = keyword_enrichment(f"{title}. {description}")
        tags = build_tags(base_tags, keyword_tags)

        visit_duration = CATEGORY_ESTIMATED_DURATION.get(category, 60)

        records.append(
            {
                "id": int(getattr(row, "id")),
                "title": title,
                "description": description,
                "address": address,
                "latitude": lat,
                "longitude": lon,
                "category_id": int(category) if category is not None else None,
                "tags": tags,
                "estimated_visit_minutes": visit_duration,
                "source_url": (
                    getattr(row, "url", None)
                    if not pd.isna(getattr(row, "url", None))
                    else None
                ),
            }
        )

    OUTPUT_PATH.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
