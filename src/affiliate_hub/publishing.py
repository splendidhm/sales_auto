"""Prepare local files only; no channel login, network or posting."""

import sqlite3
from pathlib import Path
from uuid import uuid4

from affiliate_hub.config import Settings
from affiliate_hub.db import now
from affiliate_hub.editorial import approved_text, require


def export_draft(connection: sqlite3.Connection, settings: Settings, draft_id: int) -> dict:
    row = connection.execute("""SELECT d.*,p.is_mock FROM content_drafts d
        JOIN products p ON p.id=d.product_id WHERE d.id=?""", (draft_id,)).fetchone()
    require(row is not None, "원고를 찾을 수 없습니다.")
    if row["is_mock"]:
        body, revision, status, suffix = row["body"], None, "draft", ".md"
    else:
        draft, body = approved_text(connection, draft_id)
        revision, status, suffix = draft["revision"], draft["status"], ".txt"
    relative = Path("exports") / f"draft-{draft_id}-{uuid4().hex}{suffix}"
    with (settings.home / relative).open("x", encoding="utf-8") as handle:
        handle.write(body)
    connection.execute("INSERT INTO exports(draft_id,relative_path,created_at,revision) VALUES(?,?,?,?)",
                       (draft_id, str(relative), now(), revision))
    if not row["is_mock"]:
        from affiliate_hub.planning import sync_plan_stage
        sync_plan_stage(connection, draft_id, "packaged")
    return {"path": str(settings.home / relative), "draft_status": status,
            "revision": revision, "published": False}
