from __future__ import annotations

import json
import os
import re
import string
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from hotel_spider.adapters.base import OtaAdapter, RateCandidate, RateCollectionResult
from hotel_spider.core.config import get_settings


def _normalize_hotel_name(name: str) -> str:
    table = str.maketrans("", "", string.whitespace + string.punctuation + "（）()·-")
    normalized = name.translate(table).lower()
    for suffix in ("大酒店", "酒店", "宾馆", "民宿", "公寓", "饭店"):
        normalized = normalized.replace(suffix, "")
    return normalized


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
    ) -> RateCollectionResult:
        _ = city, address
        base_price = 320 if self.platform == "meituan" else 360
        hotel_factor = (sum(ord(char) for char in hotel_name) % 70) + adults * 12 + children * 8
        final_base = base_price + hotel_factor
        return RateCollectionResult(
            platform=self.platform,
            status="success",
            reason=None,
            platform_hotel_id=f"{self.platform}-{abs(hash(hotel_name)) % 100000}",
            platform_hotel_name=hotel_name,
            rates=[
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
            ],
        )


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
    ) -> RateCollectionResult:
        matched = self._search_hotel(keyword=self._build_keyword(hotel_name=hotel_name, city=city))
        if matched is None:
            return RateCollectionResult(
                platform="ctrip",
                status="unmatched",
                reason="携程未匹配到酒店",
                rates=[],
            )

        hotel_id = matched["hotel_id"]
        detail_url = (
            f"https://m.ctrip.com/webapp/hotel/hoteldetail/{hotel_id}.html"
            f"?checkInDate={check_in_date.isoformat()}"
            f"&checkOutDate={check_out_date.isoformat()}"
            f"&adult={adults}&children={children}&isHideHeader=true"
        )

        return self._fetch_room_rates(
            hotel_id=hotel_id,
            hotel_name=matched.get("hotel_name") or hotel_name,
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
        hotel_name: str,
        detail_url: str,
        check_in_date: date,
        check_out_date: date,
    ) -> RateCollectionResult:
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
            return RateCollectionResult(
                platform="ctrip",
                status="fetch_failed",
                reason="未捕获到携程房型接口",
                rates=[],
                platform_hotel_id=hotel_id,
                platform_hotel_name=hotel_name,
            )

        data = room_payload.get("data", {})
        sale_room_map = data.get("saleRoomMap") or {}
        candidates: list[RateCandidate] = []
        had_rooms = bool(sale_room_map)
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
        if candidates:
            return RateCollectionResult(
                platform="ctrip",
                status="success",
                reason=None,
                rates=candidates,
                platform_hotel_id=hotel_id,
                platform_hotel_name=hotel_name,
            )
        if had_rooms:
            return RateCollectionResult(
                platform="ctrip",
                status="price_unavailable",
                reason="有房型但未拿到数值价格",
                rates=[],
                platform_hotel_id=hotel_id,
                platform_hotel_name=hotel_name,
            )
        return RateCollectionResult(
            platform="ctrip",
            status="no_inventory",
            reason="当前日期无可售房型",
            rates=[],
            platform_hotel_id=hotel_id,
            platform_hotel_name=hotel_name,
        )

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


class MeituanPlaywrightAdapter:
    platform = "meituan"

    def __init__(self, storage_state_path: str | None, browsers_path: str | None, headless: bool):
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
    ) -> RateCollectionResult:
        _ = address, adults, children
        if not city:
            return RateCollectionResult(
                platform="meituan",
                status="missing_city",
                reason="缺少城市信息，无法查询美团",
                rates=[],
            )

        city_match = self._resolve_city(city)
        if city_match is None:
            return RateCollectionResult(
                platform="meituan",
                status="city_unmatched",
                reason="美团未匹配到城市",
                rates=[],
            )

        list_url = (
            "https://i.meituan.com/awp/h5/hotel/list/list.html?"
            + urllib.parse.urlencode(
                {
                    "cityId": city_match["city_id"],
                    "checkIn": check_in_date.isoformat(),
                    "checkOut": check_out_date.isoformat(),
                    "keyword": hotel_name,
                    "accommodationType": 1,
                }
            )
        )

        if self.browsers_path:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self.browsers_path

        payload: dict[str, object] | None = None
        final_url = list_url
        search_request_url: str | None = None
        mobile_user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context_kwargs = dict(p.devices["iPhone 13"])
            if self.storage_state_path:
                context_kwargs["storage_state"] = self.storage_state_path
            context = browser.new_context(**context_kwargs)
            page = context.new_page()

            def on_request(req):
                nonlocal search_request_url
                if "hbsearch/HotelSearch" in req.url:
                    search_request_url = req.url

            def on_response(resp):
                nonlocal payload
                if "hbsearch/HotelSearch" not in resp.url or resp.status != 200:
                    return
                try:
                    candidate_payload = json.loads(resp.text())
                except json.JSONDecodeError:
                    return
                if payload is None or self._payload_has_results(candidate_payload):
                    payload = candidate_payload

            page.on("request", on_request)
            page.on("response", on_response)
            page.goto(list_url, wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                pass
            page.wait_for_timeout(2000)
            final_url = page.url
            browser.close()

        if "passport.meituan.com" in final_url:
            return RateCollectionResult(
                platform="meituan",
                status="login_required",
                reason="美团需要登录态",
                rates=[],
            )

        if payload is None and search_request_url:
            try:
                payload = self._fetch_search_payload(
                    request_url=search_request_url,
                    referer=list_url,
                    user_agent=mobile_user_agent,
                )
            except Exception:
                payload = None

        if self._is_risk_blocked(payload):
            return RateCollectionResult(
                platform="meituan",
                status="blocked",
                reason=self._blocked_reason(payload),
                rates=[],
            )

        if not payload:
            return RateCollectionResult(
                platform="meituan",
                status="fetch_failed",
                reason="未捕获到美团酒店列表接口",
                rates=[],
            )

        data = payload.get("data") or {}
        search_results = list(data.get("searchresult") or [])
        recommend_results = list(data.get("recommend") or [])
        merged = [item for item in [*search_results, *recommend_results] if isinstance(item, dict)]
        if not merged:
            return RateCollectionResult(
                platform="meituan",
                status="no_inventory",
                reason="当前日期无可售酒店列表",
                rates=[],
            )

        matched = self._match_hotel(merged, hotel_name)
        if matched is None:
            return RateCollectionResult(
                platform="meituan",
                status="unmatched",
                reason="美团列表未匹配到酒店",
                rates=[],
            )

        lowest_price = matched.get("lowestPrice")
        if lowest_price in (None, "", 0, "0"):
            return RateCollectionResult(
                platform="meituan",
                status="price_unavailable",
                reason="美团酒店已匹配但未拿到列表价",
                rates=[],
                platform_hotel_id=str(matched.get("poiid") or matched.get("poiId") or ""),
                platform_hotel_name=str(matched.get("name") or hotel_name),
            )

        try:
            numeric_price = float(lowest_price)
        except (TypeError, ValueError):
            return RateCollectionResult(
                platform="meituan",
                status="price_unavailable",
                reason="美团列表价格不可解析",
                rates=[],
                platform_hotel_id=str(matched.get("poiid") or matched.get("poiId") or ""),
                platform_hotel_name=str(matched.get("name") or hotel_name),
            )

        platform_hotel_id = str(matched.get("poiid") or matched.get("poiId") or "")
        platform_hotel_name = str(matched.get("name") or hotel_name)
        return RateCollectionResult(
            platform="meituan",
            status="success",
            reason=None,
            platform_hotel_id=platform_hotel_id or None,
            platform_hotel_name=platform_hotel_name,
            rates=[
                RateCandidate(
                    platform="meituan",
                    platform_hotel_id=platform_hotel_id or f"meituan-{abs(hash(platform_hotel_name)) % 100000}",
                    room_name="列表最低价",
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    display_price=numeric_price,
                    final_price=numeric_price,
                    breakfast_included=False,
                    free_cancel=False,
                )
            ],
        )

    def _resolve_city(self, city_name: str) -> dict[str, object] | None:
        url = "https://ihotel.meituan.com/group/v1/area/search/" + urllib.parse.quote(city_name)
        req = urllib.request.Request(
            url,
            headers={
                "user-agent": "Mozilla/5.0",
                "referer": "https://i.meituan.com/awp/h5/hotel/search/search.html",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        city_items = [item for item in payload.get("data", []) if item.get("tag") == "城市"]
        normalized_target = _normalize_hotel_name(city_name)
        for item in city_items:
            city_label = str(item.get("cityName") or item.get("name") or "")
            if _normalize_hotel_name(city_label).startswith(normalized_target):
                return {
                    "city_id": item.get("cityId"),
                    "city_name": item.get("cityName") or city_label,
                }
        if city_items:
            item = city_items[0]
            return {
                "city_id": item.get("cityId"),
                "city_name": item.get("cityName") or item.get("name"),
            }
        return None

    def _match_hotel(self, hotels: list[dict[str, object]], hotel_name: str) -> dict[str, object] | None:
        normalized_target = _normalize_hotel_name(hotel_name)
        scored: list[tuple[int, dict[str, object]]] = []
        for item in hotels:
            name = str(item.get("name") or "")
            normalized_name = _normalize_hotel_name(name)
            score = 0
            if normalized_name == normalized_target:
                score += 100
            if normalized_target and normalized_target in normalized_name:
                score += 40
            if normalized_name and normalized_name in normalized_target:
                score += 20
            if "酒店" in name or "大酒店" in name:
                score += 5
            scored.append((score, item))
        scored.sort(key=lambda item: item[0], reverse=True)
        if scored and scored[0][0] > 0:
            return scored[0][1]
        return None

    def _payload_has_results(self, payload: dict[str, object]) -> bool:
        data = payload.get("data") or {}
        search_results = data.get("searchresult") or []
        recommend_results = data.get("recommend") or []
        return bool(search_results or recommend_results)

    def _is_risk_blocked(self, payload: dict[str, object] | None) -> bool:
        if not payload:
            return False
        code = payload.get("code")
        if code == 406:
            return True
        custom_data = payload.get("customData")
        if isinstance(custom_data, dict) and custom_data.get("verifyUrl"):
            return True
        msg = str(payload.get("msg") or "")
        if "稍后再试" not in msg:
            return False
        if isinstance(custom_data, dict):
            return "verify" in json.dumps(custom_data, ensure_ascii=False)
        return False

    def _blocked_reason(self, payload: dict[str, object]) -> str:
        custom_data = payload.get("customData")
        if isinstance(custom_data, dict):
            verify_page_url = custom_data.get("verifyPageUrl") or custom_data.get("verifyUrl")
            if verify_page_url:
                return f"美团触发风控验证，请先完成验证: {verify_page_url}"
        return "美团触发风控验证"

    def _fetch_search_payload(self, request_url: str, referer: str, user_agent: str) -> dict[str, object] | None:
        headers = {
            "user-agent": user_agent,
            "referer": referer,
            "accept": "application/json, text/plain, */*",
        }
        cookie_header = self._build_cookie_header()
        if cookie_header:
            headers["cookie"] = cookie_header
        req = urllib.request.Request(request_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _build_cookie_header(self) -> str | None:
        if not self.storage_state_path:
            return None
        state = json.loads(Path(self.storage_state_path).read_text(encoding="utf-8"))
        cookies = []
        for item in state.get("cookies", []):
            domain = str(item.get("domain") or "")
            if "meituan.com" not in domain:
                continue
            name = item.get("name")
            value = item.get("value")
            if not name or value is None:
                continue
            cookies.append(f"{name}={value}")
        return "; ".join(cookies) if cookies else None


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
    if platform == "meituan" and settings.meituan_provider == "playwright":
        storage_state_path = settings.meituan_storage_state_path
        if storage_state_path and not Path(storage_state_path).exists():
            raise RuntimeError(f"MEITUAN storage_state file not found: {storage_state_path}")
        return MeituanPlaywrightAdapter(
            storage_state_path=storage_state_path,
            browsers_path=settings.playwright_browsers_path,
            headless=settings.meituan_headless,
        )
    if platform not in {"ctrip", "meituan"}:
        raise ValueError(f"Unsupported platform: {platform}")
    return MockOtaAdapter(platform=platform)
