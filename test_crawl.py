import re
from datetime import datetime
from urllib.parse import quote
from playwright.sync_api import sync_playwright


def is_ongoing_or_upcoming(period_str: str) -> bool:
    if not period_str or period_str == "상세페이지 참조":
        return True

    try:
        if "~" in period_str:
            end_date_str = period_str.split("~")[1].strip()
        else:
            end_date_str = period_str

        digits = re.findall(r"\d+", end_date_str)
        if len(digits) >= 3:
            year, month, day = int(digits[0]), int(digits[1]), int(digits[2])
            end_date = datetime(year, month, day).date()
            today = datetime.now().date()

            # 종료일이 오늘보다 이전이면 False
            if end_date < today:
                return False
    except Exception:
        pass

    return True


def test_crawl(keyword: str = "서울"):
    encoded_keyword = quote(keyword)
    festivals_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # 1. 기본 검색 페이지 접속
        url = f"https://korean.visitkorea.or.kr/search/search_list.do?keyword={encoded_keyword}"
        print(f"1. 검색 페이지 접속: {keyword}")
        page.goto(url, wait_until="domcontentloaded")

        # 2. 팝업 제거
        print("2. 팝업 제거 처리...")
        page.wait_for_timeout(1500)
        try:
            page.locator("a:has-text('거절'), button:has-text('거절')").first.click(force=True, timeout=2000)
            print("-> 팝업 제거 완료")
        except Exception:
            pass

        # 3. [축제/공연/행사] 탭 클릭
        print("3. [축제/공연/행사] 탭 클릭 시도...")
        tab_btn = page.locator("button[role='tab']:has-text('축제/공연/행사')").first
        if tab_btn.is_visible():
            tab_btn.click(force=True)
        else:
            page.evaluate("""
                () => {
                    const btn = Array.from(document.querySelectorAll("button[role='tab']"))
                                     .find(b => b.textContent.includes('축제/공연/행사'));
                    if (btn) btn.click();
                }
            """)

        page.wait_for_timeout(2000)

        # 4. [최신순] 정렬 적용
        print("4. [최신순] 정렬 적용...")
        try:
            sort_dropdown = page.locator("button:has-text('관련도순')").first
            if sort_dropdown.is_visible():
                sort_dropdown.click(force=True)
                page.wait_for_timeout(500)
            
            latest_btn = page.locator("button[data-sort='FINAL_MODIFIED_DATE/DESC']").first
            if latest_btn.is_visible():
                latest_btn.click(force=True)
                print("-> 최신순 정렬 적용 완료!")
                page.wait_for_timeout(2000)
        except Exception as e:
            print(f"-> 정렬 변경 중 예외: {e}")

        # 5. 수집 루프 (지난 축제 등장 시 완전 종료)
        current_page = 1
        should_stop_all = False

        while not should_stop_all:
            print(f"\n--- [ {current_page} 페이지 수집 중 ] (누적 유효 축제: {len(festivals_data)}개) ---")
            
            try:
                page.wait_for_selector(".festival_list ul > li", timeout=5000)
            except Exception:
                print("-> 리스트 로딩 실패 또는 데이터 없음")
                break

            items = page.locator(".festival_list ul > li").all()

            for idx, item in enumerate(items):
                try:
                    title_elem = item.locator(".stit, strong").first
                    title = title_elem.inner_text().strip() if title_elem.count() > 0 else ""

                    if not title or "공공누리" in title:
                        continue

                    # 중복 체크
                    if any(f["title"] == title for f in festivals_data):
                        continue

                    date_elem = item.locator(".date").first
                    period = date_elem.inner_text().strip() if date_elem.count() > 0 else "상세페이지 참조"

                    loc_elem = item.locator(".area_wrap .area, .area").first
                    location = loc_elem.inner_text().strip() if loc_elem.count() > 0 else keyword

                    # 진행 여부 판단
                    ongoing = is_ongoing_or_upcoming(period)
                    print(f"[{len(festivals_data)+1}] 제목: {title} | 기간: {period} | 진행여부: {ongoing}")

                    # 📌 핵심: 최신순 정렬에서 지난 축제가 나오면 그 즉시 전체 프로세스 정지!
                    if not ongoing:
                        print("\n🛑 [종료 조건 감지] 이미 지난 축제가 발견되었습니다. 크롤링을 정지합니다.")
                        should_stop_all = True
                        break

                    festivals_data.append({"title": title, "period": period, "location": location})

                except Exception as e:
                    print(f"아이템 파싱 오류: {e}")

            if should_stop_all:
                break

            # 다음 페이지 이동
            current_page += 1
            next_page_btn = page.locator(f".page_links > a:has-text('{current_page}')").first
            
            if next_page_btn.is_visible():
                print(f"-> {current_page} 페이지 이동 버튼 클릭")
                next_page_btn.click(force=True)
                page.wait_for_timeout(2500)
            else:
                arrow_next = page.locator("a.page_navi.next").first
                if arrow_next.is_visible():
                    print("-> 다음 화살표(>) 버튼 클릭")
                    arrow_next.click(force=True)
                    page.wait_for_timeout(2500)
                else:
                    print("-> 다음 페이지가 없어 수집을 종료합니다.")
                    break

        print(f"\n==========================================")
        print(f"🎉 최종 수집 완료: 총 {len(festivals_data)}개의 유효 축제 수집")
        print(f"==========================================")
        page.wait_for_timeout(2000)
        browser.close()


if __name__ == "__main__":
    test_crawl("서울")