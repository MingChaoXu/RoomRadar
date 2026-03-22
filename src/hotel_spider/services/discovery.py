from sqlalchemy import select
from sqlalchemy.orm import Session

from hotel_spider.adapters.base import AmapAdapter
from hotel_spider.db.models import CompetitorGroup, Hotel, HotelPlatformMapping
from hotel_spider.schemas.hotel import CompetitorRead


class DiscoveryService:
    def __init__(self, db: Session, adapter: AmapAdapter):
        self.db = db
        self.adapter = adapter

    def discover(self, target_hotel: Hotel, radius_meters: int, limit: int) -> list[CompetitorRead]:
        candidates = self.adapter.discover_competitors(
            hotel_name=target_hotel.name,
            city=target_hotel.city,
            address=target_hotel.address,
            lng=float(target_hotel.lng) if target_hotel.lng is not None else None,
            lat=float(target_hotel.lat) if target_hotel.lat is not None else None,
            radius_meters=radius_meters,
            limit=limit,
        )

        discovered: list[CompetitorRead] = []
        for candidate in candidates:
            if candidate.hotel_name == target_hotel.name:
                continue

            hotel = self._get_or_create_competitor(candidate)
            self._upsert_group(target_hotel_id=target_hotel.id, competitor_hotel_id=hotel.id, distance=candidate.distance_meters)
            self._upsert_mapping(hotel_id=hotel.id, platform_hotel_id=candidate.platform_hotel_id, hotel_name=candidate.hotel_name)

            discovered.append(
                CompetitorRead(
                    hotel_id=hotel.id,
                    hotel_name=hotel.name,
                    platform_hotel_id=candidate.platform_hotel_id,
                    distance_meters=candidate.distance_meters,
                    address=hotel.address,
                    city=hotel.city,
                )
            )

        self.db.commit()
        return discovered

    def _get_or_create_competitor(self, candidate) -> Hotel:
        existing = self.db.scalar(select(Hotel).where(Hotel.name == candidate.hotel_name, Hotel.address == candidate.address))
        if existing is not None:
            return existing

        hotel = Hotel(
            name=candidate.hotel_name,
            address=candidate.address,
            city=candidate.city,
            lng=candidate.lng,
            lat=candidate.lat,
        )
        self.db.add(hotel)
        self.db.flush()
        return hotel

    def _upsert_group(self, target_hotel_id: int, competitor_hotel_id: int, distance: int) -> None:
        group = self.db.scalar(
            select(CompetitorGroup).where(
                CompetitorGroup.target_hotel_id == target_hotel_id,
                CompetitorGroup.competitor_hotel_id == competitor_hotel_id,
            )
        )
        if group is None:
            group = CompetitorGroup(
                target_hotel_id=target_hotel_id,
                competitor_hotel_id=competitor_hotel_id,
                distance_meters=distance,
                radius_bucket=self._bucket(distance),
                enabled=True,
            )
            self.db.add(group)
            return

        group.distance_meters = distance
        group.radius_bucket = self._bucket(distance)
        group.enabled = True

    def _upsert_mapping(self, hotel_id: int, platform_hotel_id: str, hotel_name: str) -> None:
        mapping = self.db.scalar(
            select(HotelPlatformMapping).where(
                HotelPlatformMapping.platform == "amap",
                HotelPlatformMapping.platform_hotel_id == platform_hotel_id,
            )
        )
        if mapping is None:
            self.db.add(
                HotelPlatformMapping(
                    hotel_id=hotel_id,
                    platform="amap",
                    platform_hotel_id=platform_hotel_id,
                    platform_hotel_name=hotel_name,
                    match_status="matched",
                )
            )

    def _bucket(self, distance: int) -> str:
        if distance <= 1000:
            return "0-1km"
        if distance <= 3000:
            return "1-3km"
        return "3km+"
