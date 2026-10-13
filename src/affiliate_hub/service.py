"""Short-lived DB access shared by the local UI and automation tests."""

from contextlib import closing, contextmanager
from datetime import datetime

from affiliate_hub.config import Settings
from affiliate_hub.db import connect, initialize, now
from affiliate_hub.editorial import (save_product, start_draft, save_draft, review,
                                    approve, record_publication, get_product, get_draft)
from affiliate_hub.publishing import export_draft
from affiliate_hub.planning import (save_blog_settings, save_content_plan,
                                    seed_initial_calendar, duplicate_warnings, get_plan, mark_research)
from affiliate_hub.runtime import exclusive_lock, log_event


class Hub:
    def __init__(self, settings: Settings):
        self.settings = settings
        settings.prepare()

    @contextmanager
    def session(self):
        with exclusive_lock(self.settings.home / "data" / "runtime.lock"):
            with closing(connect(self.settings.database)) as connection:
                initialize(connection)
                yield connection

    def snapshot(self) -> dict:
        with self.session() as connection:
            products = [get_product(connection, row[0]) for row in connection.execute("SELECT id FROM products ORDER BY id DESC").fetchall()]
            drafts = [get_draft(connection, row[0]) for row in connection.execute("SELECT draft_id FROM editorial_state ORDER BY draft_id DESC").fetchall()]
            blog_row = connection.execute("SELECT * FROM blog_settings WHERE id=1").fetchone()
            plans = [get_plan(connection, row[0]) for row in connection.execute("SELECT id FROM content_plans ORDER BY scheduled_date,id").fetchall()]
            reviews = [dict(r) for r in connection.execute("SELECT * FROM review_events ORDER BY id DESC")]
            durations = []
            grouped = {}
            for event in reviews:
                grouped.setdefault((event["draft_id"], event["revision"]), {})[event["action"]] = event["created_at"]
            for events in grouped.values():
                if "reviewed" in events and "approved" in events:
                    durations.append((datetime.fromisoformat(events["approved"]) - datetime.fromisoformat(events["reviewed"])).total_seconds() / 60)
            metrics = {"prepared": sum(p["stage"] != "planned" for p in plans),
                       "approved": sum(p["stage"] in ("approved", "packaged", "published") for p in plans),
                       "published": sum(p["stage"] == "published" for p in plans),
                       "average_review_minutes": round(sum(durations) / len(durations), 1) if durations else None}
            return {"products": products, "drafts": drafts, "blog": dict(blog_row) if blog_row else None,
                    "plans": plans, "duplicate_warnings": duplicate_warnings(connection),
                    "metrics": metrics,
                    "publications": [dict(r) for r in connection.execute("SELECT * FROM publication_records ORDER BY id DESC")],
                    "exports": [dict(r) for r in connection.execute("SELECT * FROM exports ORDER BY id DESC")],
                    "reviews": reviews,
                    "revisions": [dict(r) for r in connection.execute("SELECT * FROM draft_revisions ORDER BY draft_id DESC,revision DESC")]}

    def mutate(self, action: str, **values) -> dict:
        operations = {"product": save_product, "start": start_draft, "save": save_draft,
                      "review": review, "approve": approve, "record": record_publication,
                      "blog_settings": save_blog_settings, "content_plan": save_content_plan,
                      "seed_calendar": seed_initial_calendar, "research": mark_research}
        if action not in (*operations, "export"):
            raise ValueError("Unknown operation")
        with self.session() as connection:
            with connection:
                connection.execute("UPDATE job_runs SET status='interrupted',finished_at=?,error_code='Interrupted' WHERE status='running'", (now(),))
                job = connection.execute("INSERT INTO job_runs(command,status,started_at) VALUES(?,'running',?)",
                                         (f"editorial:{action}", now())).lastrowid
            try:
                log_event(self.settings.log, job_id=job, command=action, status="running")
                with connection:
                    result = (export_draft(connection, self.settings, **values) if action == "export"
                              else operations[action](connection, **values))
                    connection.execute("UPDATE job_runs SET status='succeeded',finished_at=? WHERE id=?", (now(), job))
            except Exception as exc:
                with connection:
                    connection.execute("UPDATE job_runs SET status='failed',finished_at=?,error_code=? WHERE id=?",
                                       (now(), type(exc).__name__, job))
                log_event(self.settings.log, job_id=job, command=action, status="failed", error_code=type(exc).__name__)
                raise
            log_event(self.settings.log, job_id=job, command=action, status="succeeded")
            return result
