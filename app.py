"""Run using scripts/start_review.cmd; local owner-only editorial screen."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

from affiliate_hub.config import Settings
from affiliate_hub.editorial import CATEGORIES, CHECKS, ValidationError
from affiliate_hub.runtime import BusyError
from affiliate_hub.service import Hub

st.set_page_config(page_title="쇼핑 콘텐츠 작업실", page_icon="📝", layout="wide")
hub = Hub(Settings.load())
LABELS = {"draft": "초안", "needs_recheck": "재검토 필요", "reviewed": "검토 완료",
          "approved": "승인 완료", "published": "게시 기록됨"}
STAGES = {"planned": "계획", "research": "자료 준비", "draft": "초안", "reviewed": "검토",
          "approved": "승인", "packaged": "게시자료 생성", "published": "URL 기록"}
RIGHTS = {"none": "이미지 사용 안 함", "owned": "직접 촬영", "licensed": "사용 허락 확보", "unknown": "확인 전"}


def act(action: str, **values):
    try:
        result = hub.mutate(action, **values)
    except ValidationError as exc:
        st.error(str(exc))
        return
    except BusyError:
        st.warning("다른 작업이 실행 중입니다. 잠시 후 다시 시도하세요.")
        return
    except Exception:
        st.error("저장하지 못했습니다. 입력값과 파일 권한을 확인하세요. 오류 유형은 logs에 기록됩니다.")
        return
    st.session_state["notice"] = "저장했습니다." if action != "export" else "게시 자료를 준비했습니다. 아래에서 내용을 확인하고 다운로드하세요."
    if action == "export":
        st.session_state["last_export"] = result
    st.rerun()


st.title("쇼핑 콘텐츠 작업실")
st.caption("상품 자료 → 원고 작성 → 검토·승인 → 네이버에 직접 게시 → URL 기록")
if message := st.session_state.pop("notice", None):
    st.success(message)
st.sidebar.title("작업 메뉴")
page = st.sidebar.radio("작업 단계", ["이번 주 게시", "콘텐츠 캘린더", "상품 자료", "원고 · 검토",
                                   "블로그 설정", "중복 경고", "게시 이력"], key="page")
st.sidebar.caption("이 PC의 로컬 작업실입니다. 네이버 로그인·자동 게시·AI 호출은 하지 않습니다.")
if st.sidebar.button("새로고침"):
    st.rerun()
try:
    snapshot = hub.snapshot()
except BusyError:
    st.info("다른 작업이 실행 중입니다. 잠시 후 새로고침하세요.")
    st.stop()
products = {p["id"]: p for p in snapshot["products"] if not p["is_mock"]}

if page == "이번 주 게시":
    st.subheader("이번 주 승인된 게시물")
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    ready_plans = [p for p in snapshot["plans"] if monday.isoformat() <= p["scheduled_date"] <= sunday.isoformat()
                   and p["stage"] in ("approved", "packaged", "published")]
    st.caption(f"{monday.isoformat()} ~ {sunday.isoformat()} · 승인된 원고만 표시합니다.")
    if ready_plans:
        st.dataframe([{"예정일": p["scheduled_date"], "제목": p["title_seed"], "상태": STAGES[p["stage"]],
                       "제휴": "예" if p["affiliate_enabled"] else "아니오"} for p in ready_plans], hide_index=True)
    else:
        st.info("이번 주에 승인된 게시물이 없습니다. 원고 검토와 승인을 완료하세요.")
    metrics = snapshot["metrics"]
    columns = st.columns(4)
    columns[0].metric("준비 편수", metrics["prepared"])
    columns[1].metric("승인 편수", metrics["approved"])
    columns[2].metric("실제 게시 편수", metrics["published"])
    columns[3].metric("평균 검토 시간", "기록 없음" if metrics["average_review_minutes"] is None else f"{metrics['average_review_minutes']}분")

elif page == "콘텐츠 캘린더":
    st.subheader("생활가전·수납 콘텐츠 캘린더")
    if snapshot["blog"] is None:
        st.info("블로그 설정을 먼저 저장하세요.")
    else:
        if not snapshot["plans"]:
            next_monday = date.today() + timedelta(days=(7 - date.today().weekday()) % 7)
            with st.form("seed-calendar"):
                first = st.date_input("4주 캘린더 시작 월요일", value=next_monday)
                if st.form_submit_button("초기 12편 만들기", type="primary"):
                    act("seed_calendar", start_date=first.isoformat())
        with st.form("add-plan"):
            st.write("**개별 일정 추가**")
            scheduled = st.date_input("발행 예정일")
            content_type = st.selectbox("콘텐츠 유형", ["information", "comparison"],
                                        format_func=lambda x: "정보성" if x == "information" else "비교·선택")
            keyword = st.text_input("핵심 키워드")
            title_seed = st.text_input("계획 제목")
            affiliate = st.checkbox("공식 쇼핑커넥트 링크를 사용하는 제휴 글")
            if st.form_submit_button("일정 추가"):
                act("content_plan", scheduled_date=scheduled.isoformat(), content_type=content_type,
                    keyword=keyword, title_seed=title_seed, affiliate_enabled=affiliate)
    if snapshot["plans"]:
        st.dataframe([{"ID": p["id"], "예정일": p["scheduled_date"], "유형": "정보성" if p["content_type"] == "information" else "비교·선택",
                       "핵심 키워드": p["keyword"], "제목": p["title_seed"], "상태": STAGES[p["stage"]]} for p in snapshot["plans"]], hide_index=True)
        unlinked = {p["id"]: p for p in snapshot["plans"] if p["draft_id"] is None}
        planned = {p["id"]: p for p in snapshot["plans"] if p["stage"] == "planned"}
        if planned:
            research_id = st.selectbox("자료 준비를 시작할 계획", list(planned), format_func=lambda x: f"#{x} {planned[x]['title_seed']}")
            if st.button("자료 준비 시작"):
                act("research", plan_id=research_id)
        if unlinked and products:
            with st.form("plan-draft"):
                plan_id = st.selectbox("원고로 만들 계획", list(unlinked), format_func=lambda x: f"#{x} {unlinked[x]['scheduled_date']} {unlinked[x]['title_seed']}")
                product_id = st.selectbox("근거로 연결할 상품 자료", list(products), format_func=lambda x: f"#{x} {products[x]['name']}")
                if st.form_submit_button("템플릿 원고 만들기"):
                    act("start", product_id=product_id, plan_id=plan_id)
        with st.expander("선택 계획의 템플릿 확인"):
            plan_id = st.selectbox("템플릿 계획", [p["id"] for p in snapshot["plans"]], key="template-plan")
            plan = next(p for p in snapshot["plans"] if p["id"] == plan_id)
            st.write("제목 후보", plan["title_candidates"])
            st.write("글 구조", plan["template_outline"])
            st.write("확인할 사실", plan["fact_checklist"])
            st.write("이미지 목록", plan["image_checklist"])
            st.write("태그 후보", plan["tags"])

elif page == "블로그 설정":
    st.subheader("네이버 블로그 설정")
    blog = snapshot["blog"] or {}
    status_options = ["information", "brand_connected", "shopping_connect_ready"]
    status_labels = {"information": "정보성 운영", "brand_connected": "브랜드 커넥트 연동",
                     "shopping_connect_ready": "쇼핑커넥트 링크 사용 가능"}
    with st.form("blog-settings"):
        blog_name = st.text_input("블로그명", value=blog.get("blog_name", ""))
        blog_url = st.text_input("블로그 URL", value=blog.get("blog_url", "https://blog.naver.com/"))
        topic = st.text_input("주제", value=blog.get("topic", "생활가전·수납"))
        st.multiselect("발행 요일", ["월", "수", "금"], default=["월", "수", "금"], disabled=True)
        enrollment = st.selectbox("운영 단계", status_options, index=status_options.index(blog.get("enrollment_status", "information")), format_func=status_labels.get)
        if st.form_submit_button("블로그 설정 저장", type="primary"):
            act("blog_settings", blog_name=blog_name, blog_url=blog_url, topic=topic,
                publish_days=["월", "수", "금"], enrollment_status=enrollment)
    st.caption("네이버 로그인이나 자동 게시를 하지 않습니다. 운영 단계는 실제 가입·연동 결과를 확인한 뒤 변경하세요.")

elif page == "중복 경고":
    st.subheader("중복·연속 유사 글 경고")
    if snapshot["duplicate_warnings"]:
        st.dataframe([{"계획 ID": ", ".join(map(str, warning["plan_ids"])), "구분": warning["kind"], "내용": warning["message"]}
                      for warning in snapshot["duplicate_warnings"]], hide_index=True)
    else:
        st.success("현재 등록된 일정에서 같은 키워드·제목 또는 높은 제목 유사도를 찾지 못했습니다.")

elif page == "상품 자료":
    st.subheader("상품과 근거 자료")
    selected = st.selectbox("등록 또는 수정", [None, *products],
                            format_func=lambda x: "새 상품 등록" if x is None else f"#{x} {products[x]['name']}", key="product_select")
    product = products.get(selected, {})
    token = f"product-{selected}-{product.get('version', 0)}"
    with st.form(token, enter_to_submit=False):
        name = st.text_input("상품명", value=product.get("name", ""), key=token + "name")
        categories = list(dict.fromkeys([*CATEGORIES, product.get("category", CATEGORIES[0])]))
        category = st.selectbox("상품 분류", categories, index=categories.index(product.get("category", CATEGORIES[0])), key=token + "category")
        source_url = st.text_input("공식 상품 정보 / 근거 URL", value=product.get("source_url", ""), key=token + "source")
        stamp = st.text_input("자료 확인 시각 (시간대 포함)", value=product.get("observed_at", datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")), key=token + "time")
        facts = st.text_area("출처에서 확인한 사실", value=product.get("facts", ""), help="치수·소재·관리법 등 확인한 내용만 적으세요.", key=token + "facts")
        rights = st.selectbox("이미지 사용", list(RIGHTS), index=list(RIGHTS).index(product.get("image_rights", "none")), format_func=RIGHTS.get, key=token + "rights")
        image_notes = st.text_area("이미지 파일 위치 · 사용 권한 근거", value=product.get("image_notes", ""), key=token + "images")
        experience = st.text_area("직접 사용한 경험 (없으면 비워두세요)", value=product.get("experience", ""), key=token + "experience")
        st.caption("제휴 링크 없이 정보성 원고부터 시작할 수 있습니다. 링크는 공식 서비스에서 직접 발급한 주소를 입력하세요.")
        provider = st.selectbox("제휴 서비스", ["shopping_connect", "coupang"], index=1 if product.get("provider") == "coupang" else 0,
                                format_func=lambda x: "쇼핑커넥트" if x == "shopping_connect" else "쿠팡 파트너스", key=token + "provider")
        link = st.text_input("공식 제휴 링크 (선택)", value=product.get("affiliate_url") or "", key=token + "link")
        confirmed = st.checkbox("이 링크의 공식 발급과 네이버 채널 사용 허용을 확인했습니다", key=token + "linkcheck")
        if st.form_submit_button("상품 자료 저장", type="primary"):
            act("product", name=name, category=category, source_url=source_url, observed_at=stamp, facts=facts,
                image_rights=rights, image_notes=image_notes, experience=experience,
                provider=provider, affiliate_url=link, link_confirmed=confirmed,
                product_id=selected, expected_version=product.get("version"))
    if selected is not None:
        st.caption("자료나 링크를 저장하면 연결된 원고가 재검토 상태로 바뀝니다.")
        if st.button("이 상품으로 초안 만들기", key="start_draft"):
            act("start", product_id=selected)
    with st.expander("가상 테스트 데이터 (실제 상품과 분리)"):
        mocks = [{"ID": p["id"], "이름": p["name"]} for p in snapshot["products"] if p["is_mock"]]
        st.write(mocks if mocks else "가상 데이터가 없습니다.")

elif page == "원고 · 검토":
    drafts = {d["id"]: d for d in snapshot["drafts"]}
    if not drafts:
        st.info("상품 자료에서 실제 상품을 등록한 뒤 ‘이 상품으로 초안 만들기’를 누르세요.")
        st.stop()
    draft_id = st.selectbox("작업할 원고", list(drafts), format_func=lambda x: f"#{x} {drafts[x]['title']} · {LABELS[drafts[x]['status']]}", key="draft_select")
    draft = drafts[draft_id]
    product = products[draft["product_id"]]
    revision = draft["revision"]
    token = f"draft-{draft_id}-{revision}-{product['version']}-{draft['status']}"
    st.subheader(f"{LABELS[draft['status']]} · 원고 버전 {revision}")
    left, right = st.columns([2, 1])
    with right:
        st.write("**현재 상품 근거**")
        st.text(product["facts"])
        st.text("출처: " + product["source_url"])
        st.text("확인 시각: " + product["observed_at"])
        st.text("이미지: " + RIGHTS[product["image_rights"]])
        st.text(product["image_notes"] or "이미지 자료 없음")
        st.text("사용 경험: " + (product["experience"] or "등록된 경험 없음"))
        st.text("제휴 링크: " + (product["affiliate_url"] or "없음"))
    with left:
        with st.form(token + "edit", enter_to_submit=False):
            title = st.text_input("원고 제목", value=draft["title"], key=token + "title")
            body = st.text_area("원고 본문", value=draft["body"], height=300, key=token + "body")
            disclosure = st.text_area("제휴 고지 문구", value=draft["disclosure"], help="제휴 링크가 있으면 필수입니다. 해당 서비스의 최신 지침을 확인한 문구를 입력하세요.", key=token + "disclosure")
            if st.form_submit_button("원고 새 버전 저장"):
                act("save", draft_id=draft_id, expected_revision=revision, title=title, body=body, disclosure=disclosure)
    st.caption("검토·승인 대상은 저장된 원고입니다. 편집 중인 내용은 먼저 ‘원고 새 버전 저장’을 눌러 반영하세요.")
    with st.expander("저장된 원고 확인", expanded=True):
        st.code("\n\n".join(x for x in (draft["disclosure"], draft["title"], draft["body"]) if x), language=None)
    if draft["status"] in ("draft", "needs_recheck"):
        with st.form(token + "review", enter_to_submit=False):
            reviewer = st.text_input("검토자", key=token + "reviewer")
            labels = ("본문의 사실과 출처를 확인했습니다", "이미지 미사용 또는 사용 권한을 확인했습니다",
                      "사용 경험을 꾸미지 않았습니다", "가격·재고 등 변동 정보는 재확인하거나 제외했습니다",
                      "제휴 링크·채널 허용·고지 문구를 확인했습니다 (비제휴 글은 해당 없음)")
            checks = {key: st.checkbox(label, key=token + key) for key, label in zip(CHECKS, labels)}
            if st.form_submit_button("검토 완료"):
                act("review", draft_id=draft_id, expected_revision=revision, reviewer=reviewer, checks=checks)
    if draft["status"] == "reviewed":
        with st.form(token + "approve", enter_to_submit=False):
            reviewer = st.text_input("승인자", key=token + "approver")
            if st.form_submit_button("저장된 원고 승인", type="primary"):
                act("approve", draft_id=draft_id, expected_revision=revision, reviewer=reviewer)
    if draft["status"] in ("approved", "published"):
        if st.button("네이버 게시 자료 만들기", key="export_draft", type="primary"):
            act("export", draft_id=draft_id)
        exports = [e for e in snapshot["exports"] if e["draft_id"] == draft_id and e["revision"] == revision]
        if exports:
            path = hub.settings.home / exports[0]["relative_path"]
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                st.code(text, language=None)
                st.download_button("게시 자료 다운로드 (.txt)", text, file_name=path.name, mime="text/plain")
                st.caption("본문을 복사해 네이버에 직접 게시하세요. 이미지는 권한이 확인된 원본을 직접 첨부합니다.")
            with st.form(token + "record", enter_to_submit=False):
                url = st.text_input("직접 게시한 네이버 글 URL", key=token + "url")
                confirmed = st.checkbox("네이버에 직접 게시했고 승인본과 내용이 같은지 확인했습니다", key=token + "posted")
                if st.form_submit_button("게시 URL 기록"):
                    act("record", draft_id=draft_id, expected_revision=revision, url=url, confirmed=confirmed)
    with st.expander("원고 버전 · 검토 이력"):
        st.write([{k: r[k] for k in ("revision", "action", "reviewer", "created_at")} for r in snapshot["reviews"] if r["draft_id"] == draft_id])
        for old in (r for r in snapshot["revisions"] if r["draft_id"] == draft_id):
            st.write(f"버전 {old['revision']} · {old['created_at']}")
            st.code(old["title"] + "\n\n" + old["body"], language=None)
elif page == "게시 이력":
    st.subheader("직접 게시한 글의 기록")
    st.caption("사용자가 입력한 게시 이력입니다. 온라인 게시 상태를 조회하거나 확인한 결과는 아닙니다.")
    st.dataframe(snapshot["publications"], hide_index=True)
