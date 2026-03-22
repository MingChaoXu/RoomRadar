from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

from hotel_spider.adapters.base import OtaAdapter, RateCandidate
from hotel_spider.core.config import get_settings


class MockOtaAdapter:
    def __init__(self, platform: str):
        self.platform = platform

    def collect_rates(
        self,
        hotel_name: str,
        city: str | None,
        address: str | None,
        check_in_date: date,
        check_out_date: date,
        adults: int,
        children: int,
    ) -> list[RateCandidate]:
        _ = city, address
        base_price = 320 if self.platform == "meituan" else 360
        hotel_factor = (sum(ord(char) for char in hotel_name) % 70) + adults * 12 + children * 8
        final_base = base_price + hotel_factor
        return [
            RateCandidate(
                platform=self.platform,
                platform_hotel_id=f"{self.platform}-{abs(hash(hotel_name)) % 100000}",
                room_name="高级大床房",
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                display_price=float(final_base + 20),
                final_price=float(final_base),
                breakfast_included=False,
                free_cancel=True,
            ),
            RateCandidate(
                platform=self.platform,
                platform_hotel_id=f"{self.platform}-{abs(hash(hotel_name + 'suite')) % 100000}",
                room_name="豪华双床房",
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                display_price=float(final_base + 90),
                final_price=float(final_base + 70),
                breakfast_included=True,
                free_cancel=False,
            ),
        ]


class CtripPlaywrightAdapter:
    platform = "ctrip"

    def __init__(self, storage_state_path: str, browsers_path: str | None, headless: bool):
        self.storage_state_path = storage_state_path
        self.browsers_path = browsers_path
        self.headless = headless

    def collect_rates(
        self,
        hotel_name: str,
        city: str | None,
        address: str | None,
        check_in_date: date,
        check_out_date: date,
        adults: int,
        children: int,
    ) -> list[RateCandidate]:
        matched = self._search_hotel(keyword=self._build_keyword(hotel_name=hotel_name, city=city))
        if matched is None:
            return []

        hotel_id = matched["hotel_id"]
        detail_url = (
            f"https://m.ctrip.com/webapp/hotel/hoteldetail/{hotel_id}.html"
            f"?checkInDate={check_in_date.isoformat()}"
            f"&checkOutDate={check_out_date.isoformat()}"
            f"&adult={adults}&children={children}&isHideHeader=true"
        )

        return self._fetch_room_rates(
            hotel_id=hotel_id,
            detail_url=detail_url,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
        )

    def _search_hotel(self, keyword: str) -> dict[str, str] | None:
        encoded = urllib.parse.quote(keyword)
        url = f"https://m.ctrip.com/restapi/h5api/globalsearch/search?source=mobileweb&action=mobileweb&keyword={encoded}"
        req = urllib.request.Request(url, headers={"user-agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        for item in payload.get("data", []):
            if item.get("type") != "hotel":
                continue
            word = str(item.get("word", "")).strip()
            detail_url = str(item.get("url", "")).strip()
            hotel_id = self._extract_hotel_id(detail_url)
            if not hotel_id:
                continue
            return {
                "hotel_id": hotel_id,
                "hotel_name": word,
                "detail_url": detail_url,
            }
        return None

    def _fetch_room_rates(
        self,
        hotel_id: str,
        detail_url: str,
        check_in_date: date,
        check_out_date: date,
    ) -> list[RateCandidate]:
        settings = get_settings()
        if self.browsers_path:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self.browsers_path
        room_payload: dict[str, object] | None = None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(storage_state=self.storage_state_path, viewport={"width": 390, "height": 844})
            page = context.new_page()

            def on_response(resp):
                nonlocal room_payload
                if room_payload is not None:
                    return
                if "33278/getHotelRoomListInland" not in resp.url:
                    return
                room_payload = json.loads(resp.text())

            page.on("response", on_response)
            page.goto(detail_url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)
            browser.close()

        if not room_payload:
            return []

        data = room_payload.get("data", {})
        sale_room_map = data.get("saleRoomMap") or {}
        candidates: list[RateCandidate] = []
        for room in sale_room_map.values():
            if len(candidates) >= 8:
                break
            numeric_price = self._extract_numeric_price(room)
            if numeric_price is None:
                continue
            room_name = str(room.get("name") or "").strip()
            platform_hotel_id = str(hotel_id)
            tags = [str(item.get("tagTitle")) for item in room.get("tagInfoList", []) if isinstance(item, dict)]
            breakfast_included = any("早餐" in tag for tag in tags)
            free_cancel = any("免费取消" in tag for tag in tags)
            candidates.append(
                RateCandidate(
                    platform="ctrip",
                    platform_hotel_id=platform_hotel_id,
                    room_name=room_name or "未知房型",
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    display_price=float(numeric_price),
                    final_price=float(numeric_price),
                    breakfast_included=breakfast_included,
                    free_cancel=free_cancel,
                )
            )
        return candidates

    def _extract_numeric_price(self, room: dict[str, object]) -> float | None:
        price_str = room.get("priceStr")
        if isinstance(price_str, (int, float)):
            return float(price_str)
        if isinstance(price_str, str):
            match = re.search(r"\d+(?:\.\d+)?", price_str)
            if match:
                return float(match.group())

        extras = room.get("extras") or {}
        trace_map = {
            item.get("key"): item.get("value")
            for item in extras.get("traceMap", [])
            if isinstance(item, dict) and item.get("key")
        }
        for key in ("totalPriceAfterDiscountIncludeTax", "cashbackAmount"):
            value = trace_map.get(key)
            if isinstance(value, str) and re.fullmatch(r"\d+(?:\.\d+)?", value) and float(value) > 0:
                return float(value)
        return None

    def _build_keyword(self, hotel_name: str, city: str | None) -> str:
        cleaned = hotel_name.strip()
        if city and city not in cleaned:
            return f"{city}{cleaned}"
        return cleaned

    def _extract_hotel_id(self, detail_url: str) -> str | None:
        parsed = urllib.parse.urlparse(detail_url)
        query = urllib.parse.parse_qs(parsed.query)
        if "hotelid" in query and query["hotelid"]:
            return query["hotelid"][0]
        match = re.search(r"/hoteldetail/(\\d+)\\.html", detail_url)
        if match:
            return match.group(1)
        return None


def get_ota_adapter(platform: str) -> OtaAdapter:
    settings = get_settings()
    if platform == "ctrip" and settings.ctrip_provider == "playwright":
        if not settings.ctrip_storage_state_path:
            raise RuntimeError("CTRIP_STORAGE_STATE_PATH is required when CTRIP_PROVIDER=playwright")
        if not Path(settings.ctrip_storage_state_path).exists():
            raise RuntimeError(f"CTRIP storage_state file not found: {settings.ctrip_storage_state_path}")
        return CtripPlaywrightAdapter(
            storage_state_path=settings.ctrip_storage_state_path,
            browsers_path=settings.playwright_browsers_path,
            headless=settings.ctrip_headless,
        )
    if platform not in {"ctrip", "meituan"}:
        raise ValueError(f"Unsupported platform: {platform}")
    return MockOtaAdapter(platform=platform)
