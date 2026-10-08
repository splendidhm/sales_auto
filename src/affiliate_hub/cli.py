"""Single offline CLI entry point."""

import argparse
import json
import sqlite3
import sys
from contextlib import closing

from affiliate_hub.config import Settings
from affiliate_hub.content import create_draft
from affiliate_hub.db import connect, initialize, now, upsert_products
from affiliate_hub.providers.base import ProductProvider
from affiliate_hub.providers.mock import MockProductProvider
from affiliate_hub.runtime import BusyError, exclusive_lock, log_event
from affiliate_hub.publishing import export_draft


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="오프라인 제휴 콘텐츠 연습 도구 (실제 게시 없음)")
    result.add_argument("--home", help="데이터·로그·내보내기 폴더의 절대 경로")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("init-db")
    collect = commands.add_parser("collect")
    collect.add_argument("--provider", choices=["mock"], default="mock")
    collect.add_argument("--simulate-failure", action="store_true", help="실패 기록 검증용")
    commands.add_parser("products")
    commands.add_parser("status")
    draft = commands.add_parser("draft")
    draft.add_argument("--product-id", type=int, required=True)
    commands.add_parser("drafts")
    export = commands.add_parser("export")
    export.add_argument("--draft-id", type=int, required=True)
    return result


def dispatch(args: argparse.Namespace, settings: Settings, connection: sqlite3.Connection) -> dict:
    if args.command == "init-db":
        return {"schema_version": 2, "database": str(settings.database)}
    if args.command == "collect":
        if args.simulate_failure:
            raise RuntimeError("Simulated failure")
        provider: ProductProvider = MockProductProvider()
        return {"provider": "mock", "fictional": True, **upsert_products(connection, provider.fetch())}
    if args.command == "products":
        return {"products": [dict(row) for row in connection.execute("SELECT * FROM products ORDER BY id")]}
    if args.command == "status":
        return {
            "products": connection.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "drafts": connection.execute("SELECT COUNT(*) FROM content_drafts").fetchone()[0],
            "exports": connection.execute("SELECT COUNT(*) FROM exports").fetchone()[0],
            "publishing": "not_implemented", "performance": None,
            "manual_publications": connection.execute("SELECT COUNT(*) FROM publication_records").fetchone()[0],
            "job_runs": [dict(row) for row in connection.execute(
                "SELECT * FROM job_runs WHERE command != 'status' ORDER BY id DESC LIMIT 20")],
        }
    if args.command == "draft":
        return create_draft(connection, args.product_id)
    if args.command == "drafts":
        return {"drafts": [dict(row) for row in connection.execute(
            """SELECT d.id,d.product_id,COALESCE(r.title,d.title) AS title,
            COALESCE(e.status,d.status) AS status,e.revision,d.template_version,d.created_at
            FROM content_drafts d LEFT JOIN editorial_state e ON e.draft_id=d.id
            LEFT JOIN draft_revisions r ON r.draft_id=d.id AND r.revision=e.revision ORDER BY d.id""")]}
    if args.command == "export":
        return export_draft(connection, settings, args.draft_id)
    raise ValueError("Unknown command")


def emit(result: dict, *, error: bool = False) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr if error else sys.stdout)


def execute(args: argparse.Namespace, settings: Settings) -> int:
    with exclusive_lock(settings.home / "data" / "runtime.lock"):
        with closing(connect(settings.database)) as connection:
            initialize(connection)
            # The OS lock guarantees these rows belong to commands no longer running.
            with connection:
                connection.execute("UPDATE job_runs SET status='interrupted',finished_at=?,error_code='Interrupted' WHERE status='running'", (now(),))
                cursor = connection.execute("INSERT INTO job_runs(command,status,started_at) VALUES(?,'running',?)",
                                            (args.command, now()))
                job_id = cursor.lastrowid
            try:
                log_event(settings.log, job_id=job_id, command=args.command, status="running")
                with connection:
                    result = dispatch(args, settings, connection)
                    connection.execute("UPDATE job_runs SET status='succeeded',finished_at=?,summary=? WHERE id=?",
                                       (now(), json.dumps({"command": args.command}), job_id))
            except Exception as exc:
                code = type(exc).__name__
                with connection:
                    connection.execute("UPDATE job_runs SET status='failed',finished_at=?,error_code=? WHERE id=?",
                                       (now(), code, job_id))
                log_event(settings.log, job_id=job_id, command=args.command, status="failed", error_code=code)
                # Raw exceptions can contain credentials; only record safe error types.
                emit({"error": code, "job_id": job_id, "message": "작업 실패. 입력 ID·파일 접근 권한과 status를 확인하세요."}, error=True)
                return 1
            log_event(settings.log, job_id=job_id, command=args.command, status="succeeded")
            emit(result)
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    try:
        settings = Settings.load(args.home)
        settings.prepare()
        return execute(args, settings)
    except BusyError:
        emit({"error": "BusyError", "message": "다른 작업이 실행 중입니다. 완료 후 다시 실행하세요."}, error=True)
        return 3
    except Exception as exc:
        emit({"error": type(exc).__name__, "message": "초기화 또는 파일 처리 실패. 실행 경로·접근 권한을 확인하세요."}, error=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
