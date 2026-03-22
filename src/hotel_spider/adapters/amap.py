from __future__ import annotations

import json
import math
import os
import shlex
import select
import subprocess
from dataclasses import dataclass
from itertools import count

from hotel_spider.adapters.base import AmapAdapter, CompetitorCandidate
from hotel_spider.core.config import get_settings


class McpProtocolError(RuntimeError):
    pass


@dataclass
class Point:
    lng: float
    lat: float


class StdioMcpClient:
    def __init__(self, command: str, args: list[str], env: dict[str, str], timeout_seconds: float):
        self._request_ids = count(1)
        self._process = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        self._timeout_seconds = timeout_seconds
        self._initialize()

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def call_tool(self, name: str, arguments: dict[str, object]) -> object:
        result = self._request("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise McpProtocolError(f"MCP tool call failed for {name}: {result}")
        return self._extract_payload(result)

    def _initialize(self) -> None:
        self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "hotel-spider", "version": "0.1.0"},
            },
        )
        self._notify("notifications/initialized", {})

    def _notify(self, method: str, params: dict[str, object]) -> None:
        message = {"jsonrpc": "2.0", "method": method, "params": params}
        self._write_message(message)

    def _request(self, method: str, params: dict[str, object]) -> dict[str, object]:
        request_id = next(self._request_ids)
        message = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        self._write_message(message)
        while True:
            response = self._read_message()
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise McpProtocolError(f"MCP error for {method}: {response['error']}")
            result = response.get("result")
            if not isinstance(result, dict):
                raise McpProtocolError(f"Unexpected MCP result for {method}: {response}")
            return result

    def _write_message(self, message: dict[str, object]) -> None:
        if self._process.stdin is None:
            raise McpProtocolError("MCP stdin is unavailable")
        body = json.dumps(message, ensure_ascii=False).encode("utf-8") + b"\n"
        self._process.stdin.write(body)
        self._process.stdin.flush()

    def _read_message(self) -> dict[str, object]:
        if self._process.stdout is None:
            raise McpProtocolError("MCP stdout is unavailable")

        self._wait_for_stdout()
        body = self._process.stdout.readline()
        if not body:
            stderr = self._read_stderr()
            raise McpProtocolError(f"Missing MCP body. stderr={stderr}")

        return json.loads(body.decode("utf-8").strip())

    def _wait_for_stdout(self) -> None:
        if self._process.stdout is None:
            raise McpProtocolError("MCP stdout is unavailable")
        readable, _, _ = select.select([self._process.stdout], [], [], self._timeout_seconds)
        if not readable:
            raise McpProtocolError(f"MCP read timed out after {self._timeout_seconds} seconds")

    def _read_stderr(self) -> str:
        if self._process.stderr is None:
            return ""
        try:
            return self._process.stderr.read1(4096).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _extract_payload(self, result: dict[str, object]) -> object:
        structured = result.get("structuredContent")
        if structured is not None:
            return structured

        content = result.get("content")
        if not isinstance(content, list):
            return result

        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text":
                text = str(item.get("text", "")).strip()
                parsed = self._try_parse_json(text)
                if parsed is not None:
                    return parsed
            if item.get("type") == "json" and "json" in item:
                return item["json"]

        return result

    def _try_parse_json(self, text: str) -> object | None:
        if not text:
            return None
        candidate = text.strip()
        if candidate.startswith("```"):
            lines = candidate.splitlines()
            if len(lines) >= 3:
                candidate = "\n".join(lines[1:-1]).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None


class MockAmapAdapter:
    def discover_competitors(
        self,
        hotel_name: str,
        city: str | None,
        address: str | None,
        lng: float | None,
        lat: float | None,
        radius_meters: int,
        limit: int,
    ) -> list[CompetitorCandidate]:
        base_city = city or "上海"
        _ = address, lng, lat, radius_meters
        return [
            CompetitorCandidate(
                platform_hotel_id=f"amap-{idx}",
                hotel_name=f"{hotel_name}竞品酒店{idx}",
                address=f"{base_city}市示例路{idx}号",
                city=base_city,
                distance_meters=300 + idx * 180,
                lng=121.470000 + idx * 0.001,
                lat=31.230000 + idx * 0.001,
            )
            for idx in range(1, limit + 1)
        ]


class AmapMcpAdapter:
    NON_HOTEL_NAME_KEYWORDS = (
        "停车",
        "出入口",
        "礼宾部",
        "餐厅",
        "酒吧",
        "健体中心",
        "贵宾廊",
        "宴会中心",
        "大堂酒廊",
        "咖啡",
    )

    def __init__(
        self,
        command: str,
        args: list[str],
        api_key: str,
        timeout_seconds: float,
        hotel_keyword: str,
    ):
        self._command = command
        self._args = args
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._hotel_keyword = hotel_keyword

    def discover_competitors(
        self,
        hotel_name: str,
        city: str | None,
        address: str | None,
        lng: float | None,
        lat: float | None,
        radius_meters: int,
        limit: int,
    ) -> list[CompetitorCandidate]:
        env = os.environ.copy()
        env["AMAP_MAPS_API_KEY"] = self._api_key
        client = StdioMcpClient(
            command=self._command,
            args=self._args,
            env=env,
            timeout_seconds=self._timeout_seconds,
        )
        try:
            center = self._resolve_target_location(
                client=client,
                hotel_name=hotel_name,
                city=city,
                address=address,
                lng=lng,
                lat=lat,
            )
            around_result = client.call_tool(
                "maps_around_search",
                {
                    "location": f"{center.lng},{center.lat}",
                    "radius": radius_meters,
                    "keywords": self._hotel_keyword,
                },
            )
            return self._extract_competitors(
                around_result=around_result,
                hotel_name=hotel_name,
                city=city,
                limit=limit,
                client=client,
                center=center,
            )
        finally:
            client.close()

    def _resolve_target_location(
        self,
        client: StdioMcpClient,
        hotel_name: str,
        city: str | None,
        address: str | None,
        lng: float | None,
        lat: float | None,
    ) -> Point:
        if lng is not None and lat is not None:
            return Point(lng=lng, lat=lat)

        if address:
            geo_result = client.call_tool("maps_geo", {"address": address, "city": city} if city else {"address": address})
            point = self._extract_first_point(geo_result)
            if point is not None:
                return point

        text_result = client.call_tool(
            "maps_text_search",
            {
                "keywords": hotel_name,
                "city": city,
                "citylimit": True,
            }
            if city
            else {"keywords": hotel_name},
        )
        pois = self._extract_pois(text_result)
        for poi in pois:
            if poi.get("name") == hotel_name:
                point = self._point_from_poi(poi)
                if point is not None:
                    return point

        if pois:
            point = self._point_from_poi(pois[0])
            if point is not None:
                return point

        raise McpProtocolError(f"Unable to resolve location for hotel: {hotel_name}")

    def _extract_competitors(
        self,
        around_result: object,
        hotel_name: str,
        city: str | None,
        limit: int,
        client: StdioMcpClient | None = None,
        center: Point | None = None,
    ) -> list[CompetitorCandidate]:
        candidates: list[CompetitorCandidate] = []
        for poi in self._extract_pois(around_result):
            name = str(poi.get("name", "")).strip()
            if not name or self._same_hotel_name(name, hotel_name) or not self._is_competitor_candidate(name):
                continue
            resolved_poi = poi
            point = self._point_from_poi(resolved_poi)
            if point is None and client is not None and poi.get("id"):
                try:
                    detail = client.call_tool("maps_search_detail", {"id": str(poi["id"])})
                    if isinstance(detail, dict):
                        resolved_poi = {**poi, **detail}
                        point = self._point_from_poi(resolved_poi)
                except Exception:
                    point = None
            if point is None:
                continue
            poi_city = self._normalize_city(resolved_poi.get("cityname") or resolved_poi.get("city") or city)
            distance = self._extract_distance_meters(resolved_poi, center=center, point=point)
            address = str(resolved_poi.get("address") or resolved_poi.get("pname") or "") or None
            platform_hotel_id = str(resolved_poi.get("id") or resolved_poi.get("poiid") or f"amap-{name}-{distance}")
            candidates.append(
                CompetitorCandidate(
                    platform_hotel_id=platform_hotel_id,
                    hotel_name=name,
                    address=address or "",
                    city=poi_city,
                    distance_meters=distance,
                    lng=point.lng,
                    lat=point.lat,
                )
            )
            if len(candidates) >= limit:
                break
        return candidates

    def _extract_first_point(self, payload: object) -> Point | None:
        if isinstance(payload, dict):
            geocodes = payload.get("geocodes")
            if isinstance(geocodes, list) and geocodes:
                return self._point_from_poi(geocodes[0])
            returned = payload.get("return")
            if isinstance(returned, list) and returned:
                return self._point_from_poi(returned[0])
        return None

    def _extract_pois(self, payload: object) -> list[dict[str, object]]:
        if isinstance(payload, dict):
            if isinstance(payload.get("pois"), list):
                return [item for item in payload["pois"] if isinstance(item, dict)]
            if isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("pois"), list):
                return [item for item in payload["data"]["pois"] if isinstance(item, dict)]
            if isinstance(payload.get("results"), list):
                return [item for item in payload["results"] if isinstance(item, dict)]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    def _point_from_poi(self, poi: dict[str, object]) -> Point | None:
        location = poi.get("location")
        if isinstance(location, str) and "," in location:
            lng, lat = location.split(",", 1)
            return Point(lng=float(lng), lat=float(lat))
        lng = poi.get("lng")
        lat = poi.get("lat")
        if lng is not None and lat is not None:
            return Point(lng=float(lng), lat=float(lat))
        return None

    def _normalize_city(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _same_hotel_name(self, left: str, right: str) -> bool:
        normalized_left = self._normalize_hotel_name(left)
        normalized_right = self._normalize_hotel_name(right)
        if not normalized_left or not normalized_right:
            return False
        if normalized_left == normalized_right:
            return True
        return normalized_left in normalized_right or normalized_right in normalized_left

    def _extract_distance_meters(self, poi: dict[str, object], center: Point | None, point: Point) -> int:
        raw_distance = poi.get("distance")
        if raw_distance not in (None, "", []):
            return int(float(raw_distance))
        if center is None:
            return 0
        return int(self._haversine_meters(center, point))

    def _haversine_meters(self, origin: Point, target: Point) -> float:
        radius = 6371000
        lat1 = math.radians(origin.lat)
        lat2 = math.radians(target.lat)
        dlat = lat2 - lat1
        dlng = math.radians(target.lng - origin.lng)
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        return 2 * radius * math.asin(math.sqrt(a))

    def _normalize_hotel_name(self, value: str) -> str:
        return "".join(char for char in value.lower() if char.isalnum())

    def _is_competitor_candidate(self, value: str) -> bool:
        return not any(keyword in value for keyword in self.NON_HOTEL_NAME_KEYWORDS)


def get_amap_adapter() -> AmapAdapter:
    settings = get_settings()
    if settings.amap_provider == "mcp":
        if not settings.amap_maps_api_key:
            raise RuntimeError("AMAP_MAPS_API_KEY is required when AMAP_PROVIDER=mcp")
        return AmapMcpAdapter(
            command=settings.amap_mcp_command,
            args=shlex.split(settings.amap_mcp_args),
            api_key=settings.amap_maps_api_key,
            timeout_seconds=settings.amap_mcp_timeout_seconds,
            hotel_keyword=settings.amap_hotel_keyword,
        )
    return MockAmapAdapter()
