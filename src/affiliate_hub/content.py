"""Deterministic drafts: no generated claims or fabricated experience."""

import sqlite3

from affiliate_hub.db import now


def create_draft(connection: sqlite3.Connection, product_id: int) -> dict:
    product = connection.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if product is None:
        raise ValueError("Unknown product")
    if not product["is_mock"]:
        from affiliate_hub.editorial import start_draft
        return start_draft(connection, product_id)
    title = f"[테스트·게시 금지] {product['name']} 구매 전 확인 초안"
    body = f"""# {title}

> 가상 상품으로 만든 미검토 연습 원고입니다. 실제 상품 정보가 아니며 게시하면 안 됩니다.
> AI 생성·실사용 후기·제휴 링크·현재 가격·수익 데이터는 포함하지 않습니다.

## 입력 자료
- 상품명: {product['name']}
- 분류: {product['category']}
- 출처: mock (외부 쇼핑 서비스와 무관)
- 가상 주소: {product['source_url']}
- 자료 확인 시각(UTC): {product['observed_at']}

## 작성할 내용
- [미확인] 어떤 공간의 어떤 정리 문제를 해결할지
- [미확인] 설치 공간과 상품의 실제 치수
- [미확인] 소재·관리법과 확인 가능한 공식 출처
- [미확인] 단점과 구매 전 확인사항
- [미확인] 직접 사용한 경우에만 사용 경험 및 사진

## 실제 운영 전 검토 항목
- [ ] 실제 상품 정보와 출처 확인
- [ ] 이미지 사용 권한 확인
- [ ] 가격·재고를 기재한다면 게시 직전 재확인
- [ ] 공식 발급 링크와 허용 채널 확인
- [ ] 제휴 여부에 맞는 최신 고지 문구 확인
- [ ] 사용자 최종 검토

이 파일은 검토용 내보내기이며 게시 완료를 의미하지 않습니다.
"""
    cursor = connection.execute(
        "INSERT INTO content_drafts(product_id,title,body,template_version,created_at) VALUES(?,?,?,?,?)",
        (product_id, title, body, "offline-v1", now()),
    )
    return {"draft_id": cursor.lastrowid, "status": "draft", "is_mock": True}
