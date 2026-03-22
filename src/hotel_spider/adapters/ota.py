from datetime import date

from hotel_spider.adapters.base import OtaAdapter, RateCandidate


class MockOtaAdapter:
    def __init__(self, platform: str):
        self.platform = platform

    def collect_rates(
        self,
        hotel_name: str,
        check_in_date: date,
        check_out_date: date,
        adults: int,
        children: int,
    ) -> list[RateCandidate]:
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


def get_ota_adapter(platform: str) -> OtaAdapter:
    if platform not in {"ctrip", "meituan"}:
        raise ValueError(f"Unsupported platform: {platform}")
    return MockOtaAdapter(platform=platform)
