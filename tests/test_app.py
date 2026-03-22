from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from hotel_spider.adapters.amap import AmapMcpAdapter, MockAmapAdapter, Point
from hotel_spider.adapters.ota import MeituanPlaywrightAdapter, MockOtaAdapter
from hotel_spider.api.routes.hotels import hotel_dashboard
from hotel_spider.api.routes.rates import collect_rates
from hotel_spider.api.routes.system import runtime_info
from hotel_spider.db.models import Base, CompetitorGroup, Hotel, RateCollectionStatus, RateSnapshot
from hotel_spider.main import create_app
from hotel_spider.schemas.rate import RateCollectionRequest
from hotel_spider.services.discovery import DiscoveryService
from hotel_spider.services.rates import RateCollectionService
from hotel_spider.web.admin import render_admin_html


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
    assert "/api/v1/system/runtime" in paths
    assert "/api/v1/hotels" in paths
    assert "/api/v1/rates/collect" in paths


def test_admin_page_exposes_ctrip_controls():
    html = render_admin_html()

    assert "Ctrip Provider:" in html
    assert "Ctrip State:" in html
    assert "Meituan Provider:" in html
    assert "Meituan State:" in html
    assert "执行采价并刷新看板" in html
    assert "只看低于我方的竞品" in html
    assert "价差从低到高" in html
    assert "低于我方的竞品数" in html
    assert "平台视图" in html
    assert "低价竞品告警" in html
    assert "地图视图" in html
    assert "hotel-map" in html
    assert 'request(`${apiPrefix}/system/runtime`)' in html


def test_runtime_endpoint_reports_amap_and_ctrip_status():
    payload = runtime_info()

    assert "amap_provider" in payload
    assert "amap_api_key_configured" in payload
    assert "amap_js_api_key_configured" in payload
    assert "ctrip_provider" in payload
    assert "ctrip_storage_state_configured" in payload
    assert "ctrip_storage_state_exists" in payload
    assert "meituan_provider" in payload
    assert "meituan_storage_state_configured" in payload
    assert "meituan_storage_state_exists" in payload
    assert "playwright_browsers_path" in payload


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
    collected = service.collect(
        adapter=MockOtaAdapter(platform="ctrip"),
        hotels=[competitor],
        query=request,
        platform="ctrip",
    )

    assert len(collected.snapshots) == 2
    assert len(collected.statuses) == 1
    assert collected.statuses[0].attempt_status == "success"
    saved = list(db.scalars(select(RateSnapshot).where(RateSnapshot.hotel_id == competitor.id)))
    assert len(saved) == 2


def test_collect_rates_includes_target_hotel(monkeypatch, tmp_path: Path):
    db = build_session(tmp_path)
    target_hotel = Hotel(name="上海静安示例酒店", city="上海", address="静安区示例路88号")
    competitor = Hotel(name="上海静安示例酒店竞品酒店1", city="上海", address="静安区示例路66号")
    db.add_all([target_hotel, competitor])
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

    monkeypatch.setattr(
        "hotel_spider.api.routes.rates.get_ota_adapter",
        lambda platform: MockOtaAdapter(platform=platform),
    )

    response = collect_rates(
        payload=RateCollectionRequest(
            target_hotel_id=target_hotel.id,
            check_in_date=date(2026, 4, 1),
            check_out_date=date(2026, 4, 2),
            platforms=["ctrip"],
        ),
        db=db,
    )

    collected_hotel_ids = {snapshot.hotel_id for snapshot in response.snapshots}
    assert collected_hotel_ids == {target_hotel.id, competitor.id}
    assert len(response.statuses) == 2
    assert {status.attempt_status for status in response.statuses} == {"success"}


def test_dashboard_returns_target_latest_rates(tmp_path: Path):
    db = build_session(tmp_path)
    target_hotel = Hotel(name="上海静安示例酒店", city="上海", address="静安区示例路88号")
    competitor = Hotel(name="上海静安示例酒店竞品酒店1", city="上海", address="静安区示例路66号")
    db.add_all([target_hotel, competitor])
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
    db.add_all(
        [
            RateSnapshot(
                hotel_id=target_hotel.id,
                platform="ctrip",
                platform_hotel_id="target-1",
                room_name="豪华大床房",
                check_in_date=date(2026, 4, 1),
                check_out_date=date(2026, 4, 2),
                adults=2,
                children=0,
                nights=1,
                currency="CNY",
                display_price=680,
                final_price=660,
                breakfast_included=True,
                free_cancel=True,
                inventory_status="available",
            ),
            RateSnapshot(
                hotel_id=competitor.id,
                platform="ctrip",
                platform_hotel_id="competitor-1",
                room_name="高级双床房",
                check_in_date=date(2026, 4, 1),
                check_out_date=date(2026, 4, 2),
                adults=2,
                children=0,
                nights=1,
                currency="CNY",
                display_price=620,
                final_price=610,
                breakfast_included=False,
                free_cancel=True,
                inventory_status="available",
            ),
            RateCollectionStatus(
                hotel_id=target_hotel.id,
                platform="ctrip",
                platform_hotel_id="target-1",
                platform_hotel_name=target_hotel.name,
                check_in_date=date(2026, 4, 1),
                check_out_date=date(2026, 4, 2),
                attempt_status="success",
                reason=None,
            ),
            RateCollectionStatus(
                hotel_id=competitor.id,
                platform="meituan",
                platform_hotel_id=None,
                platform_hotel_name=None,
                check_in_date=date(2026, 4, 1),
                check_out_date=date(2026, 4, 2),
                attempt_status="unmatched",
                reason="美团未匹配到酒店",
            ),
        ]
    )
    db.commit()

    dashboard = hotel_dashboard(
        hotel_id=target_hotel.id,
        check_in_date=date(2026, 4, 1),
        check_out_date=date(2026, 4, 2),
        db=db,
    )

    assert dashboard.target_hotel.id == target_hotel.id
    assert len(dashboard.target_latest_rates) == 1
    assert len(dashboard.target_collection_statuses) == 1
    assert dashboard.target_latest_rates[0].final_price == 660
    assert len(dashboard.competitors) == 1
    assert dashboard.competitors[0].latest_rates[0].final_price == 610
    assert dashboard.competitors[0].collection_statuses[0].reason == "美团未匹配到酒店"
    assert dashboard.competitors[0].lng is None


def test_mock_ota_adapter_accepts_hotel_context():
    adapter = MockOtaAdapter(platform="ctrip")
    results = adapter.collect_rates(
        hotel_name="上海静安示例酒店竞品酒店1",
        city="上海",
        address="静安区示例路66号",
        check_in_date=date(2026, 4, 1),
        check_out_date=date(2026, 4, 2),
        adults=2,
        children=0,
    )
    assert results.status == "success"
    assert len(results.rates) == 2
    assert results.rates[0].platform == "ctrip"


def test_meituan_adapter_matches_best_candidate():
    adapter = MeituanPlaywrightAdapter(storage_state_path=None, browsers_path=None, headless=True)

    matched = adapter._match_hotel(
        hotels=[
            {"name": "上海南京路示例酒店", "poiid": 1},
            {"name": "上海璞丽酒店", "poiid": 2},
            {"name": "上海璞丽公寓", "poiid": 3},
        ],
        hotel_name="上海璞丽",
    )

    assert matched is not None
    assert matched["poiid"] == 2


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
