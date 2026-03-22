from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from hotel_spider.adapters.ota import get_ota_adapter
from hotel_spider.api.deps import get_db
from hotel_spider.db.models import CompetitorGroup, Hotel
from hotel_spider.schemas.rate import RateCollectionRequest, RateCollectionResponse
from hotel_spider.services.rates import RateCollectionService

router = APIRouter()


@router.post("/collect", response_model=RateCollectionResponse)
def collect_rates(payload: RateCollectionRequest, db: Session = Depends(get_db)) -> RateCollectionResponse:
    target_hotel = db.get(Hotel, payload.target_hotel_id)
    if target_hotel is None:
        raise HTTPException(status_code=404, detail="Target hotel not found")

    competitor_ids = list(
        db.scalars(
            select(CompetitorGroup.competitor_hotel_id).where(
                CompetitorGroup.target_hotel_id == payload.target_hotel_id,
                CompetitorGroup.enabled.is_(True),
            )
        )
    )
    if not competitor_ids:
        raise HTTPException(status_code=400, detail="No active competitors found for target hotel")

    competitor_hotels = list(db.scalars(select(Hotel).where(Hotel.id.in_(competitor_ids))))
    hotels_by_id = {target_hotel.id: target_hotel}
    hotels_by_id.update({hotel.id: hotel for hotel in competitor_hotels})
    hotels = list(hotels_by_id.values())

    service = RateCollectionService(db=db)
    snapshots = []
    statuses = []
    for platform in payload.platforms:
        adapter = get_ota_adapter(platform)
        collected = service.collect(adapter=adapter, hotels=hotels, query=payload, platform=platform)
        snapshots.extend(collected.snapshots)
        statuses.extend(collected.statuses)

    return RateCollectionResponse(
        target_hotel_id=payload.target_hotel_id,
        total_snapshots=len(snapshots),
        statuses=statuses,
        snapshots=snapshots,
    )
