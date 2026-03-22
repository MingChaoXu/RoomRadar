from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class RateCollectionRequest(BaseModel):
    target_hotel_id: int
    check_in_date: date
    check_out_date: date
    adults: int = Field(default=2, ge=1, le=8)
    children: int = Field(default=0, ge=0, le=4)
    platforms: list[str] = Field(default_factory=lambda: ["ctrip", "meituan"])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "target_hotel_id": 1,
                "check_in_date": "2026-04-01",
                "check_out_date": "2026-04-02",
                "adults": 2,
                "children": 0,
                "platforms": ["ctrip", "meituan"],
            }
        }
    )


class RateSnapshotRead(BaseModel):
    hotel_id: int
    hotel_name: str
    platform: str
    platform_hotel_id: str
    room_name: str
    check_in_date: date
    check_out_date: date
    display_price: float
    final_price: float
    breakfast_included: bool
    free_cancel: bool
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RateCollectionResponse(BaseModel):
    target_hotel_id: int
    total_snapshots: int
    snapshots: list[RateSnapshotRead]
