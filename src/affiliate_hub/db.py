"""SQLite persistence with an additive, backed-up v1 to v2 migration."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from affiliate_hub.models import Product


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version not in (0, 1, 2):
        raise ValueError("Unsupported database schema")
    if version == 2:
        return
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            source_url TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            is_mock INTEGER NOT NULL CHECK (is_mock IN (0,1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(source, source_id)
        );
        CREATE TABLE IF NOT EXISTS job_runs (
            id INTEGER PRIMARY KEY,
            command TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('running','succeeded','failed','interrupted')),
            started_at TEXT NOT NULL,
            finished_at TEXT,
            error_code TEXT,
            summary TEXT
        );
        CREATE TABLE IF NOT EXISTS content_drafts (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id),
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft' CHECK(status = 'draft'),
            template_version TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS exports (
            id INTEGER PRIMARY KEY,
            draft_id INTEGER NOT NULL REFERENCES content_drafts(id),
            relative_path TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        PRAGMA user_version = 1;
    """)
    from affiliate_hub.migrations import migrate_v2
    migrate_v2(connection)


def upsert_products(connection: sqlite3.Connection, products: list[Product]) -> dict[str, int]:
    inserted = 0
    updated = 0
    stamp = now()
    for product in products:
        exists = connection.execute(
            "SELECT id FROM products WHERE source=? AND source_id=?",
            (product.source, product.source_id),
        ).fetchone()
        connection.execute("""
            INSERT INTO products
            (source,source_id,name,category,source_url,observed_at,is_mock,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source,source_id) DO UPDATE SET
                name=excluded.name, category=excluded.category,
                source_url=excluded.source_url, observed_at=excluded.observed_at,
                is_mock=excluded.is_mock, updated_at=excluded.updated_at
        """, (product.source, product.source_id, product.name, product.category,
              product.source_url, product.observed_at, int(product.is_mock), stamp, stamp))
        inserted += int(exists is None)
        updated += int(exists is not None)
    total = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    return {"inserted": inserted, "updated": updated, "total": total}
