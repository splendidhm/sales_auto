# Affiliate Hub — 쇼핑 콘텐츠 자동화 준비 도구

Windows에서 API 키 없이 실행하는 **네이버 블로그 운영·편집 도구**입니다. 블로그 설정, 월·수·금 4주 12편 캘린더, 사실 확인용 템플릿, 중복 경고, 원고 검토·승인, 네이버 게시 패키지, 직접 게시한 URL 기록을 지원합니다. 상품 자동 조회, AI 호출, 링크 자동 발급, 자동 게시, 수익 수집은 구현하지 않습니다.

## 운영 화면 실행

`scripts/start_review.cmd`를 더블클릭하거나 다음 명령을 실행하세요.

```powershell
cd 'C:\Users\케이지에프앤비\codex\projects\sales_auto'
.\scripts\start_review.cmd
```

브라우저에서 **http://127.0.0.1:8501**을 엽니다. 실행 창을 유지하고, 종료할 때 Ctrl+C를 누르세요. 이 PC에서만 접속할 수 있으며 로그인 기능은 없습니다. 원격 공개용 서비스로 사용하지 마세요. 8501 포트가 사용 중이면 임의로 기존 프로그램을 종료하지 말고 다른 포트로 실행하세요.

현재 가상환경에는 Streamlit 1.65.0을 설치했습니다. 다른 PC에서는 기존 Python/가상환경 설정 후 다음을 실행합니다. 설치 시에만 패키지 다운로드가 필요합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
```

1. **블로그 설정:** 실제 블로그명과 `https://blog.naver.com/<아이디>` URL을 입력하고 현재 연동 단계를 선택합니다.
2. **콘텐츠 캘린더:** 시작 월요일을 골라 생활가전·수납 12편을 생성합니다. 제목 후보, 구조, 사실·이미지 확인 목록과 태그를 확인합니다.
3. **상품 자료:** 상품명, 분류, 출처 HTTPS URL, 확인 시각, 확인한 사실, 이미지 권한과 사용 경험을 입력합니다. 제휴 링크가 없어도 됩니다.
4. **템플릿 원고:** 캘린더 계획과 상품 자료를 연결하고 `[미확인]` 부분을 출처에 근거한 문장으로 직접 고칩니다.
5. **검토·승인:** 다섯 항목을 확인하고 승인합니다. `이번 주 게시`에는 승인된 항목만 표시됩니다.
6. **게시 자료:** 승인본을 TXT로 만들고 네이버 편집기에 직접 복사합니다. 이미지 권한을 다시 확인해 직접 첨부합니다.
7. **게시 URL 기록:** 승인본과 실제 글이 같은지 확인하고 네이버 개별 글 URL을 등록합니다.

상품 자료·제휴 링크를 저장하거나 원고를 수정하면 기존 승인이 해제됩니다. 상품 변경 후에는 원고를 다시 저장하고 검토해야 합니다. 이전 원고 버전과 게시 이력은 남습니다. 같은 URL의 수정 게시 이력은 동일 원고의 새 승인 버전에 기록할 수 있습니다. 다른 원고에 동일 URL을 중복 연결할 수 없습니다.

원고 입력은 일반 텍스트 기준입니다. HTML 렌더링이나 이미지 수집·업로드는 하지 않습니다. 고지 문구는 자동 법률 검증하지 않으며 사용자가 서비스의 최신 안내를 확인해야 합니다. 외부 페이지의 사실·이미지 권한도 입력과 사람의 검토를 기반으로 합니다.

## 기존 데이터 업그레이드

### v2 → v3 전환

최초 실행 시 운영 DB를 `data/pre-v3-<uuid>.sqlite3`로 백업하고 블로그 설정·콘텐츠 계획 테이블을 추가합니다. 기존 상품, 원고, 검토, 내보내기와 게시 이력을 수정하지 않습니다. 블로그 설정과 초기 12편은 실제 블로그 URL을 입력한 뒤 화면에서 생성합니다.

### 로봇청소기 테스트 결과 보기

로봇청소기 테스트는 별도 폴더에서 실행했습니다. 최종 원고와 결과는 `data/robot-tests/20261008-020632-c4db345a`의 `exports/`, `result.md`, `result.json`에 있습니다. 실제 게시하지 않았습니다. 판매 URL의 현재 페이지는 접근 제한으로 확인하지 못해 가격·사양을 단정하지 않는 구매 전 체크리스트로 작성했습니다.

이 데이터를 화면에서 열려면 별도 PowerShell 창에서 실행하세요. 기존 작업실이 실행 중이어도 충돌하지 않도록 8502 포트를 사용합니다.

```powershell
cd 'C:\Users\케이지에프앤비\codex\projects\sales_auto'
$env:AFFILIATE_HUB_HOME = 'C:\Users\케이지에프앤비\codex\projects\sales_auto\data\robot-tests\20261008-020632-c4db345a'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502 --server.headless true
```

브라우저에서 `http://127.0.0.1:8502`에 접속하세요. 종료는 Ctrl+C이며, 해당 PowerShell 창을 닫으면 환경변수 설정도 사라집니다. 테스트를 재현하려면 `.venv\Scripts\python.exe scripts\test_robot_workflow.py`를 실행합니다. 실행마다 새로운 테스트 폴더를 만들고 경로를 출력합니다.

### v1 → v2 전환

최초 실행 시 SQLite v1 → v2로 전환합니다. 먼저 `data/pre-v2-<uuid>.sqlite3` 백업을 만들고, 새 편집 테이블을 트랜잭션으로 추가합니다. 기존 상품·가상 초안·작업 이력·내보낸 파일은 보존합니다. 가상 상품은 실제 상품 입력·승인 대상으로 전환하지 않습니다.

복원이 필요하면 앱과 CLI를 모두 종료한 뒤 현재 DB를 별도 이름으로 보관하고, pre-v2 백업을 `data/affiliate_hub.sqlite3`로 복사합니다. 이 복원은 2단계 이후 기록을 포함하지 않습니다. 현재 프로그램을 다시 켜면 v2와 v3 마이그레이션이 순서대로 수행됩니다. 이는 마이그레이션 시점의 백업이며 정기 백업·30일 자동 정리는 후속 단계입니다.

## 가상 데이터 CLI 실행 (기존 1단계)

현재 작업 경로:

```powershell
cd 'C:\Users\케이지에프앤비\codex\projects\sales_auto'
.\.venv\Scripts\python.exe -m affiliate_hub.cli init-db
.\.venv\Scripts\python.exe -m affiliate_hub.cli collect --provider mock
.\.venv\Scripts\python.exe -m affiliate_hub.cli collect --provider mock
.\.venv\Scripts\python.exe -m affiliate_hub.cli products
.\.venv\Scripts\python.exe -m affiliate_hub.cli draft --product-id 1
.\.venv\Scripts\python.exe -m affiliate_hub.cli drafts
.\.venv\Scripts\python.exe -m affiliate_hub.cli export --draft-id 1
.\.venv\Scripts\python.exe -m affiliate_hub.cli status
```

깨끗한 DB에서 첫 수집은 `inserted: 3`, 다음 수집은 `inserted: 0, updated: 3, total: 3`입니다. 이미 수집했다면 첫 명령도 업데이트로 표시됩니다. `draft`는 실행할 때마다 새 초안을 생성합니다. 실제 ID는 `drafts`에서 확인하세요. `export`는 매번 새 파일을 만들며 기존 파일과 메모를 덮어쓰지 않습니다.

출력은 UTF-8 JSON입니다. 내보낸 원고에는 **가상 테스트·게시 금지** 표시와 미확인 항목이 들어갑니다. 내보내도 초안 상태는 `draft`이며 `published: false`입니다. `performance: null`은 미수집을 뜻하며 수익 0원이 아닙니다.

## 다른 PC에서 설치 / 환경 복구

Python 3.12 이상이 필요합니다. 현재 PC에서는 Python 3.14가 발견되었고 `py`, `python` 명령은 PATH에서 찾지 못했습니다. 설치된 실행 파일의 절대 경로를 사용합니다.

```powershell
cd 'C:\Users\케이지에프앤비\codex\projects\sales_auto'
& 'C:\Users\케이지에프앤비\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m venv .venv
.\.venv\Scripts\python.exe scripts\setup_local.py
```

`setup_local.py`는 이 프로젝트의 가상환경에 `src` 경로를 등록합니다. 다운로드나 전역 설치를 하지 않습니다. 가상환경 또는 프로젝트를 이동하면 다시 생성·등록하세요. `.env` 파일은 자동으로 읽지 않으며, 1단계는 API 키를 요구하지 않습니다.

일반 패키지 설치를 원할 때는 아래 방식을 사용할 수 있습니다. 이 방식은 인터넷과 패키지 다운로드가 필요할 수 있으며, 위의 오프라인 등록을 했으면 실행에 필요하지 않습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest -q
```

## 데이터와 로그

| 경로 | 용도 |
|---|---|
| `data/affiliate_hub.sqlite3` | 상품, 작업 이력, 초안, 내보내기 기록 |
| `data/runtime.lock` | OS 파일 잠금; 파일이 남아 있어도 실행 중이라는 뜻은 아님 |
| `logs/events.jsonl` | UTC 시각과 작업 ID를 포함한 구조화 로그 |
| `exports/draft-<id>-<uuid>.md` | 가상 상품의 검토용 원고 |

기본 저장 위치는 현재 터미널 위치가 아닌 프로젝트 루트입니다. 분리된 연습 환경은 **절대 경로**로 지정하세요. 우선순위는 `--home` → `AFFILIATE_HUB_HOME` 환경변수 → 소스 프로젝트 루트입니다.

```powershell
.\.venv\Scripts\python.exe -m affiliate_hub.cli --home 'C:\Users\케이지에프앤비\codex\projects\sales_auto\data\practice' collect
```

상품은 `(source, source_id)`로 중복을 방지합니다. 원본 ID와 내부 ID를 구분하고 관측 시각을 저장합니다. 모든 명령은 같은 실행 잠금을 사용합니다. 프로세스 종료 시 OS가 잠금을 해제하며, 다음 실행은 남아 있던 `running` 이력을 `interrupted`로 바꿉니다. DB 버전이 지원 범위보다 높으면 덮어쓰지 않고 실패합니다.

내보내기 도중 강제 종료되면 DB에 기록되지 않은 파일이 남을 수 있습니다. 다음 내보내기는 새 이름을 사용합니다. 이는 게시 파일이 아니며, 고아 파일 정리·자동 백업·로그 보관주기 처리는 후속 단계입니다. 지금 수동 백업할 때는 실행을 멈춘 상태에서 `data`, `exports`를 함께 복사하세요.

## 테스트 및 실패 확인

기존 코어 테스트는 외부 패키지 없이 실행할 수 있습니다. 전체 테스트는 Streamlit 설치가 필요하며 실제 상품 저장·승인 규칙과 AppTest 기반 화면 흐름도 검증합니다. 테스트 데이터는 임시 폴더에만 생성합니다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\check_server.py
.\.venv\Scripts\python.exe -m affiliate_hub.cli collect --simulate-failure
$LASTEXITCODE
.\.venv\Scripts\python.exe -m affiliate_hub.cli status
```

실패 주입은 종료 코드 `1`, 실패 작업 이력과 로그를 남깁니다. 명령 문법 오류는 `2`, 중복 실행은 `3`, 성공은 `0`입니다. 오류 원문과 환경변수는 로그에 출력하지 않습니다. 잘못된 상품·초안 ID는 `ValueError`, 파일 접근 문제는 해당 오류 유형으로 표시됩니다. 로그 폴더 자체에 쓸 수 없는 초기화 실패는 stderr로만 보고될 수 있습니다.

## Windows 작업 스케줄러 (아직 등록하지 않음)

수동 실행이 성공한 뒤 아래 설정으로 가상 수집만 등록할 수 있습니다.

| 항목 | 설정 |
|---|---|
| 이름 | `AffiliateHub_DailyMockCollect` |
| 프로그램 | `C:\Users\케이지에프앤비\codex\projects\sales_auto\.venv\Scripts\python.exe` |
| 인수 | `-m affiliate_hub.cli collect --provider mock` |
| 시작 위치 | `C:\Users\케이지에프앤비\codex\projects\sales_auto` |
| 실행 시간 | 매일 07:00, PC의 한국 시간 설정 확인 |
| 실행 계정 | 해당 폴더와 Python에 접근 가능한 일반 사용자, 관리자 권한 불필요 |
| 중복 실행 | 새 인스턴스를 시작하지 않음 |
| 실패 재시도 | 10분 간격, 최대 3회 (중복 방지되는 수집만 해당) |
| 실행 제한 | 5분 |
| 누락된 예약 | 가능한 즉시 실행하도록 설정 |

PC가 꺼져 있으면 실행되지 않습니다. 절전 해제는 Windows 전원 정책에 따라 달라집니다. 로그인 없이 실행하려면 계정·자격증명과 파일 접근을 별도로 검증해야 하며, 이 코드는 대화형 바탕화면이나 브라우저 로그인을 요구하지 않습니다. 등록 후 ‘실행’을 눌러 마지막 결과 `0x0`, `status`, 로그를 확인해야 예약 작업 검증이 완료됩니다.

`scripts\run_collect.cmd`로도 수동 수집할 수 있습니다. 실행 디렉터리를 직접 설정하고 Python 종료 코드를 그대로 반환합니다.

## 확정한 후속 순서

1. 네이버 생활·수납 블로그 개설과 정보성 콘텐츠 준비. 쇼핑커넥트 가입·허용 채널 확인.
2. **구현 완료:** 수동 상품·공식 링크 입력, 로컬 Streamlit 검토 화면, 게시 URL 기록.
3. 쇼핑커넥트 이용 가능 상태에서 링크 활용. AI API 연결과 비용 제한, 검토·승인 흐름 추가.
4. 4주·12편 운영, 최근 2주 하루 30분 이내 검토, 총 월 5만원 이내 조건을 만족하면 별도 WordPress 도입.
5. 쿠팡 파트너스 공식 API 권한 확인 후 추가. 성과 수집, 백업·복구, 예약 실행 고도화.

HPL은 기존 경제·데이터 사이트로 유지합니다. Instagram·무인 대량 발행·클라우드 상시 실행은 초기 범위에서 제외합니다. 공식 API가 확인되지 않은 기능은 수동 입력·내보내기로 유지합니다. 가입 조건을 충족하지 못해도 정보성 콘텐츠 운영은 계속할 수 있습니다.

운영 목표는 주 3편, 매일 검토 15~30분입니다. 월 비용 한도는 AI 2만원, WordPress 도입 후 호스팅·도메인 월 환산 2만원, 예비비 1만원이며 실제 견적이 아닙니다. 사람의 검토·승인은 구현했지만 자동 발행·정기 백업 등 후속 기능은 아직 없습니다.

기술 참고: [Streamlit 폼](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form), [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest). UI는 폼 제출 시 저장하고 AppTest로 사용자 조작 흐름을 검증합니다.
