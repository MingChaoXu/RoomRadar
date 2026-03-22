from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass
class CompetitorCandidate:
    platform_hotel_id: str
    hotel_name: str
    address: str
    city: str | None
    distance_meters: int
    lng: float
    lat: float


@dataclass
class RateCandidate:
    platform: str
    platform_hotel_id: str
    room_name: str
    check_in_date: date
    check_out_date: date
    display_price: float
    final_price: float
    breakfast_included: bool
    free_cancel: bool


class AmapAdapter(Protocol):
    def discover_competitors(
        self,
        hotel_name: str,
        city: str | None,
        address: str | None,
        lng: float | None,
        lat: float | None,
        radius_meters: int,
        limit: int,
    ) -> list[CompetitorCandidate]: ...


class OtaAdapter(Protocol):
    platform: str

    def collect_rates(
        self,
        hotel_name: str,
        city: str | None,
        address: str | None,
        check_in_date: date,
        check_out_date: date,
        adults: int,
        children: int,
    ) -> list[RateCandidate]: ...
