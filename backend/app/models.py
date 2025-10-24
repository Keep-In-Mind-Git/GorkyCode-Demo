"""Pydantic models and domain objects for the AI tourist assistant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class ItineraryRequest(BaseModel):
    interests: List[str] = Field(..., description="List of user interests")
    available_hours: float = Field(..., gt=0, description="Available time in hours")
    location: str = Field(..., min_length=3, description="Current user location")

    @validator("interests")
    def ensure_interests(cls, value: List[str]) -> List[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("At least one interest is required")
        return cleaned


class ItineraryStop(BaseModel):
    name: str
    address: str
    reason: str
    arrival_time: str
    stay_duration_minutes: int
    latitude: float
    longitude: float


class ItineraryResponse(BaseModel):
    summary: str
    total_duration_minutes: int
    stops: List[ItineraryStop]
    notes: Optional[List[str]] = None


@dataclass(slots=True)
class Place:
    id: int
    title: str
    description: str
    address: str
    latitude: float
    longitude: float
    category_id: int | None
    tags: List[str]
    estimated_visit_minutes: int
    source_url: Optional[str]

    def to_stop(self, reason: str, arrival_time: str) -> ItineraryStop:
        return ItineraryStop(
            name=self.title,
            address=self.address,
            reason=reason,
            arrival_time=arrival_time,
            stay_duration_minutes=self.estimated_visit_minutes,
            latitude=self.latitude,
            longitude=self.longitude,
        )

    def __hash__(self) -> int:
        return hash(self.id)


class FeedbackStop(BaseModel):
    name: str
    arrival_time: Optional[str] = None


class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=600)
    interests: List[str] = Field(default_factory=list)
    location: str = Field(..., min_length=3)
    available_hours: float = Field(..., gt=0)
    stops: List[FeedbackStop] = Field(default_factory=list)
