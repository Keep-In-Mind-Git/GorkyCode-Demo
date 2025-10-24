"""Feedback persistence utilities."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..models import FeedbackRequest


FEEDBACK_PATH = Path(__file__).resolve().parent.parent / "data" / "feedback.jsonl"


def record_feedback(feedback: FeedbackRequest) -> None:
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = feedback.model_dump()
    payload["timestamp"] = datetime.utcnow().isoformat(timespec="seconds")
    with FEEDBACK_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
