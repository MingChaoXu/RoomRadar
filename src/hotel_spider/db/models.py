from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class Hotel(Base, TimestampMixin):
    __tablename__ = "hotels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hotel_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    alias_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    star_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    province: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    district: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lng: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    lat: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    business_area: Mapped[str | None] = mapped_column(String(128), nullable=True)


class HotelPlatformMapping(Base, TimestampMixin):
    __tablename__ = "hotel_platform_mapping"
    __table_args__ = (UniqueConstraint("platform", "platform_hotel_id", name="uq_platform_hotel"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    platform_hotel_id: Mapped[str] = mapped_column(String(128), nullable=False)
    platform_hotel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    match_status: Mapped[str] = mapped_column(String(32), default="matched", nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    hotel: Mapped[Hotel] = relationship()


class CompetitorGroup(Base, TimestampMixin):
    __tablename__ = "competitor_groups"
    __table_args__ = (UniqueConstraint("target_hotel_id", "competitor_hotel_id", name="uq_competitor_pair"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    competitor_hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    distance_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    radius_bucket: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="amap", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class RateSnapshot(Base):
    __tablename__ = "rate_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    platform_hotel_id: Mapped[str] = mapped_column(String(128), nullable=False)
    room_name: Mapped[str] = mapped_column(String(255), nullable=False)
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    adults: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    children: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nights: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    currency: Mapped[str] = mapped_column(String(16), default="CNY", nullable=False)
    display_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    final_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    breakfast_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    free_cancel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    inventory_status: Mapped[str] = mapped_column(String(32), default="available", nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    hotel: Mapped[Hotel] = relationship()


class RateCollectionStatus(Base):
    __tablename__ = "rate_collection_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    platform_hotel_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    platform_hotel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    attempt_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    hotel: Mapped[Hotel] = relationship()
