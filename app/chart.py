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


LINE_CHART_WIDTH = 320
LINE_CHART_HEIGHT = 120
LINE_CHART_PADDING = 12


def build_line_chart(daily_totals: List[Dict]) -> Dict:
    """요일별 지출 목록을 받아 꺾은선 그래프용 좌표를 계산합니다."""
    amounts = [day["amount"] for day in daily_totals]
    max_amount = max(amounts) if max(amounts, default=0) > 0 else 1
    count = len(daily_totals)
    usable_width = LINE_CHART_WIDTH - 2 * LINE_CHART_PADDING
    usable_height = LINE_CHART_HEIGHT - 2 * LINE_CHART_PADDING

    dots = []
    for index, day in enumerate(daily_totals):
        x = LINE_CHART_PADDING + (usable_width * index / (count - 1) if count > 1 else 0)
        y = LINE_CHART_PADDING + usable_height * (1 - day["amount"] / max_amount)
        dots.append(
            {
                "x": round(x, 1),
                "y": round(y, 1),
                "label": day["label"],
                "amount": day["amount"],
                "is_today": day["is_today"],
            }
        )

    points = " ".join(f'{dot["x"]},{dot["y"]}' for dot in dots)

    return {
        "width": LINE_CHART_WIDTH,
        "height": LINE_CHART_HEIGHT,
        "points": points,
        "dots": dots,
    }


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
