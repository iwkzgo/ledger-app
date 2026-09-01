import math
from typing import Dict, List

_PALETTE = [
    "#4C6FFF", "#22C55E", "#F59E0B", "#EF4444",
    "#8B5CF6", "#06B6D4", "#EC4899", "#84CC16",
]


def _point_on_circle(cx: float, cy: float, r: float, angle_deg: float):
    angle_rad = math.radians(angle_deg - 90)
    return cx + r * math.cos(angle_rad), cy + r * math.sin(angle_rad)


def build_pie_slices(categories: Dict[str, int], size: int = 160) -> List[Dict]:
    """카테고리별 금액을 받아 SVG path로 그릴 수 있는 파이 조각 목록을 만듭니다."""
    total = sum(value for value in categories.values() if value > 0)
    if total <= 0:
        return []

    cx = cy = size / 2
    r = size / 2 - 4
    start_angle = 0.0
    slices = []

    for index, (category, value) in enumerate(categories.items()):
        if value <= 0:
            continue

        fraction = value / total
        end_angle = start_angle + fraction * 360
        color = _PALETTE[index % len(_PALETTE)]

        if fraction >= 0.999:
            # 카테고리가 하나뿐이면 원 전체를 두 개의 반원 호로 그립니다.
            path = (
                f"M {cx - r} {cy} "
                f"A {r} {r} 0 1 1 {cx + r} {cy} "
                f"A {r} {r} 0 1 1 {cx - r} {cy} Z"
            )
        else:
            x1, y1 = _point_on_circle(cx, cy, r, start_angle)
            x2, y2 = _point_on_circle(cx, cy, r, end_angle)
            large_arc = 1 if (end_angle - start_angle) > 180 else 0
            path = f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z"

        slices.append(
            {
                "category": category,
                "value": value,
                "percent": round(fraction * 100, 1),
                "path": path,
                "color": color,
            }
        )
        start_angle = end_angle

    return slices
