import re
from datetime import datetime

def is_ongoing_or_upcoming(period_str: str) -> bool:
    if not period_str or period_str == "상세페이지 참조":
        return True

    try:
        # 전체 문자열에서 연도(4자리 숫자로 시작하는 부분) 추출
        all_digits = re.findall(r"\d+", period_str)
        if len(all_digits) < 3:
            return True  # 날짜 수식이 부족하면 기본적으로 포함

        # 기본 연도 설정 (첫 번째 발견된 4자리 숫자, 없으면 현재 연도)
        base_year = int(all_digits[0]) if len(all_digits[0]) == 4 else datetime.now().year

        if "~" in period_str:
            end_part = period_str.split("~")[1].strip()
            end_digits = re.findall(r"\d+", end_part)
            
            if len(end_digits) == 3:  # YYYY.MM.DD
                year, month, day = int(end_digits[0]), int(end_digits[1]), int(end_digits[2])
            elif len(end_digits) == 2:  # MM.DD (연도 생략된 경우)
                year, month, day = base_year, int(end_digits[0]), int(end_digits[1])
            else:
                return True
        else:
            if len(all_digits) >= 3:
                year, month, day = int(all_digits[0]), int(all_digits[1]), int(all_digits[2])
            else:
                return True

        end_date = datetime(year, month, day).date()
        today = datetime.now().date()

        if end_date < today:
            return False

    except Exception:
        pass

    return True