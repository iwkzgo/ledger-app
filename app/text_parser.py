import re
from typing import Optional, Tuple

_UNIT_VALUES = {"만": 10000, "천": 1000, "백": 100}
# 숫자 없이 단위만 있는 경우("천원" = 1천원)도 인식하도록 숫자는 선택 사항으로 둡니다.
_UNIT_AMOUNT_RE = re.compile(r"((?:\d*\s*(?:만|천|백)\s*)+)원?")
_PLAIN_AMOUNT_RE = re.compile(r"([\d,]+)\s*원")
_TRAILING_DIGITS_RE = re.compile(r"(\d+)\s*$")


def _sum_korean_units(chunk: str) -> int:
    total = 0
    for number, unit in re.findall(r"(\d*)\s*(만|천|백)", chunk):
        count = int(number) if number else 1
        total += count * _UNIT_VALUES[unit]
    return total


def _find_amount(text: str) -> Optional[Tuple[int, int, int]]:
    """텍스트에서 금액을 찾아 (금액, 시작 위치, 끝 위치)를 반환합니다. 못 찾으면 None."""
    # 1) 한글 단위 표현: "5천원", "3만원", "1만5천원"
    match = _UNIT_AMOUNT_RE.search(text)
    if match:
        amount = _sum_korean_units(match.group(1))
        if amount > 0:
            return amount, match.start(), match.end()

    # 2) 순수 숫자 표현: "1400원", "12,000원"
    match = _PLAIN_AMOUNT_RE.search(text)
    if match:
        amount = int(match.group(1).replace(",", ""))
        return amount, match.start(), match.end()

    # 3) "원" 없이 끝자리 숫자만 있는 경우: "버스 1400"
    match = _TRAILING_DIGITS_RE.search(text)
    if match:
        amount = int(match.group(1))
        return amount, match.start(), match.end()

    return None


def parse_amount(text: str) -> Optional[int]:
    """텍스트에서 금액만 추출합니다. 예산 입력처럼 항목명이 필요 없을 때 사용합니다."""
    text = text.strip()
    if not text:
        return None
    found = _find_amount(text)
    return found[0] if found else None


def parse_entry(raw_text: str) -> Optional[Tuple[str, int]]:
    """자유 텍스트에서 (항목, 금액)을 추출합니다. 항목 또는 금액을 찾지 못하면 None을 반환합니다."""
    text = raw_text.strip()
    if not text:
        return None

    found = _find_amount(text)
    if found is None:
        return None

    amount, start, end = found
    item = (text[:start] + text[end:]).strip()
    if not item:
        return None
    return item, amount
