import re
import uuid
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from app.services.parser import is_ongoing_or_upcoming


def run_festival_crawler(keyword: str = "서울", max_pages: int = 10) -> list[dict]:
    festivals_data = []
    encoded_keyword = quote(keyword)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--single-process",
                "--disable-gpu",
                "--no-zygote"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # 1. networkidle 대신 domcontentloaded 사용으로 타임아웃 방지
        url = f"https://korean.visitkorea.or.kr/search/search_list.do?keyword={encoded_keyword}"
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # 2. 팝업 거절 및 본문 요소 대기
        page.wait_for_timeout(1500)
        try:
            page.locator("a:has-text('거절'), button:has-text('거절')").first.click(force=True, timeout=2000)
        except Exception:
            pass

        # 3. [축제/공연/행사] 탭 클릭
        try:
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
        except Exception as e:
            print(f"Tab click failed: {e}")

        page.wait_for_timeout(2000)

        # 4. [최신순] 정렬 적용
        try:
            sort_dropdown = page.locator("button:has-text('관련도순')").first
            if sort_dropdown.is_visible():
                sort_dropdown.click(force=True)
                page.wait_for_timeout(500)

            latest_btn = page.locator("button[data-sort='FINAL_MODIFIED_DATE/DESC']").first
            if latest_btn.is_visible():
                latest_btn.click(force=True)
                page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Sort click failed: {e}")

        # 5. 페이징 및 수집 루프
        current_page = 1

        while current_page <= max_pages:
            try:
                # 리스트 아이템 요소가 실제로 화면에 뜰 때까지 대기
                page.wait_for_selector(".festival_list ul > li", timeout=10000)
                page.wait_for_timeout(1000)
            except Exception:
                break

            items = page.locator(".festival_list ul > li").all()

            for item in items:
                try:
                    title_elem = item.locator(".stit, strong").first
                    title = title_elem.inner_text().strip() if title_elem.count() > 0 else ""

                    if not title or "공공누리" in title:
                        continue

                    if any(f["title"] == title for f in festivals_data):
                        continue

                    date_elem = item.locator(".date").first
                    period = date_elem.inner_text().strip() if date_elem.count() > 0 else "상세페이지 참조"

                    if not is_ongoing_or_upcoming(period):
                        continue

                    loc_elem = item.locator(".area_wrap .area, .area").first
                    raw_location = loc_elem.inner_text().strip() if loc_elem.count() > 0 else keyword

                    img_elem = item.locator("img").first
                    image_url = img_elem.get_attribute("src") if img_elem.count() > 0 else ""

                    link_elem = item.locator("a").first
                    raw_detail_url = link_elem.get_attribute("href") if link_elem.count() > 0 else ""

                    full_detail_url = ""
                    if raw_detail_url:
                        uuid_match = re.search(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", raw_detail_url, re.IGNORECASE)
                        id_match = re.search(r"'([^']+)'", raw_detail_url)
                        extracted_id = id_match.group(1) if (id_match and id_match.group(1) != "searchResult") else ""

                        if uuid_match:
                            cotid = uuid_match.group(0)
                            full_detail_url = f"https://korean.visitkorea.or.kr/detail/fes_detail.do?cotid={cotid}"
                        elif extracted_id:
                            if extracted_id.isdigit():
                                full_detail_url = f"https://korean.visitkorea.or.kr/kfes/detail/fstvlDetail.do?cmsCntntsId={extracted_id}"
                            else:
                                full_detail_url = f"https://korean.visitkorea.or.kr/detail/fes_detail.do?cotid={extracted_id}"

                    festivals_data.append(
                        {
                            "id": str(uuid.uuid4()),
                            "title": title,
                            "period": period,
                            "location": raw_location,
                            "image_url": image_url or "",
                            "detail_url": full_detail_url,
                        }
                    )

                except Exception:
                    continue

            current_page += 1

            candidate_btns = page.locator("div.page_links a").filter(
                has_text=re.compile(rf"^\s*{current_page}\s*$")
            ).element_handles()

            clicked = False
            for btn in candidate_btns:
                if btn.is_visible():
                    btn.click(force=True)
                    clicked = True
                    page.wait_for_timeout(2500)
                    break

            if not clicked:
                arrow_next = page.locator("a.page_navi.next").first
                if arrow_next.is_visible():
                    arrow_next.click(force=True)
                    page.wait_for_timeout(2500)
                else:
                    break

        browser.close()

    return festivals_data