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


def _split_around(text: str, start: int, end: int) -> str:
    return (text[:start] + text[end:]).strip()


def parse_entry(raw_text: str) -> Optional[Tuple[str, int]]:
    """자유 텍스트에서 (항목, 금액)을 추출합니다. 금액을 찾지 못하면 None을 반환합니다."""
    text = raw_text.strip()
    if not text:
        return None

    # 1) 한글 단위 표현: "5천원", "3만원", "1만5천원"
    match = _UNIT_AMOUNT_RE.search(text)
    if match:
        amount = _sum_korean_units(match.group(1))
        item = _split_around(text, match.start(), match.end())
        if item and amount > 0:
            return item, amount

    # 2) 순수 숫자 표현: "1400원", "12,000원"
    match = _PLAIN_AMOUNT_RE.search(text)
    if match:
        amount = int(match.group(1).replace(",", ""))
        item = _split_around(text, match.start(), match.end())
        if item:
            return item, amount

    # 3) "원" 없이 끝자리 숫자만 있는 경우: "버스 1400"
    match = _TRAILING_DIGITS_RE.search(text)
    if match:
        amount = int(match.group(1))
        item = text[: match.start()].strip()
        if item:
            return item, amount

    return None
