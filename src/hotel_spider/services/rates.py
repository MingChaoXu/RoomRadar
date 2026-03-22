from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from hotel_spider.adapters.base import OtaAdapter
from hotel_spider.db.models import Hotel, RateCollectionStatus, RateSnapshot
from hotel_spider.schemas.rate import RateCollectionRequest, RateCollectionStatusRead, RateSnapshotRead


@dataclass
class CollectedPlatformResult:
    snapshots: list[RateSnapshotRead]
    statuses: list[RateCollectionStatusRead]


class RateCollectionService:
    def __init__(self, db: Session):
        self.db = db

    def collect(
        self,
        adapter: OtaAdapter,
        hotels: list[Hotel],
        query: RateCollectionRequest,
        platform: str,
    ) -> CollectedPlatformResult:
        snapshots: list[RateSnapshotRead] = []
        statuses: list[RateCollectionStatusRead] = []

        for hotel in hotels:
            result = adapter.collect_rates(
                hotel_name=hotel.name,
                city=hotel.city,
                address=hotel.address,
                check_in_date=query.check_in_date,
                check_out_date=query.check_out_date,
                adults=query.adults,
                children=query.children,
            )

            status = RateCollectionStatus(
                hotel_id=hotel.id,
                platform=platform,
                platform_hotel_id=result.platform_hotel_id,
                platform_hotel_name=result.platform_hotel_name,
                check_in_date=query.check_in_date,
                check_out_date=query.check_out_date,
                attempt_status=result.status,
                reason=result.reason,
                attempted_at=datetime.now(UTC),
            )
            self.db.add(status)
            self.db.flush()
            statuses.append(
                RateCollectionStatusRead(
                    hotel_id=hotel.id,
                    hotel_name=hotel.name,
                    platform=platform,
                    platform_hotel_id=result.platform_hotel_id,
                    platform_hotel_name=result.platform_hotel_name,
                    check_in_date=query.check_in_date,
                    check_out_date=query.check_out_date,
                    attempt_status=result.status,
                    reason=result.reason,
                    attempted_at=status.attempted_at,
                )
            )

            for item in result.rates:
                snapshot = RateSnapshot(
                    hotel_id=hotel.id,
                    platform=platform,
                    platform_hotel_id=item.platform_hotel_id,
                    room_name=item.room_name,
                    check_in_date=item.check_in_date,
                    check_out_date=item.check_out_date,
                    adults=query.adults,
                    children=query.children,
                    nights=(query.check_out_date - query.check_in_date).days,
                    currency="CNY",
                    display_price=item.display_price,
                    final_price=item.final_price,
                    breakfast_included=item.breakfast_included,
                    free_cancel=item.free_cancel,
                    inventory_status="available",
                    captured_at=datetime.now(UTC),
                )
                self.db.add(snapshot)
                self.db.flush()
                snapshots.append(
                    RateSnapshotRead(
                        hotel_id=hotel.id,
                        hotel_name=hotel.name,
                        platform=platform,
                        platform_hotel_id=item.platform_hotel_id,
                        room_name=item.room_name,
                        check_in_date=item.check_in_date,
                        check_out_date=item.check_out_date,
                        display_price=float(item.display_price),
                        final_price=float(item.final_price),
                        breakfast_included=item.breakfast_included,
                        free_cancel=item.free_cancel,
                        captured_at=snapshot.captured_at,
                    )
                )

        self.db.commit()
        return CollectedPlatformResult(snapshots=snapshots, statuses=statuses)
