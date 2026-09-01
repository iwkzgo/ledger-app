import math
from typing import Dict, List

_PALETTE = [
    "#4C6FFF", "#22C55E", "#F59E0B", "#EF4444",
    "#8B5CF6", "#06B6D4", "#EC4899", "#84CC16",
]

# SVG viewBox는 항상 0 0 160 160 기준으로 그립니다.
RADIUS = 60
STROKE_WIDTH = 26
CIRCUMFERENCE = 2 * math.pi * RADIUS


def build_donut_segments(categories: Dict[str, int]) -> List[Dict]:
    """카테고리별 금액을 받아 도넛(링) 차트용 SVG stroke 세그먼트 목록을 만듭니다."""
    total = sum(value for value in categories.values() if value > 0)
    if total <= 0:
        return []

    segments = []
    offset = 0.0

    for index, (category, value) in enumerate(categories.items()):
        if value <= 0:
            continue

        fraction = value / total
        length = fraction * CIRCUMFERENCE
        color = _PALETTE[index % len(_PALETTE)]

        segments.append(
            {
                "category": category,
                "value": value,
                "percent": round(fraction * 100, 1),
                "color": color,
                "dasharray": f"{length} {CIRCUMFERENCE - length}",
                "dashoffset": -offset,
            }
        )
        offset += length

    return segments
