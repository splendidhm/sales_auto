import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing

from affiliate_hub.config import Settings
from affiliate_hub.db import connect, initialize, now
from affiliate_hub.editorial import CHECKS, ValidationError, naver_post_url
from affiliate_hub.service import Hub


class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings = Settings(Path(self.temp.name))
        self.hub = Hub(self.settings)

    def product(self, **overrides):
        values = dict(name="테스트 수납함", source_url="https://example.com/item", observed_at=now(),
                      facts="시험용 자료: 가로 20cm", image_rights="none")
        values.update(overrides)
        return self.hub.mutate("product", **values)

    def draft(self, affiliate=False):
        product = self.product(**(dict(provider="shopping_connect", affiliate_url="https://example.com/affiliate?a=1&b=2", link_confirmed=True) if affiliate else {}))
        draft = self.hub.mutate("start", product_id=product["product_id"])
        self.hub.mutate("save", draft_id=draft["draft_id"], expected_revision=1, title="선택 가이드",
                        body="출처에 기재된 가로 길이는 20cm입니다. 공간을 먼저 측정하세요.",
                        disclosure="테스트용 제휴 고지" if affiliate else "")
        return product["product_id"], draft["draft_id"]

    def approve(self, draft_id, revision=2):
        self.hub.mutate("review", draft_id=draft_id, expected_revision=revision, reviewer="검토자",
                        checks=dict.fromkeys(CHECKS, True))
        self.hub.mutate("approve", draft_id=draft_id, expected_revision=revision, reviewer="검토자")

    def test_complete_informational_flow_and_idempotent_manual_record(self):
        _, draft = self.draft()
        self.approve(draft)
        with self.assertRaises(ValidationError):
            self.hub.mutate("record", draft_id=draft, expected_revision=2, url="https://blog.naver.com/tester/123", confirmed=True)
        result = self.hub.mutate("export", draft_id=draft)
        self.assertFalse(result["published"])
        self.assertEqual(self.hub.snapshot()["publications"], [])
        for url in ("https://m.blog.naver.com/tester/123?x=1", "https://blog.naver.com/PostView.naver?blogId=tester&logNo=123"):
            result = self.hub.mutate("record", draft_id=draft, expected_revision=2, url=url, confirmed=True)
            self.assertFalse(result["verified_online"])
        self.assertEqual(len(self.hub.snapshot()["publications"]), 1)
        self.assertEqual(self.hub.snapshot()["drafts"][0]["status"], "published")

    def test_affiliate_export_contains_disclosure_first_and_original_link(self):
        _, draft = self.draft(affiliate=True)
        self.approve(draft)
        result = self.hub.mutate("export", draft_id=draft)
        content = Path(result["path"]).read_text(encoding="utf-8")
        self.assertTrue(content.startswith("테스트용 제휴 고지"))
        self.assertIn("https://example.com/affiliate?a=1&b=2", content)

    def test_unreviewed_export_and_approval_rejected(self):
        _, draft = self.draft()
        for action, values in (("export", {}), ("approve", dict(expected_revision=2, reviewer="검토자"))):
            with self.assertRaises(ValidationError):
                self.hub.mutate(action, draft_id=draft, **values)
        self.assertEqual(list((self.settings.home / "exports").iterdir()), [])

    def test_edit_invalidates_approval_and_preserves_history(self):
        _, draft = self.draft()
        self.approve(draft)
        self.hub.mutate("save", draft_id=draft, expected_revision=2, title="수정 제목", body="수정한 본문", disclosure="")
        with self.assertRaises(ValidationError):
            self.hub.mutate("export", draft_id=draft)
        snapshot = self.hub.snapshot()
        self.assertEqual(snapshot["drafts"][0]["status"], "needs_recheck")
        self.assertEqual(len(snapshot["revisions"]), 3)
        self.assertEqual(len(snapshot["reviews"]), 2)

    def test_product_link_change_requires_resave_and_new_review(self):
        product, draft = self.draft()
        self.approve(draft)
        self.product(product_id=product, expected_version=1, provider="shopping_connect",
                     affiliate_url="https://example.com/new", link_confirmed=True)
        with self.assertRaises(ValidationError):
            self.hub.mutate("export", draft_id=draft)
        with self.assertRaises(ValidationError):
            self.approve(draft)
        self.hub.mutate("save", draft_id=draft, expected_revision=2, title="새 링크 확인", body="확인된 원고", disclosure="고지")
        self.approve(draft, 3)
        self.assertEqual(self.hub.snapshot()["drafts"][0]["status"], "approved")

    def test_placeholder_missing_checks_rights_and_disclosure_block_review(self):
        product = self.product(image_rights="unknown", provider="shopping_connect", affiliate_url="https://example.com/ref", link_confirmed=True)
        draft = self.hub.mutate("start", product_id=product["product_id"])["draft_id"]
        with self.assertRaises(ValidationError):
            self.approve(draft, 1)
        self.product(product_id=product["product_id"], expected_version=1, provider="shopping_connect", affiliate_url="https://example.com/ref", link_confirmed=True)
        self.hub.mutate("save", draft_id=draft, expected_revision=1, title="제목", body="작성 완료", disclosure="")
        with self.assertRaises(ValidationError):
            self.approve(draft)
        self.hub.mutate("save", draft_id=draft, expected_revision=2, title="제목", body="작성 완료", disclosure="고지")
        with self.assertRaises(ValidationError):
            self.hub.mutate("review", draft_id=draft, expected_revision=3, reviewer="검토자", checks={})
        self.approve(draft, 3)

    def test_stale_editor_and_invalid_inputs_are_rejected_without_partial_save(self):
        product, draft = self.draft()
        with self.assertRaises(ValidationError):
            self.hub.mutate("save", draft_id=draft, expected_revision=1, title="오래된 창", body="본문", disclosure="")
        for overrides in (dict(source_url="javascript:alert(1)"), dict(observed_at="2999-01-01T00:00:00+00:00"),
                          dict(affiliate_url="https://example.com/ref", link_confirmed=False), dict(image_rights="licensed")):
            with self.assertRaises(ValidationError):
                self.product(**overrides)
        with self.assertRaises(ValidationError):
            self.product(product_id=product, expected_version=0)
        self.assertEqual(len(self.hub.snapshot()["products"]), 1)

    def test_publication_urls_require_exact_naver_post(self):
        for url in ("https://blog.naver.com.evil.example/test/123", "https://blog.naver.com/test", "http://blog.naver.com/test/123"):
            with self.assertRaises(ValidationError):
                naver_post_url(url)

    def test_robot_category_can_be_selected_and_survives_old_client_update(self):
        product = self.product(category="생활가전·로봇청소기")
        self.product(product_id=product["product_id"], expected_version=1)
        self.assertEqual(self.hub.snapshot()["products"][0]["category"], "생활가전·로봇청소기")

    def test_invalid_url_ports_and_brackets_return_validation_errors(self):
        for url in ("https://example.com:bad/item", "https://example.com:99999/item", "https://[invalid/item"):
            with self.subTest(url=url), self.assertRaises(ValidationError):
                self.product(source_url=url)
        self.assertEqual(self.hub.snapshot()["products"], [])

    def test_v1_migration_preserves_rows_and_is_repeatable(self):
        # A standalone fixture of the original v1 schema, independent of new migrations.
        with closing(sqlite3.connect(self.settings.database)) as connection:
            connection.executescript("""
                CREATE TABLE products(id INTEGER PRIMARY KEY,source TEXT,source_id TEXT,name TEXT,category TEXT,
                    source_url TEXT,observed_at TEXT,is_mock INTEGER,created_at TEXT,updated_at TEXT,UNIQUE(source,source_id));
                CREATE TABLE job_runs(id INTEGER PRIMARY KEY,command TEXT,status TEXT,started_at TEXT,finished_at TEXT,error_code TEXT,summary TEXT);
                CREATE TABLE content_drafts(id INTEGER PRIMARY KEY,product_id INTEGER REFERENCES products(id),title TEXT,body TEXT,
                    status TEXT DEFAULT 'draft' CHECK(status='draft'),template_version TEXT,created_at TEXT);
                CREATE TABLE exports(id INTEGER PRIMARY KEY,draft_id INTEGER REFERENCES content_drafts(id),relative_path TEXT,created_at TEXT);
                INSERT INTO products VALUES(1,'mock','mock-001','가상','수납','https://example.invalid','old',1,'old','old');
                INSERT INTO content_drafts VALUES(1,1,'기존 제목','기존 본문','draft','offline-v1','old');
                INSERT INTO exports VALUES(1,1,'exports/existing.md','old');
                INSERT INTO job_runs VALUES(1,'collect','succeeded','old','old',NULL,NULL);
                PRAGMA user_version=1;
            """)
        original = self.settings.home / "exports" / "existing.md"
        original.write_text("기존 사용자 메모", encoding="utf-8")
        connection = connect(self.settings.database)
        self.addCleanup(connection.close)
        initialize(connection)
        initialize(connection)
        self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 3)
        self.assertEqual(connection.execute("SELECT body FROM content_drafts WHERE id=1").fetchone()[0], "기존 본문")
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM exports").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM job_runs").fetchone()[0], 1)
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(original.read_text(encoding="utf-8"), "기존 사용자 메모")
        backups = list(self.settings.database.parent.glob("pre-v2-*.sqlite3"))
        self.assertEqual(len(backups), 1)
        with closing(sqlite3.connect(backups[0])) as backup:
            self.assertEqual(backup.execute("PRAGMA user_version").fetchone()[0], 1)
        v3_backups = list(self.settings.database.parent.glob("pre-v3-*.sqlite3"))
        self.assertEqual(len(v3_backups), 1)


if __name__ == "__main__":
    unittest.main()
