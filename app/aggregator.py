from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from . import db
from .chart import build_pie_slices
from .rules import EXPENSE_CATEGORY_ORDER, INCOME_CATEGORY, SAVINGS_CATEGORY

EXPENSE_CATEGORIES = EXPENSE_CATEGORY_ORDER

WARNING_THRESHOLD = 80
OVER_THRESHOLD = 100


def current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def build_monthly_summary() -> List[Dict]:
    monthly = defaultdict(
        lambda: {
            "income": 0,
            "savings": 0,
            "expense_total": 0,
            "categories": defaultdict(int),
        }
    )

    for entry in db.fetch_all_entries():
        month = entry["created_at"][:7]  # "YYYY-MM-DDTHH:MM:SS" -> "YYYY-MM"
        category = entry["category"]
        amount = entry["amount"]

        if category == INCOME_CATEGORY:
            monthly[month]["income"] += amount
        elif category == SAVINGS_CATEGORY:
            monthly[month]["savings"] += amount
        else:
            monthly[month]["expense_total"] += amount
            monthly[month]["categories"][category] += amount

    summary = []
    for month in sorted(monthly.keys()):
        data = monthly[month]
        categories = dict(data["categories"])
        # 카테고리 순서를 고정해서 파이 조각 색이 월마다 같은 카테고리에 일관되게 붙도록 합니다.
        ordered_categories = {
            category: categories[category]
            for category in EXPENSE_CATEGORY_ORDER
            if category in categories
        }
        summary.append(
            {
                "month": month,
                "income": data["income"],
                "savings": data["savings"],
                "expense_total": data["expense_total"],
                "remaining": data["income"] - data["expense_total"] - data["savings"],
                "categories": categories,
                "pie_slices": build_pie_slices(ordered_categories),
            }
        )
    return summary


def _category_totals_for_month(month: str) -> Dict[str, int]:
    totals: Dict[str, int] = defaultdict(int)
    for entry in db.fetch_all_entries():
        if entry["created_at"][:7] != month:
            continue
        if entry["category"] in (INCOME_CATEGORY, SAVINGS_CATEGORY):
            continue
        totals[entry["category"]] += entry["amount"]
    return dict(totals)


def build_category_breakdown(category: str, month: str = None) -> List[Dict]:
    """해당 달, 해당 카테고리의 지출을 항목명 기준으로 합산해서 많이 쓴 순으로 반환합니다."""
    month = month or current_month()
    totals: Dict[str, Dict[str, int]] = {}
    for entry in db.fetch_all_entries():
        if entry["created_at"][:7] != month or entry["category"] != category:
            continue
        info = totals.setdefault(entry["item"], {"count": 0, "amount": 0})
        info["count"] += 1
        info["amount"] += entry["amount"]

    return [
        {"item": item, "amount": info["amount"], "count": info["count"]}
        for item, info in sorted(totals.items(), key=lambda kv: kv[1]["amount"], reverse=True)
    ]


def build_budget_status(month: str = None) -> List[Dict]:
    """설정된 예산이 있는 카테고리에 대해 이번 달 사용률을 계산합니다."""
    month = month or current_month()
    budgets = db.get_budgets()
    totals = _category_totals_for_month(month)

    status = []
    for category in EXPENSE_CATEGORY_ORDER:
        budget = budgets.get(category, 0)
        if budget <= 0:
            continue

        spent = totals.get(category, 0)
        percent = round(spent / budget * 100, 1)

        if percent >= OVER_THRESHOLD:
            level = "over"
        elif percent >= WARNING_THRESHOLD:
            level = "warning"
        else:
            level = "ok"

        status.append(
            {
                "category": category,
                "budget": budget,
                "spent": spent,
                "percent": percent,
                "level": level,
                "breakdown": build_category_breakdown(category, month),
            }
        )
    return status
