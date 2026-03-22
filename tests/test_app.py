from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from hotel_spider.adapters.amap import AmapMcpAdapter, MockAmapAdapter, Point
from hotel_spider.adapters.ota import MockOtaAdapter
from hotel_spider.db.models import Base, CompetitorGroup, Hotel, RateSnapshot
from hotel_spider.main import create_app
from hotel_spider.schemas.rate import RateCollectionRequest
from hotel_spider.services.discovery import DiscoveryService
from hotel_spider.services.rates import RateCollectionService


def build_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return testing_session()


def test_app_routes_are_registered():
    app = create_app()
    paths = {route.path for route in app.routes}
    assert "/" in paths
    assert "/admin" in paths
    assert "/healthz" in paths
    assert "/api/v1/hotels" in paths
    assert "/api/v1/rates/collect" in paths


def test_discovery_service_creates_competitors(tmp_path: Path):
    db = build_session(tmp_path)
    target_hotel = Hotel(name="上海静安示例酒店", city="上海", address="静安区示例路88号")
    db.add(target_hotel)
    db.commit()
    db.refresh(target_hotel)

    service = DiscoveryService(db=db, adapter=MockAmapAdapter())
    competitors = service.discover(target_hotel=target_hotel, radius_meters=3000, limit=3)

    assert len(competitors) == 3
    groups = list(
        db.scalars(select(CompetitorGroup).where(CompetitorGroup.target_hotel_id == target_hotel.id))
    )
    assert len(groups) == 3


def test_rate_collection_service_persists_snapshots(tmp_path: Path):
    db = build_session(tmp_path)
    target_hotel = Hotel(name="上海静安示例酒店", city="上海", address="静安区示例路88号")
    competitor = Hotel(name="上海静安示例酒店竞品酒店1", city="上海", address="静安区示例路66号")
    db.add(target_hotel)
    db.add(competitor)
    db.commit()
    db.refresh(target_hotel)
    db.refresh(competitor)

    db.add(
        CompetitorGroup(
            target_hotel_id=target_hotel.id,
            competitor_hotel_id=competitor.id,
            distance_meters=800,
            radius_bucket="0-1km",
            enabled=True,
        )
    )
    db.commit()

    service = RateCollectionService(db=db)
    request = RateCollectionRequest(
        target_hotel_id=target_hotel.id,
        check_in_date=date(2026, 4, 1),
        check_out_date=date(2026, 4, 2),
        platforms=["ctrip"],
    )
    snapshots = service.collect(
        adapter=MockOtaAdapter(platform="ctrip"),
        hotels=[competitor],
        query=request,
        platform="ctrip",
    )

    assert len(snapshots) == 2
    saved = list(db.scalars(select(RateSnapshot).where(RateSnapshot.hotel_id == competitor.id)))
    assert len(saved) == 2


class FakeMcpClient:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, object]]] = []

    def call_tool(self, name: str, arguments: dict[str, object]) -> object:
        self.calls.append((name, arguments))
        if name == "maps_geo":
            return {"geocodes": [{"location": "121.4737,31.2304"}]}
        if name == "maps_around_search":
            return {
                "pois": [
                    {
                        "id": "poi-1",
                        "name": "上海静安示例酒店",
                        "location": "121.4737,31.2304",
                        "distance": "0",
                        "cityname": "上海",
                        "address": "静安区示例路88号",
                    },
                    {
                        "id": "poi-2",
                        "name": "上海静安竞品酒店A",
                        "location": "121.4747,31.2314",
                        "distance": "520",
                        "cityname": "上海",
                        "address": "静安区南京西路100号",
                    },
                    {
                        "id": "poi-3",
                        "name": "上海静安竞品酒店B",
                        "location": "121.4767,31.2324",
                        "distance": "860",
                        "cityname": "上海",
                        "address": "静安区北京西路200号",
                    },
                ]
            }
        raise AssertionError(f"Unexpected MCP tool: {name}")


def test_amap_mcp_adapter_extracts_competitors():
    adapter = AmapMcpAdapter(
        command="uvx",
        args=["amap-mcp-server"],
        api_key="dummy",
        timeout_seconds=5,
        hotel_keyword="酒店",
    )
    client = FakeMcpClient()

    point = adapter._resolve_target_location(
        client=client,
        hotel_name="上海静安示例酒店",
        city="上海",
        address="静安区示例路88号",
        lng=None,
        lat=None,
    )
    competitors = adapter._extract_competitors(
        around_result=client.call_tool(
            "maps_around_search",
            {"location": f"{point.lng},{point.lat}", "radius": 3000, "keywords": "酒店"},
        ),
        hotel_name="上海静安示例酒店",
        city="上海",
        limit=10,
    )

    assert point == Point(lng=121.4737, lat=31.2304)
    assert [item.hotel_name for item in competitors] == ["上海静安竞品酒店A", "上海静安竞品酒店B"]
    assert competitors[0].distance_meters == 520
