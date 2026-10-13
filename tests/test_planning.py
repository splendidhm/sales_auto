import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from affiliate_hub.config import Settings
from affiliate_hub.db import now
from affiliate_hub.editorial import CHECKS, ValidationError
from affiliate_hub.service import Hub


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.hub = Hub(Settings(Path(self.temp.name)))

    def blog(self, status="information"):
        return self.hub.mutate("blog_settings", blog_name="쇼핑 테스트", blog_url="https://blog.naver.com/shoptest",
                               topic="생활가전·수납", publish_days=["월", "수", "금"], enrollment_status=status)

    def monday(self):
        today = date.today()
        return today + timedelta(days=(7 - today.weekday()) % 7)

    def product(self, affiliate=False):
        values = dict(name="로봇청소기 후보", category="생활가전·로봇청소기",
                      source_url="https://example.com/robot", observed_at=now(),
                      facts="공식 자료에서 확인한 모델명", image_rights="none")
        if affiliate:
            values.update(provider="shopping_connect", affiliate_url="https://example.com/official-link", link_confirmed=True)
        return self.hub.mutate("product", **values)["product_id"]

    def plan(self, affiliate=False, offset=0, keyword="로봇청소기"):
        return self.hub.mutate("content_plan", scheduled_date=(self.monday() + timedelta(days=offset)).isoformat(),
                               content_type="comparison" if affiliate else "information", keyword=keyword,
                               title_seed=f"{keyword} 구매 전 체크리스트", affiliate_enabled=affiliate)["plan_id"]

    def finish(self, draft_id, disclosure=""):
        self.hub.mutate("save", draft_id=draft_id, expected_revision=1, title="검증된 선택 가이드",
                        body="공식 자료에서 확인한 모델명을 기준으로 구매 전 공간을 확인합니다.", disclosure=disclosure)
        self.hub.mutate("review", draft_id=draft_id, expected_revision=2, reviewer="검토자", checks=dict.fromkeys(CHECKS, True))
        self.hub.mutate("approve", draft_id=draft_id, expected_revision=2, reviewer="승인자")

    def test_seed_creates_twelve_template_plans_idempotently(self):
        self.blog()
        result = self.hub.mutate("seed_calendar", start_date=self.monday().isoformat())
        repeated = self.hub.mutate("seed_calendar", start_date=self.monday().isoformat())
        snapshot = self.hub.snapshot()
        self.assertEqual((result["inserted"], repeated["inserted"], len(snapshot["plans"])), (12, 0, 12))
        self.assertEqual([p["scheduled_date"] for p in snapshot["plans"][:3]],
                         [(self.monday() + timedelta(days=n)).isoformat() for n in (0, 2, 4)])
        self.assertTrue(all(p["title_candidates"] and p["fact_checklist"] and p["image_checklist"] and p["tags"] for p in snapshot["plans"]))

    def test_schedule_collision_and_wrong_weekday_are_blocked(self):
        self.blog()
        self.plan()
        with self.assertRaises(ValidationError):
            self.plan(keyword="중복 일정")
        with self.assertRaises(ValidationError):
            self.plan(offset=1, keyword="화요일")

    def test_duplicate_keyword_warning(self):
        self.blog()
        self.plan()
        self.plan(offset=2)
        warnings = self.hub.snapshot()["duplicate_warnings"]
        self.assertTrue(any(item["kind"] == "duplicate" for item in warnings))

    def test_information_plan_omits_existing_affiliate_link(self):
        self.blog()
        product_id = self.product(affiliate=True)
        plan_id = self.plan(affiliate=False)
        draft_id = self.hub.mutate("start", product_id=product_id, plan_id=plan_id)["draft_id"]
        self.finish(draft_id, disclosure="표시되면 안 되는 문구")
        result = self.hub.mutate("export", draft_id=draft_id)
        package = Path(result["path"]).read_text(encoding="utf-8")
        self.assertNotIn("official-link", package)
        self.assertNotIn("표시되면 안 되는 문구", package)
        self.assertIn("이미지 체크리스트", package)
        self.assertEqual(self.hub.snapshot()["plans"][0]["stage"], "packaged")
        self.hub.mutate("record", draft_id=draft_id, expected_revision=2,
                        url="https://blog.naver.com/shoptest/100", confirmed=True)
        snapshot = self.hub.snapshot()
        self.assertEqual(snapshot["plans"][0]["stage"], "published")
        self.assertEqual(snapshot["metrics"]["published"], 1)

    def test_affiliate_plan_requires_ready_channel_and_official_link(self):
        self.blog()
        with self.assertRaises(ValidationError):
            self.plan(affiliate=True)
        self.blog("shopping_connect_ready")
        plan_id = self.plan(affiliate=True)
        without_link = self.product()
        with self.assertRaises(ValidationError):
            self.hub.mutate("start", product_id=without_link, plan_id=plan_id)
        with_link = self.product(affiliate=True)
        draft_id = self.hub.mutate("start", product_id=with_link, plan_id=plan_id)["draft_id"]
        self.finish(draft_id, disclosure="제휴 활동 고지")
        package = Path(self.hub.mutate("export", draft_id=draft_id)["path"]).read_text(encoding="utf-8")
        self.assertTrue(package.startswith("제휴 활동 고지"))
        self.assertIn("official-link", package)


if __name__ == "__main__":
    unittest.main()
