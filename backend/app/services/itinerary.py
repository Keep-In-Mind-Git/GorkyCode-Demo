"""Основная логика построения маршрута."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Sequence, Tuple

from ..models import ItineraryResponse, ItineraryStop, Place
from .dataset import load_places
from .embeddings import EmbeddingProvider, EmbeddingVector
from .geocoding import resolve_location
from .interest_parser import InterestParser
from .narrative import NarrativeGenerator


WALKING_SPEED_KMH = 4.2
MAX_STOPS = 5
MIN_STOPS = 3
SEMANTIC_WEIGHT = 2.6
SEMANTIC_REASON_THRESHOLD = 0.32


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return 6371.0 * c


def walking_minutes(distance_km: float) -> float:
    return (distance_km / WALKING_SPEED_KMH) * 60.0


@dataclass
class Candidate:
    place: Place
    match_score: float
    matched_tags: Sequence[str]
    distance_km: float
    semantic_score: float


class ItineraryPlanner:
    def __init__(self) -> None:
        self.places = load_places()
        self.interest_parser = InterestParser()
        self.narrative = NarrativeGenerator()
        self.embedding = EmbeddingProvider()

    def plan(
        self, interests: Iterable[str], available_hours: float, location: str
    ) -> Tuple[ItineraryResponse, List[str]]:
        user_coords, warnings = self._resolve_user_context(location)
        normalized_interests = self.interest_parser.parse(interests)
        interest_vector = self.embedding.embed_interests(normalized_interests)
        candidates = self._choose_candidates(
            normalized_interests, user_coords, warnings, interest_vector
        )
        route = self._build_route(candidates, user_coords, available_hours)
        ordered_stops, total_minutes = self._schedule(route, user_coords)

        itinerary_stops = [
            candidate.place.to_stop(reason=reason, arrival_time=arrival)
            for candidate, arrival, reason in ordered_stops
        ]

        interest_list = sorted(normalized_interests)
        time_warning = self._time_warning(total_minutes, available_hours)
        if time_warning:
            warnings.append(time_warning)

        summary = self._compose_summary(
            itinerary_stops=itinerary_stops,
            interest_list=interest_list,
            available_hours=available_hours,
            location=location,
            stop_count=len(ordered_stops),
        )

        response = ItineraryResponse(
            summary=summary,
            total_duration_minutes=round(total_minutes),
            stops=itinerary_stops,
            notes=warnings or None,
        )
        return response, warnings

    def _resolve_user_context(
        self, location: str
    ) -> Tuple[Tuple[float, float], List[str]]:
        coords, warning = resolve_location(location)
        warnings = [warning] if warning else []
        return coords, warnings

    def _choose_candidates(
        self,
        normalized_interests: Iterable[str],
        user_coords: Tuple[float, float],
        warnings: List[str],
        interest_vector: Optional[EmbeddingVector],
    ) -> List[Candidate]:
        candidates = self._score_candidates(
            normalized_interests, user_coords, interest_vector
        )
        if candidates:
            return candidates

        warnings.append(
            "Не найдено объектов по интересам, показываем популярные места центра города."
        )
        return self._fallback_candidates(user_coords)

    @staticmethod
    def _time_warning(total_minutes: float, available_hours: float) -> str | None:
        if total_minutes <= available_hours * 60:
            return None
        return "Подобрать все интересные места в заданный лимит сложно, маршрут может занять чуть больше времени."

    def _compose_summary(
        self,
        itinerary_stops: List[ItineraryStop],
        interest_list: Sequence[str],
        available_hours: float,
        location: str,
        stop_count: int,
    ) -> str:
        default_summary = self._default_summary(
            stop_count, available_hours, interest_list
        )
        narrative_summary = self.narrative.generate_summary(
            stops=itinerary_stops,
            interests=interest_list,
            available_hours=available_hours,
            location=location,
        )
        if not narrative_summary:
            return default_summary
        return f"{narrative_summary} {default_summary}".strip()

    @staticmethod
    def _default_summary(
        stop_count: int, available_hours: float, interest_list: Sequence[str]
    ) -> str:
        summary_parts = [
            f"Маршрут включает {stop_count} остановки",
            f"доступное время: {available_hours:.1f} ч.",
        ]
        if interest_list:
            summary_parts.append("учитываем интересы: " + ", ".join(interest_list))
        return ". ".join(summary_parts)

    # TODO: improve point
    def _score_candidates(
        self,
        normalized_interests: Iterable[str],
        user_coords: Tuple[float, float],
        interest_vector: Optional[EmbeddingVector],
    ) -> List[Candidate]:
        interest_set = set(normalized_interests)
        scored: List[Candidate] = []
        for place in self.places:
            matched = sorted(interest_set.intersection(place.tags))

            base_score = 1.0 if matched else 0.4

            interest_boost = len(matched) * 1.5

            distance = haversine_km(
                user_coords[0], user_coords[1], place.latitude, place.longitude
            )
            distance_penalty = distance * 0.1

            diversity_boost = 0.2 if place.category_id else 0.0

            semantic_similarity = self.embedding.semantic_similarity(
                interest_vector, place
            )
            semantic_boost = semantic_similarity * SEMANTIC_WEIGHT

            score = (
                base_score
                + interest_boost
                - distance_penalty
                + diversity_boost
                + semantic_boost
            )

            scored.append(
                Candidate(
                    place=place,
                    match_score=score,
                    matched_tags=matched,
                    distance_km=distance,
                    semantic_score=semantic_similarity,
                )
            )

        scored.sort(key=lambda c: (c.match_score, -c.distance_km), reverse=True)
        return scored

    def _fallback_candidates(self, user_coords: Tuple[float, float]) -> List[Candidate]:
        popular = sorted(
            self.places,
            key=lambda place: (
                min(place.estimated_visit_minutes, 120),
                -haversine_km(
                    user_coords[0], user_coords[1], place.latitude, place.longitude
                ),
            ),
            reverse=True,
        )
        return [
            Candidate(
                place=place,
                match_score=1.0,
                matched_tags=place.tags,
                distance_km=haversine_km(
                    user_coords[0], user_coords[1], place.latitude, place.longitude
                ),
                semantic_score=0.0,
            )
            for place in popular[:20]
        ]

    # TODO: improve point
    def _build_route(
        self,
        candidates: List[Candidate],
        user_coords: Tuple[float, float],
        available_hours: float,
    ) -> List[Candidate]:
        available_minutes = available_hours * 60
        route: List[Candidate] = []
        current_coords = user_coords
        time_budget = available_minutes

        for candidate in candidates:
            if len(route) >= MAX_STOPS:
                break
            travel = walking_minutes(
                haversine_km(
                    current_coords[0],
                    current_coords[1],
                    candidate.place.latitude,
                    candidate.place.longitude,
                )
            )
            cost = travel + candidate.place.estimated_visit_minutes
            if cost <= time_budget or not route:
                route.append(candidate)
                current_coords = (candidate.place.latitude, candidate.place.longitude)
                time_budget = max(0.0, time_budget - cost)

        return route

    def _schedule(
        self,
        route: Sequence[Candidate],
        user_coords: Tuple[float, float],
        start_time: datetime | None = None,
    ) -> Tuple[List[Tuple[Candidate, str, str]], float]:
        if start_time is None:
            start_time = datetime.now().replace(second=0, microsecond=0)

        scheduled: List[Tuple[Candidate, str, str]] = []
        current_time = start_time
        current_coords = user_coords
        total_minutes = 0.0

        for candidate in route:
            distance = haversine_km(
                current_coords[0],
                current_coords[1],
                candidate.place.latitude,
                candidate.place.longitude,
            )
            travel = walking_minutes(distance)
            arrival_time = current_time + timedelta(minutes=travel)
            stay = candidate.place.estimated_visit_minutes
            reason = self._build_reason(candidate, distance)
            scheduled.append((candidate, arrival_time.strftime("%H:%M"), reason))
            current_time = arrival_time + timedelta(minutes=stay)
            current_coords = (candidate.place.latitude, candidate.place.longitude)
            total_minutes += travel + stay

        return scheduled, total_minutes

    def _build_reason(self, candidate: Candidate, leg_distance_km: float) -> str:
        walk_minutes = round(walking_minutes(leg_distance_km))
        if candidate.matched_tags:
            tags_text = ", ".join(candidate.matched_tags)
            return (
                f"Совпадает с интересами ({tags_text}), идти около {leg_distance_km:.1f} км "
                f"(примерно {walk_minutes} мин ходьбы)."
            )
        if candidate.semantic_score >= SEMANTIC_REASON_THRESHOLD:
            similarity = int(candidate.semantic_score * 100)
            return (
                f"По смыслу близко к запросу (схожесть ~{similarity}%), расстояние {leg_distance_km:.1f} км "
                f"(примерно {walk_minutes} мин ходьбы)."
            )
        if candidate.place.tags:
            return (
                f"Хорошо дополняет маршрут как локация с акцентом на {candidate.place.tags[0]} "
                f"в около {leg_distance_km:.1f} км (примерно {walk_minutes} мин ходьбы)."
            )
        return "Популярное место неподалёку, стоит посетить для разнообразия."
