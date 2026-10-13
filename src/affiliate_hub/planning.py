"""Deterministic blog calendar and templates; no network or generated claims."""

import json
import re
import sqlite3
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit

from affiliate_hub.db import now
from affiliate_hub.editorial import ValidationError, require, web_url


ENROLLMENT = ("information", "brand_connected", "shopping_connect_ready")
CONTENT_TYPES = ("information", "comparison")
INITIAL_TOPICS = (
    ("information", "로봇청소기 구매 체크리스트", "로봇청소기 구매 전 체크리스트"),
    ("information", "충전 스테이션 설치 공간", "로봇청소기 충전 스테이션 설치 공간 확인법"),
    ("comparison", "로봇청소기 후보 선택", "우리 집에 맞는 로봇청소기 후보 선택 가이드"),
    ("information", "문턱 카펫 가구 높이", "문턱·카펫·가구 높이 확인법"),
    ("information", "로봇청소기 소모품 관리", "필터와 브러시 등 소모품 관리 체크리스트"),
    ("comparison", "수납 공간별 정리용품", "수납 공간별 정리용품 선택 가이드"),
    ("information", "청소가전 관리 부담", "청소가전 관리 부담을 비교하는 기준"),
    ("information", "반려동물 머리카락 청소", "반려동물·머리카락 환경의 청소가전 체크사항"),
    ("comparison", "로봇청소기 상품 비교", "확인된 정보로 만드는 로봇청소기 상품 비교표"),
    ("information", "작은 집 청소 동선", "작은 집에서 먼저 확인할 청소 동선"),
    ("information", "필터 브러시 교체", "필터·브러시 교체 시기 확인법"),
    ("comparison", "생활가전 수납 종합 선택", "한 달 콘텐츠 종합 선택 가이드"),
)


def _json(items) -> str:
    return json.dumps(list(items), ensure_ascii=False)


def save_blog_settings(connection: sqlite3.Connection, *, blog_name: str, blog_url: str,
                       topic: str, publish_days: list[str], enrollment_status: str) -> dict:
    require(bool(blog_name.strip()) and bool(topic.strip()), "블로그명과 주제를 입력하세요.")
    parsed_url = web_url(blog_url)
    parsed = urlsplit(parsed_url)
    require(parsed.hostname in ("blog.naver.com", "m.blog.naver.com") and bool(parsed.path.strip("/")),
            "개별 네이버 블로그 URL을 입력하세요.")
    require(enrollment_status in ENROLLMENT, "채널 운영 단계를 선택하세요.")
    days = list(dict.fromkeys(publish_days))
    require(days == ["월", "수", "금"], "현재 운영 일정은 월·수·금 주 3회입니다.")
    stamp = now()
    connection.execute("""INSERT INTO blog_settings
        (id,blog_name,blog_url,topic,publish_days,enrollment_status,created_at,updated_at)
        VALUES(1,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
        blog_name=excluded.blog_name,blog_url=excluded.blog_url,topic=excluded.topic,
        publish_days=excluded.publish_days,enrollment_status=excluded.enrollment_status,
        updated_at=excluded.updated_at""",
        (blog_name.strip(), parsed_url, topic.strip(), _json(days), enrollment_status, stamp, stamp))
    return {"saved": True}


def _template(title: str, keyword: str, content_type: str) -> dict:
    kind = "비교·선택" if content_type == "comparison" else "구매 전 정보"
    return {
        "title_candidates": [title, f"{keyword}: 구매 전에 확인할 기준", f"{keyword} 체크리스트"],
        "outline": ["독자가 해결하려는 문제", "출처에서 확인한 정보", f"{kind} 기준", "한계와 추가 확인사항"],
        "facts": ["공식 출처와 확인 날짜", "치수·호환성 등 선택에 필요한 수치", "가격·재고처럼 변하는 정보의 게시 직전 확인"],
        "images": ["직접 촬영 또는 사용 허락 여부", "이미지별 출처와 파일 위치", "권한이 불명확하면 사용하지 않기"],
        "tags": list(dict.fromkeys([keyword.replace(" ", ""), "생활가전", "수납", "구매가이드"]))[:5],
    }


def save_content_plan(connection: sqlite3.Connection, *, scheduled_date: str, content_type: str,
                      keyword: str, title_seed: str, affiliate_enabled: bool = False) -> dict:
    require(connection.execute("SELECT 1 FROM blog_settings WHERE id=1").fetchone() is not None,
            "블로그 설정을 먼저 저장하세요.")
    try:
        day = date.fromisoformat(scheduled_date)
    except ValueError:
        raise ValidationError("예정일은 YYYY-MM-DD 형식으로 입력하세요.") from None
    require(content_type in CONTENT_TYPES, "콘텐츠 유형을 선택하세요.")
    require(bool(keyword.strip()) and bool(title_seed.strip()), "핵심 키워드와 제목을 입력하세요.")
    require(day.weekday() in (0, 2, 4), "발행 예정일은 월·수·금 중 하나여야 합니다.")
    if affiliate_enabled:
        status = connection.execute("SELECT enrollment_status FROM blog_settings WHERE id=1").fetchone()[0]
        require(status == "shopping_connect_ready", "쇼핑커넥트 이용 가능 상태에서만 제휴 계획을 만들 수 있습니다.")
    require(connection.execute("SELECT 1 FROM content_plans WHERE blog_id=1 AND scheduled_date=?", (scheduled_date,)).fetchone() is None,
            "같은 날짜에 이미 예정된 글이 있습니다.")
    template = _template(title_seed.strip(), keyword.strip(), content_type)
    stamp = now()
    cursor = connection.execute("""INSERT INTO content_plans
        (blog_id,scheduled_date,content_type,keyword,title_seed,title_candidates,template_outline,
         fact_checklist,image_checklist,tags,affiliate_enabled,stage,created_at,updated_at)
        VALUES(1,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (scheduled_date, content_type, keyword.strip(), title_seed.strip(),
         _json(template["title_candidates"]), _json(template["outline"]), _json(template["facts"]),
         _json(template["images"]), _json(template["tags"]), int(affiliate_enabled), "planned", stamp, stamp))
    return {"plan_id": cursor.lastrowid, "stage": "planned"}


def seed_initial_calendar(connection: sqlite3.Connection, *, start_date: str | None = None) -> dict:
    require(connection.execute("SELECT 1 FROM blog_settings WHERE id=1").fetchone() is not None,
            "블로그 설정을 먼저 저장하세요.")
    if connection.execute("SELECT 1 FROM content_plans LIMIT 1").fetchone():
        return {"inserted": 0, "existing": True}
    if start_date:
        try:
            first = date.fromisoformat(start_date)
        except ValueError:
            raise ValidationError("시작일은 YYYY-MM-DD 형식으로 입력하세요.") from None
        require(first.weekday() == 0, "초기 캘린더 시작일은 월요일이어야 합니다.")
    else:
        today = datetime.now().astimezone().date()
        first = today + timedelta(days=(7 - today.weekday()) % 7)
    offsets = (0, 2, 4) * 4
    for index, (content_type, keyword, title) in enumerate(INITIAL_TOPICS):
        week, within = divmod(index, 3)
        scheduled = first + timedelta(days=week * 7 + offsets[within])
        save_content_plan(connection, scheduled_date=scheduled.isoformat(), content_type=content_type,
                          keyword=keyword, title_seed=title, affiliate_enabled=False)
    return {"inserted": 12, "existing": False}


def get_plan(connection: sqlite3.Connection, plan_id: int) -> dict:
    row = connection.execute("SELECT * FROM content_plans WHERE id=?", (plan_id,)).fetchone()
    require(row is not None, "콘텐츠 계획을 찾을 수 없습니다.")
    result = dict(row)
    for field in ("title_candidates", "template_outline", "fact_checklist", "image_checklist", "tags"):
        result[field] = json.loads(result[field])
    result["affiliate_enabled"] = bool(result["affiliate_enabled"])
    return result


def link_plan_draft(connection: sqlite3.Connection, plan_id: int, draft_id: int) -> None:
    row = connection.execute("SELECT draft_id FROM content_plans WHERE id=?", (plan_id,)).fetchone()
    require(row is not None, "콘텐츠 계획을 찾을 수 없습니다.")
    require(row[0] is None, "이 계획에는 이미 원고가 연결되어 있습니다.")
    connection.execute("UPDATE content_plans SET draft_id=?,stage='draft',updated_at=? WHERE id=?",
                       (draft_id, now(), plan_id))


def mark_research(connection: sqlite3.Connection, *, plan_id: int) -> dict:
    plan = get_plan(connection, plan_id)
    require(plan["stage"] == "planned", "계획 상태의 글만 자료 준비로 변경할 수 있습니다.")
    connection.execute("UPDATE content_plans SET stage='research',updated_at=? WHERE id=?", (now(), plan_id))
    return {"plan_id": plan_id, "stage": "research"}


def sync_plan_stage(connection: sqlite3.Connection, draft_id: int, stage: str) -> None:
    connection.execute("UPDATE content_plans SET stage=?,updated_at=? WHERE draft_id=?", (stage, now(), draft_id))


def duplicate_warnings(connection: sqlite3.Connection) -> list[dict]:
    rows = [dict(row) for row in connection.execute("""SELECT c.id,c.scheduled_date,c.keyword,c.title_seed,d.product_id
        FROM content_plans c LEFT JOIN content_drafts d ON d.id=c.draft_id ORDER BY c.scheduled_date,c.id""")]
    warnings = []
    normalize = lambda value: re.sub(r"[^0-9A-Za-z가-힣]", "", value).lower()
    for index, left in enumerate(rows):
        for right in rows[index + 1:]:
            same_keyword = normalize(left["keyword"]) == normalize(right["keyword"])
            same_title = normalize(left["title_seed"]) == normalize(right["title_seed"])
            same_product = left["product_id"] is not None and left["product_id"] == right["product_id"]
            lt, rt = set(left["title_seed"].split()), set(right["title_seed"].split())
            similarity = len(lt & rt) / max(1, len(lt | rt))
            if same_keyword or same_title or same_product or similarity >= 0.6:
                warnings.append({"plan_ids": [left["id"], right["id"]], "kind": "duplicate" if same_keyword or same_title or same_product else "similar",
                                 "message": "같은 상품·핵심 키워드 또는 제목이 겹칩니다." if same_keyword or same_title or same_product else "유사한 제목이 연속될 수 있습니다."})
    return warnings
