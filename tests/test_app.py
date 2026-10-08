import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from affiliate_hub.config import Settings
from affiliate_hub.service import Hub

ROOT = Path(__file__).resolve().parents[1]


class AppTests(unittest.TestCase):
    def test_owner_can_prepare_review_export_and_record_without_network(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"AFFILIATE_HUB_HOME": directory}):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()

            def field(group, label):
                return next(element for element in getattr(app, group) if element.label == label)

            def click(label):
                field("button", label).click().run()
                self.assertFalse(app.exception)

            self.assertFalse(app.exception)
            field("text_input", "상품명").set_value("화면 테스트 수납함")
            field("text_input", "공식 상품 정보 / 근거 URL").set_value("https://example.com/test")
            field("text_area", "출처에서 확인한 사실").set_value("테스트 자료: 가로 20cm")
            click("상품 자료 저장")
            field("selectbox", "등록 또는 수정").select(1).run()
            click("이 상품으로 초안 만들기")
            app.sidebar.radio[0].set_value("원고 · 검토").run()
            self.assertFalse(app.exception)
            field("text_area", "원고 본문").set_value("가로 20cm입니다. 구매 전 공간을 측정하세요.")
            click("원고 새 버전 저장")
            field("text_input", "검토자").set_value("사용자")
            for checkbox in app.checkbox:
                checkbox.check()
            click("검토 완료")
            field("text_input", "승인자").set_value("사용자")
            click("저장된 원고 승인")
            click("네이버 게시 자료 만들기")
            field("text_input", "직접 게시한 네이버 글 URL").set_value("https://blog.naver.com/tester/123")
            field("checkbox", "네이버에 직접 게시했고 승인본과 내용이 같은지 확인했습니다").check()
            click("게시 URL 기록")
            snapshot = Hub(Settings(Path(directory))).snapshot()
            self.assertEqual(len(snapshot["publications"]), 1)
            self.assertEqual(snapshot["drafts"][0]["status"], "published")
            app.sidebar.radio[0].set_value("게시 이력").run()
            self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
