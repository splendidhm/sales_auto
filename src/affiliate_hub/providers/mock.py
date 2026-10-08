from datetime import datetime, timezone

from affiliate_hub.models import Product


class MockProductProvider:
    """Exactly three fictional products; no prices, images or affiliate links."""

    def fetch(self) -> list[Product]:
        observed = datetime.now(timezone.utc).isoformat()
        names = ("가상 수납함 A", "가상 서랍 칸막이 B", "가상 정리 바구니 C")
        return [
            Product("mock", f"mock-{index:03}", f"[가상 테스트] {name}",
                    "생활·수납용품", f"https://example.invalid/mock/{index}",
                    observed, True)
            for index, name in enumerate(names, start=1)
        ]
