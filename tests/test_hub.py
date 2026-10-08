"""Behavior tests runnable with unittest or pytest; no external services."""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from affiliate_hub.config import Settings
from affiliate_hub.db import connect, initialize, upsert_products
from affiliate_hub.providers.mock import MockProductProvider
from affiliate_hub.runtime import exclusive_lock


class HubTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "한글 경로 with spaces"
        self.settings = Settings(self.home)
        self.settings.prepare()

    def cli(self, *args, expected=0):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "-m", "affiliate_hub.cli", "--home", str(self.home), *args],
            cwd=self.temp.name, env=env, capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stderr if expected else result.stdout)

    def database(self):
        connection = connect(self.settings.database)
        self.addCleanup(connection.close)
        return connection

    def test_collection_is_idempotent_and_jobs_are_durable(self):
        self.assertEqual(self.cli("collect")["inserted"], 3)
        repeated = self.cli("collect", "--provider", "mock")
        self.assertEqual((repeated["inserted"], repeated["updated"], repeated["total"]), (0, 3, 3))
        products = self.cli("products")["products"]
        self.assertEqual({p["source_id"] for p in products}, {"mock-001", "mock-002", "mock-003"})
        self.assertTrue(all(p["source"] == "mock" and p["is_mock"] for p in products))
        status = self.cli("status")
        self.assertIsNone(status["performance"])
        self.assertEqual(status["publishing"], "not_implemented")
        self.assertTrue(all(job["status"] == "succeeded" for job in status["job_runs"]))

    def test_upsert_updates_existing_product_and_preserves_identity(self):
        connection = self.database()
        initialize(connection)
        products = MockProductProvider().fetch()
        with connection:
            upsert_products(connection, products)
        before = dict(connection.execute("SELECT * FROM products WHERE source_id='mock-001'").fetchone())
        with connection:
            upsert_products(connection, [replace(products[0], name="[가상 테스트] 수정", observed_at="2030-01-01T00:00:00+00:00")])
        after = dict(connection.execute("SELECT * FROM products WHERE source_id='mock-001'").fetchone())
        self.assertEqual(after["id"], before["id"])
        self.assertEqual(after["created_at"], before["created_at"])
        self.assertEqual(after["name"], "[가상 테스트] 수정")
        self.assertEqual(after["observed_at"], "2030-01-01T00:00:00+00:00")

    def test_collection_rolls_back_partial_writes(self):
        connection = self.database()
        initialize(connection)
        products = MockProductProvider().fetch()
        with self.assertRaises(sqlite3.IntegrityError):
            with connection:
                upsert_products(connection, [products[0], replace(products[1], name=None)])
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM products").fetchone()[0], 0)

    def test_failure_returns_nonzero_and_records_safe_logs(self):
        result = self.cli("collect", "--simulate-failure", expected=1)
        self.assertEqual(result["error"], "RuntimeError")
        status = self.cli("status")
        self.assertEqual(status["products"], 0)
        self.assertEqual(status["job_runs"][0]["status"], "failed")
        events = [json.loads(line) for line in self.settings.log.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any(e.get("error_code") == "RuntimeError" and e["status"] == "failed" for e in events))

    def test_draft_export_is_not_publication_and_preserves_prior_file(self):
        self.cli("collect")
        draft = self.cli("draft", "--product-id", "1")
        self.assertEqual(draft["status"], "draft")
        first = self.cli("export", "--draft-id", str(draft["draft_id"]))
        first_path = Path(first["path"])
        text = first_path.read_text(encoding="utf-8")
        self.assertIn("테스트·게시 금지", text)
        self.assertIn("[미확인]", text)
        first_path.write_text(text + "\n사용자 메모", encoding="utf-8")
        second = self.cli("export", "--draft-id", str(draft["draft_id"]))
        self.assertNotEqual(first["path"], second["path"])
        self.assertIn("사용자 메모", first_path.read_text(encoding="utf-8"))
        self.assertFalse(second["published"])
        self.assertEqual(self.cli("drafts")["drafts"][0]["status"], "draft")

    def test_invalid_draft_and_product_do_not_create_artifacts(self):
        self.cli("draft", "--product-id", "999", expected=1)
        self.cli("export", "--draft-id", "999", expected=1)
        self.assertEqual(self.cli("drafts")["drafts"], [])
        self.assertEqual(list((self.home / "exports").iterdir()), [])

    def test_second_process_cannot_run_under_lock(self):
        with exclusive_lock(self.home / "data" / "runtime.lock"):
            self.assertEqual(self.cli("collect", expected=3)["error"], "BusyError")
        self.assertEqual(self.cli("collect")["total"], 3)

    def test_abandoned_job_is_reconciled_on_next_run(self):
        self.cli("init-db")
        connection = self.database()
        with connection:
            connection.execute("INSERT INTO job_runs(command,status,started_at) VALUES('collect','running','2020-01-01')")
        status = self.cli("status")
        self.assertEqual(status["job_runs"][0]["status"], "interrupted")
        self.assertEqual(status["job_runs"][0]["error_code"], "Interrupted")

    def test_future_schema_is_rejected_without_downgrade(self):
        connection = self.database()
        connection.execute("PRAGMA user_version = 999")
        self.cli("init-db", expected=1)
        self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 999)

    def test_relative_home_is_rejected(self):
        with self.assertRaises(ValueError):
            Settings.load("relative-path")


if __name__ == "__main__":
    unittest.main()
