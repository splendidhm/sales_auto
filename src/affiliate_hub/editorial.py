"""Manual editorial workflow shared by CLI and the local review UI.

Call mutations within a transaction and the runtime's exclusive lock.
No network requests and no actual publishing are performed here.
"""

import json
import re
import sqlite3
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit, urlunsplit
from uuid import uuid4

from affiliate_hub.db import now


CHECKS = ("facts", "images", "experience", "freshness", "links_disclosure")
CATEGORIES = ("생활·수납용품", "생활가전·로봇청소기")


class ValidationError(ValueError):
    """Messages contain only application-authored text, never raw user input."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def web_url(value: str) -> str:
    value = value.strip()
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ValidationError("URL의 호스트와 포트 형식을 확인하세요.") from None
    require(parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username
            and not parsed.password and port != 0 and not any(c.isspace() or ord(c) < 32 for c in value),
            "URL은 로그인 정보가 없는 HTTPS 주소로 입력하세요.")
    return value


def observed(value: str) -> str:
    try:
        stamp = datetime.fromisoformat(value)
        require(stamp.tzinfo is not None, "확인 시각에는 시간대가 필요합니다. 예: +09:00")
        require(stamp <= datetime.now(timezone.utc), "자료 확인 시각은 미래일 수 없습니다.")
        return stamp.astimezone(timezone.utc).isoformat()
    except ValueError as exc:
        if isinstance(exc, ValidationError):
            raise
        raise ValidationError("자료 확인 시각을 ISO 형식으로 입력하세요.") from None


def get_product(connection: sqlite3.Connection, product_id: int) -> dict:
    row = connection.execute("""SELECT p.*, f.version, f.facts, f.image_rights,
        f.image_notes,f.experience,f.link_id,l.provider,l.url AS affiliate_url
        FROM products p LEFT JOIN product_profiles f ON f.product_id=p.id
        LEFT JOIN affiliate_links l ON l.id=f.link_id WHERE p.id=?""", (product_id,)).fetchone()
    require(row is not None, "상품을 찾을 수 없습니다.")
    return dict(row)


def save_product(connection: sqlite3.Connection, *, name: str, source_url: str,
                 observed_at: str, facts: str, image_rights: str = "none",
                 image_notes: str = "", experience: str = "", provider: str = "",
                 affiliate_url: str = "", link_confirmed: bool = False,
                 product_id: int | None = None, expected_version: int | None = None,
                 category: str | None = None) -> dict:
    require(bool(name.strip()) and bool(facts.strip()), "상품명과 출처에서 확인한 사실을 입력하세요.")
    source_url = web_url(source_url)
    observed_at = observed(observed_at)
    require(image_rights in ("none", "owned", "licensed", "unknown"), "이미지 권한 구분을 선택하세요.")
    if image_rights in ("owned", "licensed"):
        require(bool(image_notes.strip()), "이미지 파일 위치와 직접 촬영/사용 허락 근거를 적어주세요.")
    affiliate_url = affiliate_url.strip()
    if affiliate_url:
        require(provider in ("shopping_connect", "coupang") and link_confirmed,
                "공식 발급 링크와 네이버 게시 허용 여부를 확인하고 체크하세요.")
        affiliate_url = web_url(affiliate_url)
    stamp = now()
    old = get_product(connection, product_id) if product_id is not None else None
    category = category if category is not None else (old["category"] if old else CATEGORIES[0])
    require(category in CATEGORIES or (old is not None and category == old["category"]), "지원하는 상품 분류를 선택하세요.")
    if product_id is None:
        cursor = connection.execute("""INSERT INTO products
            (source,source_id,name,category,source_url,observed_at,is_mock,created_at,updated_at)
            VALUES('manual',?,?,?,?,?,0,?,?)""",
            (uuid4().hex, name.strip(), category, source_url, observed_at, stamp, stamp))
        product_id, version = cursor.lastrowid, 1
    else:
        require(not old["is_mock"], "가상 상품을 실제 상품으로 변경할 수 없습니다.")
        require(old["version"] == expected_version, "다른 화면에서 상품이 수정되었습니다. 새로고침하세요.")
        version = expected_version + 1
        connection.execute("UPDATE products SET name=?,category=?,source_url=?,observed_at=?,updated_at=? WHERE id=?",
                           (name.strip(), category, source_url, observed_at, stamp, product_id))
    link_id = None
    if affiliate_url:
        link_id = connection.execute("INSERT INTO affiliate_links(product_id,provider,url,confirmed_at) VALUES(?,?,?,?)",
                                     (product_id, provider, affiliate_url, stamp)).lastrowid
    connection.execute("""INSERT INTO product_profiles VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(product_id) DO UPDATE SET version=excluded.version,facts=excluded.facts,
        image_rights=excluded.image_rights,image_notes=excluded.image_notes,
        experience=excluded.experience,link_id=excluded.link_id""",
        (product_id, version, facts.strip(), image_rights, image_notes.strip(), experience.strip(), link_id))
    connection.execute("""UPDATE editorial_state SET status='needs_recheck',approved_revision=NULL
        WHERE draft_id IN (SELECT id FROM content_drafts WHERE product_id=?)""", (product_id,))
    return {"product_id": product_id, "version": version}


def get_draft(connection: sqlite3.Connection, draft_id: int) -> dict:
    row = connection.execute("""SELECT d.id,d.product_id,e.status,e.revision,e.approved_revision,
        r.title,r.body,r.disclosure,r.product_version,r.source_snapshot
        FROM content_drafts d JOIN editorial_state e ON e.draft_id=d.id
        JOIN draft_revisions r ON r.draft_id=d.id AND r.revision=e.revision WHERE d.id=?""", (draft_id,)).fetchone()
    require(row is not None, "실제 상품 원고를 찾을 수 없습니다.")
    return dict(row)


def start_draft(connection: sqlite3.Connection, product_id: int) -> dict:
    product = get_product(connection, product_id)
    require(not product["is_mock"] and product["version"] is not None, "실제 등록 상품만 원고를 만들 수 있습니다.")
    title = f"{product['name']} 선택 전 확인할 점"
    body = f"확인한 상품 정보\n{product['facts']}\n\n[미확인] 공간·용도별 선택 기준과 주의사항을 작성하세요."
    cursor = connection.execute("INSERT INTO content_drafts(product_id,title,body,template_version,created_at) VALUES(?,?,?,?,?)",
                                (product_id, title, body, "manual-v2", now()))
    draft_id = cursor.lastrowid
    connection.execute("INSERT INTO editorial_state VALUES(?,0,'draft',NULL)", (draft_id,))
    return save_draft(connection, draft_id, 0, title, body, "")


def save_draft(connection: sqlite3.Connection, draft_id: int, expected_revision: int,
               title: str, body: str, disclosure: str) -> dict:
    row = connection.execute("""SELECT e.*,d.product_id FROM editorial_state e
        JOIN content_drafts d ON d.id=e.draft_id WHERE e.draft_id=?""", (draft_id,)).fetchone()
    require(row is not None, "원고를 찾을 수 없습니다.")
    require(row["revision"] == expected_revision, "원고 버전이 변경되었습니다. 새로고침 후 다시 저장하세요.")
    require(bool(title.strip()) and bool(body.strip()), "제목과 본문을 입력하세요.")
    product = get_product(connection, row["product_id"])
    revision = expected_revision + 1
    connection.execute("""INSERT INTO draft_revisions
        (draft_id,revision,title,body,disclosure,product_version,source_snapshot,created_at)
        VALUES(?,?,?,?,?,?,?,?)""",
                       (draft_id, revision, title.strip(), body.strip(), disclosure.strip(),
                        product["version"], json.dumps(product, ensure_ascii=False), now()))
    connection.execute("UPDATE editorial_state SET revision=?,status=?,approved_revision=NULL WHERE draft_id=?",
                       (revision, "draft" if revision == 1 else "needs_recheck", draft_id))
    return {"draft_id": draft_id, "revision": revision}


def ready(connection: sqlite3.Connection, draft: dict) -> dict:
    product = get_product(connection, draft["product_id"])
    require(not product["is_mock"], "가상 원고는 승인하거나 게시 기록할 수 없습니다.")
    require(product["version"] == draft["product_version"], "상품 자료가 변경되었습니다. 원고를 확인하고 새 버전으로 저장하세요.")
    require(product["image_rights"] != "unknown", "이미지 사용 권한을 확인하거나 이미지 없음으로 변경하세요.")
    require("[미확인]" not in draft["title"] + draft["body"], "원고의 미확인 항목을 해결하세요.")
    if product["affiliate_url"]:
        require(bool(draft["disclosure"].strip()), "제휴 원고에는 확인한 고지 문구를 입력하세요.")
    return product


def review(connection: sqlite3.Connection, draft_id: int, expected_revision: int,
           reviewer: str, checks: dict) -> dict:
    draft = get_draft(connection, draft_id)
    require(draft["revision"] == expected_revision, "원고 버전이 변경되었습니다. 다시 확인하세요.")
    require(draft["status"] in ("draft", "needs_recheck"), "검토 대기 원고만 검토 완료할 수 있습니다.")
    ready(connection, draft)
    require(bool(reviewer.strip()), "검토자 이름을 입력하세요.")
    require(all(checks.get(key) is True for key in CHECKS), "다섯 가지 검토 항목을 모두 확인하세요.")
    connection.execute("INSERT INTO review_events(draft_id,revision,action,reviewer,checks,created_at) VALUES(?,?,'reviewed',?,?,?)",
                       (draft_id, expected_revision, reviewer.strip(), json.dumps(checks), now()))
    connection.execute("UPDATE editorial_state SET status='reviewed' WHERE draft_id=?", (draft_id,))
    return {"status": "reviewed"}


def approve(connection: sqlite3.Connection, draft_id: int, expected_revision: int, reviewer: str) -> dict:
    draft = get_draft(connection, draft_id)
    require(draft["revision"] == expected_revision and draft["status"] == "reviewed", "현재 버전의 검토 완료가 먼저 필요합니다.")
    ready(connection, draft)
    require(bool(reviewer.strip()), "승인자 이름을 입력하세요.")
    connection.execute("INSERT INTO review_events(draft_id,revision,action,reviewer,checks,created_at) VALUES(?,?,'approved',?,'{}',?)",
                       (draft_id, expected_revision, reviewer.strip(), now()))
    connection.execute("UPDATE editorial_state SET status='approved',approved_revision=revision WHERE draft_id=?", (draft_id,))
    return {"status": "approved"}


def approved_text(connection: sqlite3.Connection, draft_id: int) -> tuple[dict, str]:
    draft = get_draft(connection, draft_id)
    product = ready(connection, draft)
    require(draft["status"] in ("approved", "published") and draft["approved_revision"] == draft["revision"],
            "현재 버전을 검토·승인한 뒤 게시 자료를 내보낼 수 있습니다.")
    parts = [draft["disclosure"], draft["title"], draft["body"]]
    if product["affiliate_url"]:
        parts.append("상품 링크\n" + product["affiliate_url"])
    parts.append("자료 출처\n" + product["source_url"] + "\n확인 시각: " + product["observed_at"])
    return draft, "\n\n".join(part for part in parts if part) + "\n"


def naver_post_url(value: str) -> str:
    parsed = urlsplit(web_url(value))
    require(parsed.hostname in ("blog.naver.com", "m.blog.naver.com") and parsed.port in (None, 443),
            "네이버 블로그 게시글 주소를 입력하세요.")
    path = parsed.path.rstrip("/")
    if re.fullmatch(r"/[A-Za-z0-9_-]+/\d+", path):
        return urlunsplit(("https", "blog.naver.com", path, "", ""))
    query = parse_qs(parsed.query)
    blog_id, log_no = query.get("blogId", [""])[0], query.get("logNo", [""])[0]
    require(path == "/PostView.naver" and bool(re.fullmatch(r"[A-Za-z0-9_-]+", blog_id))
            and log_no.isdigit(), "블로그 홈이 아닌 개별 게시글 주소를 입력하세요.")
    return f"https://blog.naver.com/{blog_id}/{log_no}"


def record_publication(connection: sqlite3.Connection, draft_id: int, expected_revision: int,
                       url: str, confirmed: bool) -> dict:
    require(confirmed, "네이버에 직접 게시한 내용이 승인본과 같은지 확인하세요.")
    draft, _ = approved_text(connection, draft_id)
    require(draft["revision"] == expected_revision, "원고 버전이 변경되었습니다.")
    require(connection.execute("SELECT 1 FROM exports WHERE draft_id=? AND revision=?", (draft_id, expected_revision)).fetchone() is not None,
            "현재 승인본의 게시 자료를 먼저 내보내세요.")
    url = naver_post_url(url)
    existing = connection.execute("SELECT * FROM publication_records WHERE draft_id=? AND revision=?", (draft_id, expected_revision)).fetchone()
    if existing:
        require(existing["url"] == url, "이 원고 버전에는 이미 다른 게시 URL이 기록되어 있습니다.")
        return {"publication_id": existing["id"], "recorded": True, "verified_online": False}
    owner = connection.execute("SELECT draft_id FROM publication_records WHERE url=?", (url,)).fetchone()
    require(owner is None or owner["draft_id"] == draft_id, "다른 원고에 등록된 게시 URL입니다. 기존 게시 이력을 확인하세요.")
    cursor = connection.execute("INSERT INTO publication_records(draft_id,revision,url,recorded_at) VALUES(?,?,?,?)",
                                (draft_id, expected_revision, url, now()))
    connection.execute("UPDATE editorial_state SET status='published' WHERE draft_id=?", (draft_id,))
    return {"publication_id": cursor.lastrowid, "recorded": True, "verified_online": False}
