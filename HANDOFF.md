# Affiliate Hub — 구현 인수인계

## 다음 세션 시작점 — 전체 작업 요약 (2026-10-26)

**이 절이 최신 상태다. 아래 단계별 기록의 ‘미생성/미구현/다음 작업’은 당시 기록이며 현재 상태와 구분한다.**

### 운영 결정과 읽을 문서

- 저장소: https://github.com/splendidhm/sales_auto.git, 브랜치 main. 로컬: `C:\Users\케이지에프앤비\codex\projects\sales_auto`.
- 읽는 순서: AGENTS.md → 이 절 → [통합 편집 지침](docs/BLOG_EDITORIAL_GUIDE.md) → [수동 운영 절차](docs/MANUAL_BLOG_WORKFLOW.md). README는 실행 안내, SKILLS_USED는 실제 스킬/도구 이력.
- HiddenPatternsLab 인스타그램 콘텐츠의 블로그 확장판. HPL 웹사이트 코드는 별도 유지. 기존 인스타 원본은 아직 제공되지 않았으며 실제 원본 열람·확장 검증은 미수행.
- Plus 이용 환경의 대화에서 사용자 수동 요청으로 글·이미지 작성. 별도 API/모델/예산 결정은 보류. 자동 수집·생성·발행 기능을 추가하지 않음. 이용 한도 도달 시 API로 자동 전환 금지.
- 두 방식: 주제 기반 글·요청한 AI 이미지 / 사용자 사진+주제+경험 메모로 글·캡션. 내 사진 방식에 요청 없는 AI 이미지 보충 금지.
- 초기 발행은 하루 1개 이하(이전 1~2편을 대체). 20편 주기 목표: 부동산 7, 금융·투자 6, 사회이슈 4, 일상·생활 2, 여행·과학 1. 부동산+금융은 완성 주기 60~70% 목표.
- 자연스러운 존댓말, 기본 본문 1,000~2,000자, 심층 2,500~3,000자, 제목 후보 3개. 유형 A~F와 전개 방식을 구분해 최근 글과 구성을 다양화. 질문형 시작은 강제하지 않음. 길이보다 완성도 우선.
- 최종 태그 규칙: 10~20개, 기본 15개. 주제와 관련된 인기·이슈 키워드 우선. 인기 측정 근거가 없으면 주제 기반 후보로 표시. 노출·계정 안전을 보장하지 않음.
- 썸네일·공통 시각 디자인·이미지 규격 지침은 아직 미정. 이번 설명용 이미지 디자인을 영구 브랜드 템플릿으로 확정한 것이 아님.

### 첫 글 준비 결과

- 제목: 「서울 6억 아파트, 현금은 얼마나 필요할까? LTV 40%로 계산해봤습니다」. 카테고리 부동산, A 정보 설명형.
- 담보가치 6억/LTV 40% 가정 → 대출 2.4억, 매매대금 자기자금 3.6억. 무주택자의 1주택 취득·전용 85㎡ 이하·과세표준 6억·감면/중과 미적용 조건에서 취득세/교육세 660만원, 중개보수 상한 240만원을 합쳐 3억6900만원. 부가세·등기·채권 할인·이사 등 별도. 실제 대출은 소득·부채·심사에 따라 달라짐.
- 2026-10-26 금융위원회, 서울시, 지방자치단체 공식 자료를 조사해 원고 작성. 후속 패키징에서는 재조사하지 않음. 나중에 재게시/수정할 때 최신 규정을 재확인할 것.
- 출처: https://www.fsc.go.kr/po020201/85466 ; https://fsc.go.kr/no010101/85824 ; https://land.seoul.go.kr/land/broker/brokerageCommission.do ; https://goheung.go.kr/contentsView.do?pageId=www527 .
- imagegen 스킬과 내장 image_gen으로 설명 이미지 2장 생성·시각 확인. ① 대출/자기자금 40:60 ② 자기자금+세금+보수/기타 비용 별도. 별도 API/CLI 결제 경로를 사용하지 않음.
- 첫 글 태그 15개: 서울아파트, 6억아파트, 아파트매매, 내집마련, 주택담보대출, 주담대, 대출규제, LTV, DSR, 스트레스DSR, 주택구입자금, 자기자금, 취득세, 부동산중개보수, 부동산정보. 실제 인기 순위/검색량은 미검증.
- **게시 여부 미확인. 사용자에게 네이버 새글창 붙여넣기·게시를 맡겼으며 게시 URL을 받지 않았다. 요청 커밋 메시지의 ‘첫 글 게시’는 실제 발행 성공의 증거가 아니다.**

### 결과 파일과 실행 방법

첫 글 폴더: `data/manual-blog/posts/2026-10-26-seoul-600m/` (위 로컬 프로젝트 기준).

| 파일 | 역할 |
|---|---|
| publish.html | 이미지 2장 내장 게시용 원고. 제목 복사 / 본문+이미지 복사 / 텍스트만 복사 / 본문 선택 버튼 |
| title.txt, body.txt | 제목·본문 별도. TXT에는 이미지 삽입 위치 표시 |
| images/01-loan-and-cash.png | 첫 계산표 뒤에 넣는 이미지 |
| images/02-purchase-costs.png | 부대비용 계산표 뒤에 넣는 이미지 |
| naver-first-post.zip | HTML·제목·본문·사용방법·이미지 2장, 총 6개 파일 |
| image-prompts.md | 실제 이미지 생성 프롬프트 |
| package-review.md | 검증/미확인 범위, 게시 준비 상태 |
| 사용방법.txt | 복사·이미지 첨부 방법 |

- 사용자는 publish.html을 브라우저로 열어 제목과 본문을 별도로 복사. 이미지가 빠지면 텍스트 복사 후 이미지 2장을 삽입하고 위치 표시 문구를 삭제. HTML 파일을 네이버에 업로드하는 방식이 아님.
- 실제 자료는 `data/` Git 제외 대상. **새 PC에서 clone만 하면 원고·이미지·ZIP은 복원되지 않는다.** 동일 PC의 다음 세션은 해당 폴더를 사용. 다른 PC로 옮길 때는 사용자가 로컬 첫 글 폴더 전체와 게시 기록을 별도로 복사해야 한다. ZIP만으로 프롬프트/내부 기록까지 복원되지는 않음.
- `data/manual-blog/POST_LOG.md`와 posts 폴더 준비. 로컬 POST_LOG는 초기 빈 양식이며 이후 Git 템플릿 확장 내용을 자동 덮어쓰지 않았다. 필요 필드를 추가해 사용. Git의 빈 양식은 docs/templates/POST_LOG.md, POST_BRIEF.md, OPERATIONS_REVIEW.md.
- 바탕화면 `C:\Users\케이지에프앤비\Desktop\HPL 블로그 운영.lnk` 생성, 대상 scripts/start_review.cmd, 작업 디렉터리 프로젝트 루트. 이 바로가기는 기존 앱 실행용이며 첫 글 HTML을 여는 바로가기는 아님.
- 기존 앱: scripts/start_review.cmd 실행 → http://127.0.0.1:8501 접속. 서버창 유지, Ctrl+C 종료. 현재 앱은 여전히 상품 연결·월수금·날짜당 한 편 제약. 새 운영 문서가 앱 기능으로 구현된 것은 아님.

### 검증과 남은 일

- 이번 세션 초반 unittest 28개 통과(23.095초), CLI --help 종료 코드 0. 제한 환경에서 한글 Python 경로 오류가 있어 승인된 일반 사용자 환경에서 실행. 이후 앱 코드/DB/의존성 변경 없음, 문서 편집마다 회귀 테스트를 반복하지 않음.
- 로컬 문서 링크, git diff --check, 실제 자료의 Git 제외 확인. HTML 이미지 2장 내장, TXT 위치 표시 2개, 제목/안내와 본문 분리, 금액·출처 보존, ZIP 6개 파일 확인. 최종 HTML/TXT/ZIP의 동일한 태그 15개 확인.
- 브라우저 복사 버튼 실행, 네이버 붙여넣기의 이미지/표/링크 유지, 실제 게시 결과는 미검증. 썸네일 지침·사진 방식의 실제 운영 시험·성과 기록은 남아 있음.
- 다음 세션은 먼저 실제 게시 여부/URL과 붙여넣기 불편을 확인한다. 완료된 경우에만 게시 기록과 20편 주기에 반영한다. 이후 다음 주제 또는 디자인 지침을 받아 이어간다. API 개발을 자동 재개하지 않는다.
- 사용자가 이번 작업의 Git commit/push를 명시 요청함. 정확한 메시지: `블로그 자동화  첫 글 게시` (자동화 뒤 공백 2개). 이후 전송 성공 여부는 Git 이력/원격 HEAD와 대조. 이 요청은 미래 작업의 무조건적인 push 허가가 아님.

다음 세션 시작 요청 예시: “sales_auto의 AGENTS.md와 HANDOFF.md 최상단을 읽고 수동 블로그 운영을 이어가줘. 첫 글 로컬 자료는 data/manual-blog/posts/2026-10-26-seoul-600m/에 있어.”

## 해시태그 운영 기준 변경 (2026-10-26)

- 사용자 요청에 따라 기존 3~5개를 10~20개(기본 15개)로 변경. 통합 편집 지침·글별 양식·AGENTS에 반영. 주제 관련 인기·이슈 키워드를 우선하되 실제 검색 관심 자료와 단순 후보를 구분.
- 첫 게시물 HTML·TXT·ZIP도 동일한 15개 태그로 갱신. 본문·이미지는 유지. 이번 태그는 주제 기반 후보이며 인기 순위·검색량을 조사한 결과가 아님. 네이버의 플랫폼 최대 입력 수를 확인했다는 의미가 아님.

## 첫 게시물 붙여넣기 자료 (2026-10-26)

- 사용자 요청에 따라 `data/manual-blog/posts/2026-10-26-seoul-600m/`에 publish.html, title.txt, body.txt, 사용방법.txt와 이미지 2장을 담은 naver-first-post.zip 준비. 실제 자료는 Git 제외 경로에 보관.
- HTML은 제목/본문 복사와 텍스트 복사·본문 선택을 제공하며 이미지 2장을 내장. TXT는 이미지 삽입 위치를 표시. 앞서 작성·확인한 조건부 LTV 계산 원고를 사용하고 이번에는 규정을 재조사하지 않음.
- 이미지 내장 수·TXT 위치 표시·본문과 안내 분리·금액·출처·ZIP 6개 파일·Git 제외 확인. 브라우저 버튼 실행 및 네이버 붙여넣기는 미검증. 사용자가 직접 붙여넣고 최종 확인·게시할 예정이며 게시 완료로 집계하지 않음.

## 최신 지침 통합: HPL 블로그 확장 (2026-10-26)

- 사용자 제공 운영 지침 v1.0을 `docs/BLOG_EDITORIAL_GUIDE.md` 통합 v1.1로 반영. 편집 규칙의 단일 기준으로 삼고 기존 수동 운영 안내의 중복 편집 절은 링크·기록 절차로 대체.
- 충돌 해결: 초기 발행 하루 1개 이하(이전 1~2편 대체), 자유 주제는 부동산·금융 중심의 20편 비중 관리와 병행. 자동 발굴·유형 선택·검증 보고서는 현재 수동 요청에 따른 대화 작업이며 API·앱 자동화가 아님.
- 20편 목표는 7/6/4/2/1. 주 카테고리 하나만 집계하며 부동산+금융은 완성 주기 12~14편 목표. 전체 주제 중복과 최근 최대 20편 상세 비교를 구분. A~F 유형과 기존 전개 방식은 목적/구성으로 통합.
- HPL 인스타그램 원본을 확장·최신 검증하되 별도 웹사이트 코드는 유지. 질문형 시작은 선택 사항이며 문체·분량·해시태그는 확정, 썸네일·시각 디자인·이미지 규격은 보류.
- 기존 두 기록 양식에 카테고리·주기·HPL 원본·검증 보고서·시간·발행 확인 방법 추가. OPERATIONS_REVIEW.md에 후보 점수·20편 집계·월별 성과 양식 추가. 실제 기록은 덮어쓰지 않음.
- 비공식 게시 자동화 검토 문구는 기존 저장소 원칙과 통합하여 공식 허용 수단·권한 확인 후 별도 설계로 한정. 현재 게시·예약은 사용자 직접 수행.
- 문서만 변경. 실제 HPL 원본 조사·포스팅 작성·이미지 생성·API 호출·게시·성과 수집·커밋·push는 수행하지 않음. 아래 수동 운영 전환 절의 편수·미정 양식 범위는 이 절로 대체된 과거 기록이다.

검증: `git diff --check` 통과, README·운영 안내·통합 편집 지침의 로컬 링크 존재 확인 통과. 현행 문서에서 이전 하루 2편 기준과 미정 본문 양식 표현을 검색해 충돌 여부 확인. 앱 코드·DB 변경이 없어 회귀 테스트는 반복하지 않음.

다음 작업: 썸네일·시각 지침과 첫 주제/HPL 원본 또는 사진 수령 후 통합 기준에 따라 작성. 직전 28개 회귀 테스트 결과를 이번 재실행 결과로 주장하지 않는다.

## 최신 운영 전환: 수동 작성·수동 게시 (2026-10-26)

- 사용자 확정: 자유 주제, 하루 기본 1편·최대 2편, Plus 이용 환경의 대화에서 수동으로 글·이미지 요청, 사용자 검토 후 네이버 직접 게시/예약. API·과금·공급자 결정은 후순위.
- AI 글쓰기와 사용자 사진+경험 메모 글쓰기 절차를 `docs/MANUAL_BLOG_WORKFLOW.md`에 추가. 이미지 수는 요청별 결정. 썸네일·공통 양식·이미지 규격은 다음 단계에서 사용자 지침을 받음.
- `docs/templates/POST_LOG.md`, `POST_BRIEF.md`에 게시 이력·구성·근거·이미지·수정 기록용 빈 양식 추가. 실제 자료는 기존 Git 제외 경로 `data/manual-blog/`에 보관. 자동 구성 검사·EXIF 제거·이미지 생성 기능을 구현한 것은 아님.
- AGENTS.md와 README.md 상단에 새 운영 방침을 명시하고 과거 구현·로드맵과 구분. SKILLS_USED.md에 이번 실제 사용 이력 추가.
- 앱/DB/의존성은 변경하지 않음. 상품 필수·월수금·날짜당 한 편 제약은 여전히 존재하므로 새 운영은 수동 기록으로 진행. 기존 운영 DB의 현재 내용은 이번에 조회하거나 변경하지 않음.
- 실제 원고·이미지·게시 URL은 생성하지 않음. 실제 자료를 받은 후 두 방식으로 한 편씩 운영 시험. API 호출·결제·네이버 게시·커밋·push 없음.

검증 및 로컬 준비:

- `data/manual-blog/posts/`와 빈 `data/manual-blog/POST_LOG.md`를 준비했으며 기존 파일은 덮어쓰지 않음.
- `git diff --check` 통과, README/운영 안내의 로컬 Markdown 링크 존재 확인 통과. `git check-ignore`로 게시 기록·원고·사진 경로 제외 확인.
- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`: 28개 통과 (23.095초). 임시 데이터 기반 기존 회귀 검증이며 실제 글 게시 시험은 아님.
- 제한된 실행 환경에서 Python 한글 경로 오류가 있어 승인된 일반 사용자 환경에서 테스트 실행. 문서·양식 변경을 위해 새 테스트나 의존성을 추가하지 않음.

다음 작업: 사용자 썸네일·공통 양식 지침 수령 → 첫 주제/사진/경험 메모로 작성 → 사용자 검토·직접 게시 → 최종 자료와 URL 기록. 향후 자동화는 반복 작업이 확인된 후 범위와 예산을 재결정.

아래 기록은 과거 구현 이력이며, 운영 우선순위와 다음 단계는 이 절이 기준이다.

## 최신 상태: 네이버 블로그 4주 운영 자동화 구현 (2026-10-13)

- SQLite v3에 `blog_settings`, `content_plans`를 추가. 운영 DB 이관 전 `data/pre-v3-d0e068465a174819aa1e7a5e871c04fe.sqlite3` 백업을 만들었고 기존 상품 3개를 보존함. DB·백업은 Git 제외 대상.
- 화면 메뉴: `이번 주 게시`, `콘텐츠 캘린더`, `상품 자료`, `원고 · 검토`, `블로그 설정`, `중복 경고`, `게시 이력`.
- 블로그명·실제 네이버 URL·생활가전/수납 주제·월수금 일정과 `정보성 운영 → 브랜드 커넥트 연동 → 쇼핑커넥트 링크 사용 가능` 단계를 저장할 수 있음.
- 초기 캘린더 버튼은 다음 월요일부터 월·수·금 4주, 총 12편을 생성함. 재실행은 중복 생성하지 않음. 실제 블로그 URL을 아직 전달받지 않아 운영 DB에는 블로그 설정과 계획을 임의 생성하지 않음.
- 각 계획에 제목 후보 3개, 글 구조, 확인할 사실, 이미지 체크리스트, 태그 후보를 템플릿으로 저장. 원고에는 `[미확인]`을 남겨 사람의 사실 확인 전 승인을 차단하며 사용 후기를 만들지 않음.
- 계획 상태는 `계획 → 자료 준비 → 초안 → 검토 → 승인 → 게시자료 생성 → URL 기록`. 이번 주 화면에는 승인 이후 항목만 표시. 준비/승인/게시 편수와 검토 완료부터 승인까지 평균 시간을 표시함.
- 같은 날짜 일정은 차단하며 같은 상품·키워드·제목과 높은 제목 유사도를 경고함.
- 정보성 계획은 상품에 제휴 링크가 있어도 링크와 고지문을 게시 패키지에서 제외함. 제휴 계획은 쇼핑커넥트 이용 가능 단계, 확인된 공식 쇼핑커넥트 링크, 고지문이 모두 있어야 검토·승인 가능.
- 게시 패키지는 제목, 본문, 조건부 고지·공식 링크, 출처와 확인 시각, 태그 후보, 이미지 체크리스트를 TXT로 만듦. 승인 전 내보내기 차단과 상품·링크·본문 수정 시 승인 해제는 유지됨.
- 실제 네이버 로그인·자동 게시·브라우저 매크로·CAPTCHA 처리·AI 호출·실적 추정은 없음. 사용자가 네이버에서 직접 게시한 뒤 개별 URL을 기록해야 완료됨.

검증:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\check_server.py
```

- unittest **28개 통과** (13.294초). 블로그 설정/12편 생성 UI, 템플릿, 일정 충돌, 중복 경고, 정보성 링크 제외, 제휴 조건, 승인/내보내기 차단, 수정 시 승인 해제, URL 기록을 포함함.
- Streamlit 임시 루프백 서버 `/_stcore/health` HTTP 200 확인 후 테스트 프로세스를 종료함. 운영 데이터는 서버 확인에 사용하지 않음.
- 기존 로봇청소기 AppTest 시나리오도 새 메뉴에서 **12개 항목 PASS**. 최신 격리 결과는 `data/robot-tests/20261013-062149-16fd980c`이며 운영 DB 해시는 실행 전후 동일함.
- 샌드박스 사용자 경로에서는 Python 사용자명 인코딩 문제로 AppTest가 멈춰 실제 Windows 사용자 환경에서 같은 프로젝트 가상환경으로 검증함.

다음 작업:

1. `블로그 설정`에서 실제 블로그명과 `https://blog.naver.com/<아이디>` 주소를 저장.
2. `콘텐츠 캘린더`에서 시작 월요일을 선택해 초기 12편 생성.
3. 첫 글의 상품 근거를 등록하고 템플릿 원고 연결 → 사실 확인/수정 → 검토/승인 → 게시자료 생성.
4. 사용자가 네이버에 한 편을 직접 게시하고 URL을 기록해 실제 파일럿을 완료.
5. 쇼핑커넥트 가입·연동이 실제 완료된 뒤 운영 단계를 변경하고, 새 제휴 계획부터 공식 링크를 사용.

## 저장소 인수인계 (2026-10-08)

- 사용자 지정 원격: https://github.com/splendidhm/sales_auto.git
- 전달 브랜치: `main`; 요청 커밋 메시지: `쇼핑커넥트 블로그 자동화`.
- 현재 기능·개발 규칙은 AGENTS.md, 실행 방법은 README.md, 실제 스킬/도구 사용 이력은 SKILLS_USED.md에 정리.
- 코드 검증 최신 기준: unittest 22개 통과와 로봇청소기 시나리오 12항목 PASS. 이번 문서·Git 정리는 기능 코드 변경이 없어 같은 테스트를 불필요하게 반복하지 않음.
- `.venv`, `.env`, DB, 로그, 백업, 내보낸 원고와 로컬 테스트 결과는 Git 제외. 아래 로컬 결과 경로는 이 PC에만 존재하며 clone에는 포함되지 않음. 재현 스크립트와 테스트 원고 텍스트는 소스에 포함.
- 새 환경: Python 3.12 이상으로 `.venv` 생성 → `.venv/Scripts/python.exe scripts/setup_local.py` → `pip install -r requirements-ui.txt` → unittest 실행 → `scripts/start_review.cmd` 실행. Python 절대 경로와 작업 디렉터리는 해당 PC에 맞게 설정.
- 로봇 사례 재현: `.venv/Scripts/python.exe scripts/test_robot_workflow.py`. 결과 폴더는 매 실행마다 새로 생성되므로 출력된 경로 사용.
- 아래 각 단계의 “Git 초기화·커밋·push 없음”은 해당 단계 당시의 과거 기록임. 이 전달의 실제 커밋·원격 반영 상태는 Git 이력과 최종 보고를 기준으로 확인.

## 최신 검증: 로봇청소기 사례 (2026-10-08)

- 사용자 요청으로 로보락 Qrevo L 후보의 상품 등록 → 원고 작성 → 검토·승인 → TXT 내보내기를 Streamlit AppTest로 실행. 검토자/승인자는 `Codex 테스트`, 제목과 본문에 테스트·게시 금지 표시.
- 판매 URL: `https://smartstore.naver.com/roborock/products/11548996873`. 직접 조회는 robots.txt로 제한됨. 현재 판매 여부·가격·사양을 확인한 것으로 처리하지 않았으며 일반 구매 전 질문으로 원고 작성. 제휴 링크란은 비워 두고 판매 URL은 자료 출처로 입력.
- 발견·수정 1: 상품 분류가 생활·수납용품으로 고정됨. 화면과 save_product에 분류 선택 추가, 생활가전·로봇청소기 지원. 기존 호출에서 category 생략 시 기존 상품 분류 보존, 신규 상품은 기존 기본값 유지. DB 스키마는 v2 유지.
- 발견·수정 2: 잘못된 URL 포트 문자열/범위가 저장되고 잘못된 대괄호 URL은 원시 ValueError로 처리됨. 저장 전 URL 구문과 포트를 검증하고 사용자용 ValidationError로 통일. 회귀 테스트로 수정 전 실패와 수정 후 통과 확인.
- 화면/TXT 비교에서 st.code가 마지막 줄바꿈 한 개를 생략하는 것을 확인. 본문 차이는 아니므로 테스트 비교에 표시 규칙만 반영.

실행 명령:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\test_robot_workflow.py
```

- 전체 회귀 테스트 **22개 통과** (7.514초).
- 로봇청소기 별도 시나리오 **12개 확인 항목 PASS**, 종료 코드 0. 잘못된 URL·검토 누락·미승인 내보내기·오래된 버전 저장 차단, 승인 후 본문/URL 변경 시 재검토, 재내보내기 파일 보존, UTF-8·화면 내용 확인 포함.
- 성공 결과 폴더: `data/robot-tests/20261008-020632-c4db345a`.
- 최종 원고: `exports/draft-1-3b29812c65974fe992a4110eed7d2358.txt` (위 폴더 기준).
- `result.json`, `result.md`에 결과 보관. 상품 ID 1, 원고 ID 1, 최종 버전 4, approved 상태, 게시 기록 0.
- 운영 DB SHA-256 실행 전후 동일. 운영 DB나 기존 내보내기는 수정하지 않았고 별도 테스트 DB·로그·원고를 보존.
- 브라우저 픽셀/스크린샷 검증은 하지 않음. 실제 Streamlit 스크립트의 폼·버튼·표시 내용은 AppTest로 검증. 실제 네이버 게시·구매·API 호출 없음.
- 변경: app.py, src/affiliate_hub/editorial.py, tests/test_editorial.py, scripts/test_robot_workflow.py, README.md, HANDOFF.md. Git 초기화·커밋·push 없음.

기본 작업실에서는 별도 테스트 데이터가 보이지 않는 것이 정상입니다. README의 테스트 데이터 열기 절차로 결과를 확인할 수 있습니다.

## 최신 상태: 2단계 구현 완료 (2026-10-08)

이 절이 현재 상태입니다. 아래 1단계 기록은 당시 검증 결과를 보존한 과거 이력입니다.

### 구현한 기능

- `app.py`: 로컬 Streamlit 화면. 상품 자료 / 원고·검토 / 게시 이력 메뉴.
- 실제 상품명·출처 URL·자료 확인 시각·확인된 사실·이미지 권한 근거·사용 경험 입력과 수정.
- 쇼핑커넥트 또는 쿠팡의 공식 발급 링크 직접 등록. 링크 없이 정보성 콘텐츠도 작성 가능.
- 원고 버전별 제목·본문·고지·상품 근거 스냅샷과 검토자·승인자 기록.
- `draft → reviewed → approved → published` 흐름. `published`는 사용자가 직접 게시했다고 기록한 상태이며 자동 발행 또는 온라인 확인을 뜻하지 않음.
- 상품/링크/원고 변경 시 `needs_recheck`로 바뀌고 승인 해제. 오래된 편집 창의 버전 충돌 차단.
- 미확인 표시, 확인되지 않은 이미지 권한, 제휴 고지 누락, 체크 항목 미완료 상태에서는 검토·승인 차단.
- 승인본 TXT 내보내기와 복사 화면. 기존 가상 원고는 게시 금지 Markdown 내보내기 유지.
- 네이버 개별 글 URL 기록. 모바일/쿼리 URL을 정규화하고 같은 기록의 반복 입력은 중복 생성하지 않음. 같은 원고의 새 승인 버전에는 기존 URL의 수정 게시 이력 기록 가능.
- 공식 API·AI·자동 발행·실적 수집은 미구현. 사용자 입력 사실이나 고지의 법률 적합성을 자동 검증하지 않음.

### 환경과 실행

- Python 3.14.3의 기존 프로젝트 가상환경 사용. Streamlit **1.65.0**과 종속 패키지 설치 완료.
- `scripts/start_review.cmd` 실행 후 브라우저에서 `http://127.0.0.1:8501` 접속. 종료는 실행 창에서 Ctrl+C.
- 루프백 접속만 허용하고 Streamlit 사용 통계 전송 비활성화. 원격 사용자 인증·공개 배포 기능 없음.
- 설치 재현: `.venv\Scripts\python.exe -m pip install -r requirements-ui.txt`. UI 의존성은 pyproject의 `ui` extra에도 명시.
- 실제 상품은 아직 입력하지 않음. 테스트에서는 임시 DB에만 시험 자료를 입력했으며 실제 계정 게시·API 호출·결제 없음.

### 데이터 보존과 구조

- 실제 프로젝트 DB를 SQLite **v2**로 전환 완료. 전환 직전 `data/pre-v2-<uuid>.sqlite3` 자동 백업 생성.
- 기존 상품 **3개**, 가상 초안 **1개**, 내보내기 기록 **1개** 보존. 실제 게시 기록 **0개**.
- 기존 `content_drafts`는 최초 원고 스냅샷을 보존. 실제 원고의 현재 상태/본문은 `editorial_state`와 `draft_revisions`가 기준. 기존 컬럼만 조회해 현재 상태를 판단하지 말 것.
- `product_profiles`, `affiliate_links`, `review_events`, `publication_records` 추가. 기존 exports에는 revision 컬럼만 추가.
- UI와 CLI가 같은 OS 잠금과 DB를 사용. UI 변경은 `Hub.mutate`의 트랜잭션과 작업 로그를 거침.
- 마이그레이션 백업은 정기 백업과 다름. 정기 보관·복원 UI·로그 정리는 여전히 후속 범위.

### 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m affiliate_hub.cli init-db
.\.venv\Scripts\python.exe -m affiliate_hub.cli status
.\.venv\Scripts\python.exe scripts\check_server.py
.\.venv\Scripts\python.exe -m pip check
```

- 전체 **20개 테스트 통과** (6.944초). 기존 10개 + 편집/마이그레이션 9개 + AppTest 화면 흐름 1개.
- AppTest에서 상품 등록 → 초안 → 수정 → 검토 → 승인 → 파일 준비 → 게시 URL 기록의 사용자 조작 검증. 실제 네이버 게시 시험은 하지 않음.
- v1 백업과 기존 데이터·내보낸 파일 보존, 마이그레이션 반복 실행, 외래키 무결성 검증.
- 승인 전 내보내기 차단, 자료 변경 후 승인 해제, 원고 이력 보존, 부적절한 URL·미확인 항목·누락 고지 차단 검증.
- 실제 DB CLI smoke: schema_version=2, 기존 자료 개수 유지, manual_publications=0.
- 패키지 점검: `No broken requirements found.`
- 서버 기동·종료 점검: `HTTP 200`과 `Temporary server stopped; production data untouched.` 확인, 종료 코드 0. 임시 서버는 종료했으며 상시 실행 중인 서버는 없음.
- pytest 자체 실행과 브라우저 스크린샷 검증은 수행하지 않음. 화면 행동은 Streamlit AppTest로 확인.

### 다음 단계

사용자가 실제 상품 근거와 원고를 입력해 흐름을 시험할 수 있습니다. 쇼핑커넥트 승인 전에는 링크 없는 정보성 글부터 준비합니다. 다음 개발은 3단계의 AI 초안·사용량/비용 제한이며, 실제 호출은 공급자·키·예산을 준비한 뒤 연결합니다. WordPress·쿠팡 API는 그 이후입니다.

변경 파일: app.py, .streamlit/config.toml, requirements-ui.txt, pyproject.toml, .gitignore, src/affiliate_hub의 migrations/editorial/publishing/service 및 기존 DB/CLI/content 모듈, scripts/start_review.cmd·check_server.py, tests/test_editorial.py·test_app.py, README.md·AGENTS.md·HANDOFF.md. 기존 HPL 프로젝트는 수정하지 않았습니다. Git 저장소 초기화·커밋·push도 하지 않았습니다.

## 이하: 1단계 완료 당시 기록

검증일: **2026-10-08 (한국 시간)**. 이 절의 미구현·다음 단계 표시는 1단계 종료 당시 상태입니다.

## 확정한 방향

- 쇼핑커넥트 우선, 쿠팡 파트너스 후속.
- 별도 네이버 생활·수납용품 블로그를 먼저 운영하고 WordPress는 검증 후 도입.
- 기존 HPL은 경제·데이터 브랜드로 유지. 로컬 HPL_auto는 Next.js와 코드 기반 기사 구조이며 CMS 발행 API는 발견되지 않았음. 라이브 배포와의 일치는 미확인.
- 네이버 블로그·쇼핑커넥트 준비 전, API 키 없음.
- 매일 15~30분 검토, 주 3편·4주 12편 운영 목표, 월 운영비 상한 5만원.
- Instagram, 무인 대량 발행, 클라우드 상시 실행은 초기 제외.

## 구현 완료 범위: 1단계

프로젝트: `C:\Users\케이지에프앤비\codex\projects\sales_auto`

| 구성 | 확인된 상태 |
|---|---|
| Python | 기존 설치 Python **3.14.3**, 프로젝트 `.venv` 생성 |
| Git | 최초 폴더는 Git 저장소 아님. 초기화·커밋·push 하지 않음 |
| 실행 구조 | `src/affiliate_hub`, 단일 CLI, 외부 런타임 패키지 불필요 |
| 데이터 | SQLite schema v1, 상품·작업 이력·초안·내보내기 기록 |
| 수집 | 명확히 가상 표시된 mock 상품 3개, 안정된 source ID, upsert |
| 초안 | 템플릿 기반, 가상 테스트·게시 금지 표시, 미확인 항목 포함 |
| 내보내기 | UTF-8 Markdown, 고유 파일명, 기존 파일 보존, 게시 처리 없음 |
| 운영 안전 | 프로세스 간 OS 잠금, 비정상 종료 이력 복구 표시, 구조화 로그, 오류 종료 코드 |
| 비밀정보 | 실제 키 없음. `.env` 자동 로딩 없음. 원시 예외·환경변수 로그 출력 안 함 |
| 테스트 | unittest 행동 테스트 **10개 통과**, pytest 호환. pytest 자체 실행은 하지 않음 |
| 작업 스케줄러 | 설정 가이드만 작성. 등록·예약 실행 검증 안 함 |

기존 Python 경로:
`C:\Users\케이지에프앤비\AppData\Local\Python\pythoncore-3.14-64\python.exe`

`py`, `python`은 PATH에서 찾지 못했으며, 설치 폴더가 도구 샌드박스에서 접근 제한되어 승인된 권한으로 가상환경 생성과 테스트를 수행했습니다. 일반 Windows 터미널에서도 문제가 생기면 위 경로 실행 권한부터 확인하세요.

`scripts/setup_local.py`는 프로젝트 가상환경의 `.pth`에 로컬 소스 경로를 등록했습니다. 인터넷 다운로드나 pip 설치는 하지 않았습니다. pyproject의 일반 패키지 설치 경로는 준비되어 있으나 별도 빌드·설치 검증하지 않았습니다.

## 실제 검증 명령과 결과

프로젝트 루트에서:

```powershell
.\.venv\Scripts\python.exe scripts\setup_local.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m affiliate_hub.cli init-db
.\.venv\Scripts\python.exe -m affiliate_hub.cli collect --provider mock
.\.venv\Scripts\python.exe -m affiliate_hub.cli collect --provider mock
.\.venv\Scripts\python.exe -m affiliate_hub.cli draft --product-id 1
.\.venv\Scripts\python.exe -m affiliate_hub.cli export --draft-id 1
.\.venv\Scripts\python.exe -m affiliate_hub.cli collect --simulate-failure
$LASTEXITCODE
.\.venv\Scripts\python.exe -m affiliate_hub.cli status
```

- 테스트: `Ran 10 tests ... OK` (3.486초).
- 첫 수집: `inserted=3, updated=0, total=3`.
- 두 번째: `inserted=0, updated=3, total=3`.
- 초안: `draft_id=1`, `status=draft`, `is_mock=true`.
- 내보내기: `published=false`, 초안 상태 유지.
- 결과 파일: `exports/draft-1-f85e86c3fa8e4d22a71b0d236f1b7b1d.md`.
- 실패 주입: `RuntimeError`, 종료 코드 **1**, 작업 ID **6**은 의도적인 테스트 실패 기록.
- 마지막 상태: 상품 3개, 초안 1개, 내보내기 1개, `publishing=not_implemented`, `performance=null`.
- 테스트는 임시 폴더와 한글·공백 경로, 다른 현재 디렉터리를 사용. 동시 실행 차단은 실제 별도 프로세스로 확인.

테스트 범위: 반복 수집, 기존 상품 수정과 ID 유지, 일부 저장 실패 시 롤백, 실패 코드·로그, 내보내기와 게시 구분, 기존 파일 보존, 잘못된 ID, 동시 실행 차단, 중단된 작업 표시, 미래 DB 버전 거부, 상대 home 경로 거부.

## 파일 및 사용법

- `README.md`: 설치, CLI, 데이터 경로, Windows 예약 작업 설정과 한계.
- `AGENTS.md`: 구현 규칙과 수정된 단계 순서.
- `pyproject.toml`, `.gitignore`, `.env.example`: 패키지 정의와 생성물·비밀정보 제외 규칙.
- `src/affiliate_hub/`: 설정, DB, 모델, mock provider, 템플릿, 잠금·로그, CLI.
- `tests/test_hub.py`: unittest/pytest 호환 행동 테스트.
- `scripts/setup_local.py`, `scripts/run_collect.cmd`: 네트워크 없는 소스 등록과 수집 실행.

`data/`, `logs/`, `exports/`, `.venv/`는 로컬 생성물입니다. Git 저장소가 없으므로 git status로 추적 제외 여부를 검증한 것으로 주장하지 않습니다.

## 미구현 사항과 다음 단계

현재 CLI는 mock만 지원합니다. 실제 상품 입력, 제휴 링크 저장, AI, 승인·수정 버전 관리, 네이버 게시 URL 기록, WordPress, 쿠팡 API, 성과 분석, 자동 백업·30일 보관, 로그 정리는 **후속 구현**입니다. 실제 게시·API 호출·결제·계정 가입은 전혀 수행하지 않았습니다.

강제 종료 시 내보내기 파일만 남고 DB 기록이 없을 수 있습니다. 다음 내보내기는 고유 이름을 사용합니다. 고아 파일 자동 정리는 미구현이며 사용자 메모를 임의 삭제하지 마세요. 자동 재시도는 없고 안전한 수집에 한해 Windows 예약 작업에서 설정합니다.

다음 구현은 **2단계**로 한정:

1. 수동 실제 상품·출처·확인 시각·이미지 권한·공식 발급 제휴 링크 등록.
2. 로컬 Streamlit 화면에서 입력·원고 수정·검토·승인. 변경 후 재검토 처리.
3. 네이버 게시 자료 내보내기와 사용자 게시 URL 기록. 공식 게시 수단이 확인되지 않으면 수동 게시 유지.
4. 실제 데이터와 가상 데이터를 분리하고 기존 SQLite v1 자료를 보존하는 마이그레이션 테스트.

쇼핑커넥트 가입 조건·사용 가능한 채널은 실제 가입 시 확인합니다. 공개 API를 확인하지 못했으므로 상품 검색 API를 제휴 링크 발급 API로 대체하지 않습니다. 가입이 지연돼도 정보성 글 작성은 진행할 수 있습니다.

이후 AI·쇼핑커넥트 운영, 별도 WordPress, 쿠팡 순으로 진행합니다. WordPress 도입 기준은 4주·12편 운영, 최근 2주 하루 검토 30분 이내, 월 총 5만원 이내입니다. 이는 내부 목표이며 서비스 가입 기준이 아닙니다.
