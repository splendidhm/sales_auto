"""Run using scripts/start_review.cmd; local owner-only editorial screen."""

from datetime import datetime, timedelta, timezone
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
page = st.sidebar.radio("작업 단계", ["상품 자료", "원고 · 검토", "게시 이력"], key="page")
st.sidebar.caption("이 PC의 로컬 작업실입니다. 네이버 로그인·자동 게시·AI 호출은 하지 않습니다.")
if st.sidebar.button("새로고침"):
    st.rerun()
try:
    snapshot = hub.snapshot()
except BusyError:
    st.info("다른 작업이 실행 중입니다. 잠시 후 새로고침하세요.")
    st.stop()
products = {p["id"]: p for p in snapshot["products"] if not p["is_mock"]}

if page == "상품 자료":
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
else:
    st.subheader("직접 게시한 글의 기록")
    st.caption("사용자가 입력한 게시 이력입니다. 온라인 게시 상태를 조회하거나 확인한 결과는 아닙니다.")
    st.dataframe(snapshot["publications"], hide_index=True)
