from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from hotel_spider.adapters.amap import get_amap_adapter
from hotel_spider.api.deps import get_db
from hotel_spider.db.models import CompetitorGroup, Hotel, RateCollectionStatus, RateSnapshot
from hotel_spider.schemas.hotel import (
    CompetitorDiscoverRequest,
    CompetitorDiscoverResponse,
    DashboardResponse,
    HotelCreate,
    HotelRead,
)
from hotel_spider.services.discovery import DiscoveryService

router = APIRouter()


def _serialize_collection_status(hotel_name: str, status: RateCollectionStatus) -> dict[str, object]:
    return {
        "hotel_id": status.hotel_id,
        "hotel_name": hotel_name,
        "platform": status.platform,
        "platform_hotel_id": status.platform_hotel_id,
        "platform_hotel_name": status.platform_hotel_name,
        "check_in_date": status.check_in_date,
        "check_out_date": status.check_out_date,
        "attempt_status": status.attempt_status,
        "reason": status.reason,
        "attempted_at": status.attempted_at,
    }


@router.post("", response_model=HotelRead, status_code=status.HTTP_201_CREATED)
def create_hotel(payload: HotelCreate, db: Session = Depends(get_db)) -> Hotel:
    hotel = Hotel(**payload.model_dump())
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel


@router.get("", response_model=list[HotelRead])
def list_hotels(db: Session = Depends(get_db)) -> list[Hotel]:
    return list(db.scalars(select(Hotel).order_by(Hotel.id.desc())))


@router.post("/{hotel_id}/discover-competitors", response_model=CompetitorDiscoverResponse)
def discover_competitors(
    hotel_id: int,
    payload: CompetitorDiscoverRequest,
    db: Session = Depends(get_db),
) -> CompetitorDiscoverResponse:
    target_hotel = db.get(Hotel, hotel_id)
    if target_hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")

    service = DiscoveryService(db=db, adapter=get_amap_adapter())
    discovered = service.discover(target_hotel=target_hotel, radius_meters=payload.radius_meters, limit=payload.limit)

    return CompetitorDiscoverResponse(target_hotel_id=hotel_id, competitors=discovered, total=len(discovered))


@router.get("/{hotel_id}/dashboard", response_model=DashboardResponse)
def hotel_dashboard(
    hotel_id: int,
    check_in_date: date | None = Query(default=None),
    check_out_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    hotel = db.get(Hotel, hotel_id)
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")

    competitors = list(
        db.execute(
            select(CompetitorGroup, Hotel)
            .join(Hotel, Hotel.id == CompetitorGroup.competitor_hotel_id)
            .where(CompetitorGroup.target_hotel_id == hotel_id, CompetitorGroup.enabled.is_(True))
            .order_by(CompetitorGroup.distance_meters.asc())
        )
    )

    hotel_ids = [hotel.id, *[row[1].id for row in competitors]]

    rate_query = (
        select(RateSnapshot)
        .where(RateSnapshot.hotel_id.in_(hotel_ids or [-1]))
        .order_by(desc(RateSnapshot.captured_at))
    )
    if check_in_date:
        rate_query = rate_query.where(RateSnapshot.check_in_date == check_in_date)
    if check_out_date:
        rate_query = rate_query.where(RateSnapshot.check_out_date == check_out_date)

    latest_rates = list(db.scalars(rate_query.limit(200)))

    rate_by_hotel: dict[int, list[RateSnapshot]] = {}
    for rate in latest_rates:
        rate_by_hotel.setdefault(rate.hotel_id, []).append(rate)

    status_query = (
        select(RateCollectionStatus)
        .where(RateCollectionStatus.hotel_id.in_(hotel_ids or [-1]))
        .order_by(desc(RateCollectionStatus.attempted_at))
    )
    if check_in_date:
        status_query = status_query.where(RateCollectionStatus.check_in_date == check_in_date)
    if check_out_date:
        status_query = status_query.where(RateCollectionStatus.check_out_date == check_out_date)

    latest_statuses = list(db.scalars(status_query.limit(200)))
    status_by_hotel: dict[int, list[RateCollectionStatus]] = {}
    seen_status_keys: set[tuple[int, str]] = set()
    for status_row in latest_statuses:
        key = (status_row.hotel_id, status_row.platform)
        if key in seen_status_keys:
            continue
        seen_status_keys.add(key)
        status_by_hotel.setdefault(status_row.hotel_id, []).append(status_row)

    items = []
    for group, competitor in competitors:
        items.append(
            {
                "hotel_id": competitor.id,
                "hotel_name": competitor.name,
                "distance_meters": group.distance_meters,
                "city": competitor.city,
                "address": competitor.address,
                "lng": float(competitor.lng) if competitor.lng is not None else None,
                "lat": float(competitor.lat) if competitor.lat is not None else None,
                "latest_rates": rate_by_hotel.get(competitor.id, []),
                "collection_statuses": [
                    _serialize_collection_status(competitor.name, item)
                    for item in status_by_hotel.get(competitor.id, [])
                ],
            }
        )

    return DashboardResponse(
        target_hotel=hotel,
        target_latest_rates=rate_by_hotel.get(hotel.id, []),
        target_collection_statuses=[
            _serialize_collection_status(hotel.name, item)
            for item in status_by_hotel.get(hotel.id, [])
        ],
        competitors=items,
    )
