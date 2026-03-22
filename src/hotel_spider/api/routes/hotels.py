from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from hotel_spider.adapters.amap import get_amap_adapter
from hotel_spider.api.deps import get_db
from hotel_spider.db.models import CompetitorGroup, Hotel, RateSnapshot
from hotel_spider.schemas.hotel import (
    CompetitorDiscoverRequest,
    CompetitorDiscoverResponse,
    DashboardResponse,
    HotelCreate,
    HotelRead,
)
from hotel_spider.services.discovery import DiscoveryService

router = APIRouter()


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

    rate_query = (
        select(RateSnapshot)
        .where(RateSnapshot.hotel_id.in_([row[1].id for row in competitors] or [-1]))
        .order_by(desc(RateSnapshot.captured_at))
    )
    if check_in_date:
        rate_query = rate_query.where(RateSnapshot.check_in_date == check_in_date)

    latest_rates = list(db.scalars(rate_query.limit(200)))

    rate_by_hotel: dict[int, list[RateSnapshot]] = {}
    for rate in latest_rates:
        rate_by_hotel.setdefault(rate.hotel_id, []).append(rate)

    items = []
    for group, competitor in competitors:
        items.append(
            {
                "hotel_id": competitor.id,
                "hotel_name": competitor.name,
                "distance_meters": group.distance_meters,
                "latest_rates": rate_by_hotel.get(competitor.id, []),
            }
        )

    return DashboardResponse(
        target_hotel=hotel,
        competitors=items,
    )
