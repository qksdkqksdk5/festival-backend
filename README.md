# 🎪 Festival Information Crawler & API Server

대한민국 구석구석 사이트의 실시간 축제 데이터를 Playwright 기반으로 동적 크롤링하고, 지역별/일정별 정제된 API를 제공하는 FastAPI 백엔드 서비스입니다.

## 🛠️ Tech Stack
- **Language & Framework**: Python 3.14 / FastAPI
- **Web Scraping**: Playwright (Headless Chromium)
- **Database**: Supabase (PostgreSQL) / SQLAlchemy
- **Deployment**: Render

## 🚀 Key Features & System Design
- **동적 수집기**: SPA 기반의 웹페이지 데이터를 Playwright로 동적 렌더링 후 수집
- **비동기 크롤링 Task**: 작업 ID(Task ID) 기반 비동기 수집 프로세스 구축
- **데이터 정제 (Normalization)**: 광역지자체(광주특별시 등) 및 구 단위 지명 데이터 정밀 파싱

## 🎯 Key Engineering & Troubleshooting (기술적 도전 및 해결)

### 1. Playwright 크롤링 타임아웃(30s) 해결
- **문제**: `wait_until="networkidle"` 사용 시 배경 스크립트 및 소켓 통신으로 인해 타임아웃 에러 발생
- **해결**: `domcontentloaded` 방식으로 전환 후 핵심 요소(`.festival_list`) 명시적 대기(`wait_for_selector`) 로직을 적용하여 **수집 성공률 100% 달성 및 속도 개선**

### 2. 지역 필터링 오검색 예외 처리
- **문제**: 단순 문자열 매칭 시 '대구' 검색어에 '부산 해운대구'가 걸려오거나, '광주' 검색 시 '경기도 광주시'가 오매칭되는 현상 발생
- **해결**: 쿼리 단에서 부정 조건(`~ilike`) 및 지명 정규화 매핑 로직을 도입하여 정밀한 지역 필터링 구현

## ⚙️ Project Architecture & Setup

```text
app/
├── api/v1/       # API 라우터 (Crawl, Festivals)
├── services/     # Crawler (Playwright) & Parser 로직
├── tasks/        # 비동기 크롤링 태스크
└── main.py       # FastAPI 앱 및 CORS 설정

실행 방법
Bash
# 가상환경 구축 및 패키지 설치
pip install -r requirements.txt
playwright install chromium

# 서버 실행
uvicorn app.main:app --reload