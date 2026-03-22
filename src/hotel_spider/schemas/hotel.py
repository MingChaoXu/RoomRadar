from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class HotelBase(BaseModel):
    name: str
    alias_name: str | None = None
    brand: str | None = None
    star_level: int | None = Field(default=None, ge=0, le=5)
    province: str | None = None
    city: str | None = None
    district: str | None = None
    address: str | None = None
    lng: float | None = None
    lat: float | None = None
    business_area: str | None = None


class HotelCreate(HotelBase):
    hotel_code: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "上海静安示例酒店",
                "city": "上海",
                "address": "静安区示例路 88 号",
                "brand": "示例品牌",
                "star_level": 4,
            }
        }
    )


class HotelRead(HotelBase):
    id: int
    hotel_code: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitorDiscoverRequest(BaseModel):
    radius_meters: int = Field(default=3000, ge=100, le=10000)
    limit: int = Field(default=20, ge=1, le=50)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "radius_meters": 3000,
                "limit": 20,
            }
        }
    )


class CompetitorRead(BaseModel):
    hotel_id: int
    hotel_name: str
    platform_hotel_id: str
    distance_meters: int
    address: str | None = None
    city: str | None = None


class CompetitorDiscoverResponse(BaseModel):
    target_hotel_id: int
    total: int
    competitors: list[CompetitorRead]


class SnapshotRead(BaseModel):
    platform: str
    room_name: str
    check_in_date: date
    check_out_date: date
    display_price: float
    final_price: float
    breakfast_included: bool
    free_cancel: bool
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardCompetitorItem(BaseModel):
    hotel_id: int
    hotel_name: str
    distance_meters: int | None = None
    latest_rates: list[SnapshotRead]


class DashboardResponse(BaseModel):
    target_hotel: HotelRead
    competitors: list[DashboardCompetitorItem]
