"""Additive migration: retain all v1 rows, foreign keys and exported files."""

import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4


def migrate_v2(connection: sqlite3.Connection) -> None:
    database = connection.execute("PRAGMA database_list").fetchone()[2]
    if database:
        original = Path(database)
        backup = original.parent / f"pre-v2-{uuid4().hex}.sqlite3"
        with closing(sqlite3.connect(backup)) as target:
            connection.backup(target)
    try:
        connection.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE affiliate_links (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id),
                provider TEXT NOT NULL CHECK(provider IN ('shopping_connect','coupang')),
                url TEXT NOT NULL,
                confirmed_at TEXT NOT NULL
            );
            CREATE TABLE product_profiles (
                product_id INTEGER PRIMARY KEY REFERENCES products(id),
                version INTEGER NOT NULL,
                facts TEXT NOT NULL,
                image_rights TEXT NOT NULL CHECK(image_rights IN ('none','owned','licensed','unknown')),
                image_notes TEXT NOT NULL,
                experience TEXT NOT NULL,
                link_id INTEGER REFERENCES affiliate_links(id)
            );
            CREATE TABLE editorial_state (
                draft_id INTEGER PRIMARY KEY REFERENCES content_drafts(id),
                revision INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('draft','reviewed','approved','needs_recheck','published')),
                approved_revision INTEGER
            );
            CREATE TABLE draft_revisions (
                draft_id INTEGER NOT NULL REFERENCES content_drafts(id),
                revision INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                disclosure TEXT NOT NULL,
                product_version INTEGER NOT NULL,
                source_snapshot TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(draft_id,revision)
            );
            CREATE TABLE review_events (
                id INTEGER PRIMARY KEY,
                draft_id INTEGER NOT NULL REFERENCES content_drafts(id),
                revision INTEGER NOT NULL,
                action TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                checks TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE publication_records (
                id INTEGER PRIMARY KEY,
                draft_id INTEGER NOT NULL REFERENCES content_drafts(id),
                revision INTEGER NOT NULL,
                url TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                UNIQUE(draft_id,revision)
            );
            ALTER TABLE exports ADD COLUMN revision INTEGER;
            PRAGMA user_version = 2;
            COMMIT;
        """)
    except Exception:
        connection.rollback()
        raise


def migrate_v3(connection: sqlite3.Connection) -> None:
    """Add blog/channel planning without rewriting any v2 editorial rows."""
    database = connection.execute("PRAGMA database_list").fetchone()[2]
    if database:
        original = Path(database)
        backup = original.parent / f"pre-v3-{uuid4().hex}.sqlite3"
        with closing(sqlite3.connect(backup)) as target:
            connection.backup(target)
    try:
        connection.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE blog_settings (
                id INTEGER PRIMARY KEY CHECK(id=1),
                blog_name TEXT NOT NULL,
                blog_url TEXT NOT NULL,
                topic TEXT NOT NULL,
                publish_days TEXT NOT NULL,
                enrollment_status TEXT NOT NULL CHECK(enrollment_status IN
                    ('information','brand_connected','shopping_connect_ready')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE content_plans (
                id INTEGER PRIMARY KEY,
                blog_id INTEGER NOT NULL DEFAULT 1 REFERENCES blog_settings(id),
                scheduled_date TEXT NOT NULL,
                content_type TEXT NOT NULL CHECK(content_type IN ('information','comparison')),
                keyword TEXT NOT NULL,
                title_seed TEXT NOT NULL,
                title_candidates TEXT NOT NULL,
                template_outline TEXT NOT NULL,
                fact_checklist TEXT NOT NULL,
                image_checklist TEXT NOT NULL,
                tags TEXT NOT NULL,
                affiliate_enabled INTEGER NOT NULL DEFAULT 0 CHECK(affiliate_enabled IN (0,1)),
                stage TEXT NOT NULL CHECK(stage IN
                    ('planned','research','draft','reviewed','approved','packaged','published')),
                draft_id INTEGER UNIQUE REFERENCES content_drafts(id),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(blog_id, scheduled_date)
            );
            CREATE INDEX content_plans_week ON content_plans(scheduled_date,stage);
            PRAGMA user_version = 3;
            COMMIT;
        """)
    except Exception:
        connection.rollback()
        raise
