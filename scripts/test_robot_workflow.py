"""Repeatable AppTest scenario with persistent, isolated robot-vacuum artifacts."""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from streamlit.testing.v1 import AppTest

from affiliate_hub.config import Settings
from affiliate_hub.editorial import ValidationError
from affiliate_hub.service import Hub

ROOT = Path(__file__).resolve().parents[1]
URL = "https://smartstore.naver.com/roborock/products/11548996873"
TITLE = "[테스트용·게시 금지] 로보락 Qrevo L 후보로 살펴보는 로봇청소기 구매 전 체크리스트"
BODY = """이 글은 상품 등록부터 검토·승인·내보내기까지 확인하기 위한 연습 원고입니다.
실제 사용 후기나 구매 추천이 아니며 공개 게시용이 아닙니다.

테스트 대상과 자료 범위
로보락 Qrevo L로 소개된 네이버 판매 URL을 테스트 후보로 선택했습니다.
판매 페이지의 현재 내용은 접근 제한으로 직접 확인하지 못했습니다.
현재 판매 여부·가격·할인·재고·구체적인 성능 수치는 이 글에서 다루지 않습니다.
아래 내용은 이 모델이 특정 기능을 갖췄다는 설명이 아니라 구매 전 확인할 질문입니다.

1. 설치 공간부터 측정하기
충전·관리 스테이션을 둘 장소와 콘센트 위치를 정해보세요.
후보 제품 설명서에서 요구하는 주변 여유 공간과 실제 설치 장소를 비교할 항목으로 남깁니다.

2. 문턱과 가구 아래 공간 확인하기
집 안 문턱 높이와 청소할 가구 아래 공간을 측정해 두세요.
제품의 본체 높이·문턱 관련 조건은 판매자나 공식 설명서에서 확인할 항목입니다.
이 원고는 해당 모델의 통과 가능 높이를 보장하지 않습니다.

3. 바닥과 관리 방식에 맞는지 확인하기
카펫이나 매트 유무, 물걸레 사용이 가능한 바닥인지부터 점검해보세요.
세척·건조·먼지 비움 방식과 관리 빈도는 후보 제품의 공식 안내에서 따로 확인하세요.

4. 소모품과 사후지원 확인하기
필터·브러시·물걸레 등 필요한 소모품의 종류와 구입처를 확인할 항목으로 적어두세요.
보증 조건과 국내 사후지원 창구도 구매 전에 판매자에게 확인하세요.

테스트 정리
설치 공간, 집 안 장애물, 관리 부담, 소모품과 사후지원 순서로 질문을 정리했습니다.
이미지는 사용하지 않았으며 실제 사용 경험은 없습니다.
하단 주소는 일반 판매 페이지 참고 주소이며 쇼핑커넥트·쿠팡 제휴 링크가 아닙니다.
"""


def run_scenario(home: Path) -> dict:
    home.mkdir(parents=True, exist_ok=False)
    outcomes = []
    with patch.dict(os.environ, {"AFFILIATE_HUB_HOME": str(home)}):
        hub = Hub(Settings(home))
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        app.sidebar.radio[0].set_value("상품 자료").run()

        def field(group, label):
            return next(item for item in getattr(app, group) if item.label == label)

        def check(condition, description):
            if not condition:
                raise AssertionError(description)
            outcomes.append(description)

        def click(label, expect_error=False):
            field("button", label).click().run()
            assert not app.exception, str(app.exception)
            assert bool(app.error) == expect_error, str(app.error)

        def blocked(action, **values):
            try:
                hub.mutate(action, **values)
            except ValidationError:
                return
            raise AssertionError(f"Expected rejection: {action}")

        def approve_current():
            field("text_input", "검토자").set_value("Codex 테스트")
            for checkbox in app.checkbox:
                checkbox.check()
            click("검토 완료")
            field("text_input", "승인자").set_value("Codex 테스트")
            click("저장된 원고 승인")

        field("text_input", "상품명").set_value("[테스트용·게시 금지] 로보락 Qrevo L")
        field("selectbox", "상품 분류").select("생활가전·로봇청소기")
        field("text_input", "공식 상품 정보 / 근거 URL").set_value("https://smartstore.naver.com:bad/item")
        field("text_area", "출처에서 확인한 사실").set_value(
            "테스트 자료: 검색에서 로보락 Qrevo L로 소개된 판매 URL을 선택함. "
            "판매 페이지 직접 접근은 robots.txt로 제한되어 현재 판매 상태·가격·사양은 확인하지 못함. "
            "원고는 제품 성능을 단정하지 않는 일반 구매 전 질문으로 구성. 이미지·사용 경험 없음.")
        click("상품 자료 저장", expect_error=True)
        check(not hub.snapshot()["products"], "잘못된 URL: 사용자 안내와 저장 차단")
        field("text_input", "공식 상품 정보 / 근거 URL").set_value(URL)
        click("상품 자료 저장")
        product = hub.snapshot()["products"][0]
        product_id = product["id"]
        check(product["category"] == "생활가전·로봇청소기" and product["affiliate_url"] is None,
              "로봇청소기 분류와 일반 판매 URL 등록, 제휴 링크 없음")
        field("selectbox", "등록 또는 수정").select(product_id).run()
        check(field("selectbox", "상품 분류").value == "생활가전·로봇청소기", "상품 재선택 시 분류 보존")
        click("이 상품으로 초안 만들기")
        app.sidebar.radio[0].set_value("원고 · 검토").run()
        field("text_input", "원고 제목").set_value(TITLE)
        field("text_area", "원고 본문").set_value(BODY)
        click("원고 새 버전 저장")
        draft_id = hub.snapshot()["drafts"][0]["id"]
        blocked("export", draft_id=draft_id)
        outcomes.append("승인 전 내보내기 차단")
        field("text_input", "검토자").set_value("Codex 테스트")
        click("검토 완료", expect_error=True)
        check(hub.snapshot()["drafts"][0]["status"] == "needs_recheck", "검토 체크 누락 시 승인 단계 진입 차단")
        approve_current()
        click("네이버 게시 자료 만들기")
        first_path = Path(hub.settings.home / hub.snapshot()["exports"][0]["relative_path"])
        first = first_path.read_bytes()
        click("네이버 게시 자료 만들기")
        check(first_path.read_bytes() == first and len(hub.snapshot()["exports"]) == 2,
              "반복 내보내기 시 기존 파일 보존")
        blocked("save", draft_id=draft_id, expected_revision=1, title=TITLE, body=BODY, disclosure="")
        outcomes.append("오래된 원고 버전의 덮어쓰기 차단")
        edited_body = BODY + "\n추가 확인: 주문 전 판매자 안내와 모델명을 다시 대조하세요.\n"
        field("text_area", "원고 본문").set_value(edited_body)
        click("원고 새 버전 저장")
        check(hub.snapshot()["drafts"][0]["status"] == "needs_recheck", "승인 후 본문 수정 시 승인 해제")
        blocked("export", draft_id=draft_id)
        approve_current()
        app.sidebar.radio[0].set_value("상품 자료").run()
        field("selectbox", "등록 또는 수정").select(product_id).run()
        field("text_input", "공식 상품 정보 / 근거 URL").set_value(URL + "#qa-test")
        click("상품 자료 저장")
        check(hub.snapshot()["drafts"][0]["status"] == "needs_recheck", "상품 URL 변경 시 승인 해제")
        blocked("export", draft_id=draft_id)
        field("text_input", "공식 상품 정보 / 근거 URL").set_value(URL)
        click("상품 자료 저장")
        app.sidebar.radio[0].set_value("원고 · 검토").run()
        click("원고 새 버전 저장")
        approve_current()
        click("네이버 게시 자료 만들기")
        snapshot = hub.snapshot()
        target = home / snapshot["exports"][0]["relative_path"]
        text = target.read_text(encoding="utf-8")
        check(TITLE in text and edited_body.strip() in text and URL in text and "\ufffd" not in text,
              "최종 TXT 제목·본문·판매 URL·UTF-8 확인")
        # Streamlit st.code strips one leading/trailing newline for display.
        displayed = text.removeprefix("\n").removesuffix("\n")
        check(any(block.value == displayed for block in app.code), "화면 게시 자료와 TXT 내용 일치 (표시용 끝 줄바꿈 제외)")
        check(snapshot["drafts"][0]["status"] == "approved" and snapshot["publications"] == [],
              "최종 승인 상태 유지, 게시 완료 기록 없음")
        report = {"result": "PASS", "home": str(home), "source_url": URL,
                  "source_access": "robots.txt denied; price/specifications/current sale not verified",
                  "export": str(target), "product_id": product_id, "draft_id": draft_id,
                  "revision": snapshot["drafts"][0]["revision"], "checks": outcomes,
                  "publications": 0, "reviewer": "Codex 테스트"}
        (home / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        (home / "result.md").write_text("# 로봇청소기 화면 테스트 결과\n\nPASS — 실제 게시 없음\n\n"
            + "\n".join(f"- PASS: {item}" for item in outcomes)
            + f"\n\n최종 원고: {target.name}\n\n상품 페이지 직접 조회는 제한되어 가격·사양은 검증하지 않았습니다.\n", encoding="utf-8")
        return report


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    production = ROOT / "data" / "affiliate_hub.sqlite3"
    before = hashlib.sha256(production.read_bytes()).hexdigest() if production.exists() else None
    run_home = ROOT / "data" / "robot-tests" / (datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:8])
    result = run_scenario(run_home)
    after = hashlib.sha256(production.read_bytes()).hexdigest() if production.exists() else None
    assert before == after, "Production database changed during isolated test"
    result["production_db_unchanged"] = True
    (run_home / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
