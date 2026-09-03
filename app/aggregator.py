import calendar as pycalendar
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .categories import get_expense_categories
from .chart import build_donut_segments
from .models import Budget, Entry, SavingsGoal
from .rules import INCOME_CATEGORY, SAVINGS_CATEGORY
from .timeutil import KST_OFFSET, to_kst

WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]

WARNING_THRESHOLD = 80
OVER_THRESHOLD = 100


def current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def build_monthly_summary(user_id: int) -> List[Dict]:
    monthly = defaultdict(
        lambda: {"income": 0, "savings": 0, "expense_total": 0, "categories": defaultdict(int)}
    )

    entries = Entry.query.filter_by(user_id=user_id).all()
    for entry in entries:
        month = entry.created_at.strftime("%Y-%m")
        category = entry.category
        amount = entry.amount

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
            for category in get_expense_categories(user_id)
            if category in categories
        }
        income_breakdown = {
            item["item"]: item["amount"]
            for item in build_category_breakdown(user_id, INCOME_CATEGORY, month)
        }
        savings_breakdown = {
            item["item"]: item["amount"]
            for item in build_category_breakdown(user_id, SAVINGS_CATEGORY, month)
        }

        expense_slices = build_donut_segments(ordered_categories)
        for slice_info in expense_slices:
            slice_info["breakdown"] = build_category_breakdown(user_id, slice_info["category"], month)

        summary.append(
            {
                "month": month,
                "income": data["income"],
                "savings": data["savings"],
                "expense_total": data["expense_total"],
                "remaining": data["income"] - data["expense_total"] - data["savings"],
                "categories": categories,
                "income_slices": build_donut_segments(income_breakdown),
                "expense_slices": expense_slices,
                "savings_slices": build_donut_segments(savings_breakdown),
                "savings_goal": build_savings_goal_status(user_id, month),
            }
        )

    for i, row in enumerate(summary):
        if i == 0:
            row["expense_comparison"] = None
            continue

        previous_total = summary[i - 1]["expense_total"]
        current_total = row["expense_total"]
        diff = current_total - previous_total

        if diff == 0:
            direction = "same"
        elif diff > 0:
            direction = "up"
        else:
            direction = "down"

        percent = round(abs(diff) / previous_total * 100, 1) if previous_total > 0 else None

        row["expense_comparison"] = {"diff": diff, "percent": percent, "direction": direction}

    return summary


def build_today_summary(user_id: int) -> Dict:
    """오늘(KST) 하루 지출 합계를 계산합니다."""
    today = to_kst(datetime.now()).date()
    range_start = datetime.combine(today, datetime.min.time()) - KST_OFFSET
    range_end = range_start + timedelta(days=1)

    entries = Entry.query.filter(
        Entry.user_id == user_id,
        Entry.created_at >= range_start,
        Entry.created_at < range_end,
    ).all()

    total = 0
    count = 0
    for entry in entries:
        if entry.category in (INCOME_CATEGORY, SAVINGS_CATEGORY):
            continue
        total += entry.amount
        count += 1

    return {"date": today.strftime("%m-%d"), "total": total, "count": count}


def build_weekly_pattern(user_id: int) -> List[Dict]:
    """이번 주(월~일) 요일별 지출 합계를 KST 기준으로 계산합니다."""
    today = to_kst(datetime.now()).date()
    monday = today - timedelta(days=today.weekday())
    week_dates = [monday + timedelta(days=offset) for offset in range(7)]

    range_start = datetime.combine(monday, datetime.min.time()) - KST_OFFSET
    range_end = range_start + timedelta(days=7)

    totals = {day: 0 for day in week_dates}
    category_totals = {day: defaultdict(int) for day in week_dates}
    entries = Entry.query.filter(
        Entry.user_id == user_id,
        Entry.created_at >= range_start,
        Entry.created_at < range_end,
    ).all()
    for entry in entries:
        if entry.category in (INCOME_CATEGORY, SAVINGS_CATEGORY):
            continue
        day = to_kst(entry.created_at).date()
        if day in totals:
            totals[day] += entry.amount
            category_totals[day][entry.category] += entry.amount

    return [
        {
            "date": day.strftime("%m-%d"),
            "label": WEEKDAY_LABELS[index],
            "amount": totals[day],
            "is_today": day == today,
            "categories": dict(
                sorted(category_totals[day].items(), key=lambda kv: kv[1], reverse=True)
            ),
        }
        for index, day in enumerate(week_dates)
    ]


def build_calendar_month(user_id: int, month: str) -> Dict:
    """해당 월의 달력을 일요일 시작으로 구성하고, 날짜별 지출/수입 합계를 계산합니다."""
    year, mon = map(int, month.split("-"))
    weeks_of_dates = pycalendar.Calendar(firstweekday=6).monthdatescalendar(year, mon)

    range_start_date = weeks_of_dates[0][0]
    range_end_date = weeks_of_dates[-1][-1] + timedelta(days=1)
    range_start = datetime.combine(range_start_date, datetime.min.time()) - KST_OFFSET
    range_end = datetime.combine(range_end_date, datetime.min.time()) - KST_OFFSET

    daily_expense: Dict = defaultdict(int)
    daily_income: Dict = defaultdict(int)
    entries = Entry.query.filter(
        Entry.user_id == user_id,
        Entry.created_at >= range_start,
        Entry.created_at < range_end,
    ).all()
    for entry in entries:
        day = to_kst(entry.created_at).date()
        if entry.category == INCOME_CATEGORY:
            daily_income[day] += entry.amount
        elif entry.category == SAVINGS_CATEGORY:
            continue
        else:
            daily_expense[day] += entry.amount

    today = to_kst(datetime.now()).date()
    weeks = [
        [
            {
                "day": day.day,
                "in_month": day.month == mon,
                "is_today": day == today,
                "expense": daily_expense.get(day, 0),
                "income": daily_income.get(day, 0),
            }
            for day in week
        ]
        for week in weeks_of_dates
    ]

    prev_month_date = datetime(year, mon, 1) - timedelta(days=1)
    next_month_date = datetime(year, mon, pycalendar.monthrange(year, mon)[1]) + timedelta(days=1)

    total_expense = sum(amount for day, amount in daily_expense.items() if day.month == mon)
    total_income = sum(amount for day, amount in daily_income.items() if day.month == mon)

    return {
        "month": month,
        "weeks": weeks,
        "total_expense": total_expense,
        "total_income": total_income,
        "prev_month": prev_month_date.strftime("%Y-%m"),
        "next_month": next_month_date.strftime("%Y-%m"),
    }


def _savings_total_for_month(user_id: int, month: str) -> int:
    total = 0
    for entry in Entry.query.filter_by(user_id=user_id, category=SAVINGS_CATEGORY).all():
        if entry.created_at.strftime("%Y-%m") == month:
            total += entry.amount
    return total


def build_savings_goal_status(user_id: int, month: Optional[str] = None) -> Optional[Dict]:
    """해당 달에 "저축" 카테고리로 실제 기록한 금액이 목표 대비 얼마나 되는지 계산합니다.
    목표가 없으면 None을 반환합니다."""
    month = month or current_month()
    goal = SavingsGoal.query.filter_by(user_id=user_id, month=month).first()
    if goal is None or goal.target_amount <= 0:
        return None

    saved = _savings_total_for_month(user_id, month)
    percent = round(saved / goal.target_amount * 100, 1)
    achieved = saved >= goal.target_amount
    level = "achieved" if achieved else "progress"

    return {
        "month": month,
        "target": goal.target_amount,
        "saved": saved,
        "percent": percent,
        "achieved": achieved,
        "level": level,
    }


def _category_totals_for_month(user_id: int, month: str) -> Dict[str, int]:
    totals: Dict[str, int] = defaultdict(int)
    entries = Entry.query.filter_by(user_id=user_id).all()
    for entry in entries:
        if entry.created_at.strftime("%Y-%m") != month:
            continue
        if entry.category in (INCOME_CATEGORY, SAVINGS_CATEGORY):
            continue
        totals[entry.category] += entry.amount
    return dict(totals)


def build_category_breakdown(user_id: int, category: str, month: Optional[str] = None) -> List[Dict]:
    """해당 달, 해당 카테고리의 지출을 항목명 기준으로 합산해서 많이 쓴 순으로 반환합니다."""
    month = month or current_month()
    totals: Dict[str, Dict[str, int]] = {}
    entries = Entry.query.filter_by(user_id=user_id, category=category).all()
    for entry in entries:
        if entry.created_at.strftime("%Y-%m") != month:
            continue
        info = totals.setdefault(entry.item, {"count": 0, "amount": 0})
        info["count"] += 1
        info["amount"] += entry.amount

    return [
        {"item": item, "amount": info["amount"], "count": info["count"]}
        for item, info in sorted(totals.items(), key=lambda kv: kv[1]["amount"], reverse=True)
    ]


def build_budget_status(user_id: int, month: Optional[str] = None) -> List[Dict]:
    """설정된 예산이 있는 카테고리에 대해 이번 달 사용률을 계산합니다."""
    month = month or current_month()
    budgets = {b.category: b.monthly_amount for b in Budget.query.filter_by(user_id=user_id).all()}
    totals = _category_totals_for_month(user_id, month)

    status = []
    for category in get_expense_categories(user_id):
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
                "breakdown": build_category_breakdown(user_id, category, month),
            }
        )
    return status


def build_expense_forecast(user_id: int) -> Optional[Dict]:
    """이번 달 지금까지의 지출 속도를 기준으로 월말 예상 총 지출을 계산합니다."""
    today = to_kst(datetime.now()).date()
    days_in_month = pycalendar.monthrange(today.year, today.month)[1]
    days_elapsed = today.day
    month = today.strftime("%Y-%m")

    month_start_date = today.replace(day=1)
    if today.month == 12:
        next_month_date = month_start_date.replace(year=today.year + 1, month=1)
    else:
        next_month_date = month_start_date.replace(month=today.month + 1)
    range_start = datetime.combine(month_start_date, datetime.min.time()) - KST_OFFSET
    range_end = datetime.combine(next_month_date, datetime.min.time()) - KST_OFFSET

    totals: Dict[str, int] = defaultdict(int)
    entries = Entry.query.filter(
        Entry.user_id == user_id,
        Entry.created_at >= range_start,
        Entry.created_at < range_end,
    ).all()
    for entry in entries:
        if entry.category in (INCOME_CATEGORY, SAVINGS_CATEGORY):
            continue
        totals[entry.category] += entry.amount

    current_total = sum(totals.values())
    if current_total <= 0:
        return None

    daily_average = current_total / days_elapsed
    projected_total = round(daily_average * days_in_month)

    total_budget = sum(b.monthly_amount for b in Budget.query.filter_by(user_id=user_id).all())

    return {
        "current_total": current_total,
        "projected_total": projected_total,
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
        "total_budget": total_budget,
        "over_budget": total_budget > 0 and projected_total > total_budget,
    }
