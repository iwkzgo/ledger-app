import calendar
from datetime import date, datetime
from typing import List

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .extensions import db
from .models import Entry, RecurringItem
from .rules import FIXED_EXPENSE_CATEGORY, INCOME_CATEGORY
from .text_parser import parse_amount, parse_entry

bp = Blueprint("recurring", __name__, url_prefix="/recurring")


def _last_day_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _next_month(year_month: str) -> str:
    year, month = map(int, year_month.split("-"))
    if month == 12:
        return f"{year + 1}-01"
    return f"{year}-{month + 1:02d}"


def sync_recurring_items(user_id: int) -> List[str]:
    """오늘 날짜 기준으로 아직 기록되지 않은 고정지출이 있으면 지금 기록하고,
    새로 기록된 항목에 대한 안내 메시지 목록을 반환합니다."""
    today = date.today()
    current_month = today.strftime("%Y-%m")
    messages: List[str] = []

    for recurring in RecurringItem.query.filter_by(user_id=user_id).all():
        month_cursor = (
            _next_month(recurring.last_recorded_month)
            if recurring.last_recorded_month
            else recurring.created_at.strftime("%Y-%m")
        )

        while month_cursor <= current_month:
            year, month = map(int, month_cursor.split("-"))
            day = min(recurring.day_of_month, _last_day_of_month(year, month))
            scheduled_date = date(year, month, day)

            if scheduled_date > today:
                break

            category = recurring.category or FIXED_EXPENSE_CATEGORY
            label = "고정수입" if category == INCOME_CATEGORY else "고정지출"
            db.session.add(
                Entry(
                    user_id=user_id,
                    created_at=datetime.combine(scheduled_date, datetime.min.time()),
                    raw_text=f"{recurring.item} {recurring.amount:,}원 ({label} 자동기록)",
                    item=recurring.item,
                    amount=recurring.amount,
                    category=category,
                )
            )
            recurring.last_recorded_month = month_cursor
            messages.append(f"{recurring.item} {recurring.amount:,}원 ({month_cursor})")

            month_cursor = _next_month(month_cursor)

    if messages:
        db.session.commit()

    return messages


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        raw_text = request.form.get("raw_text", "").strip()

        parsed = parse_entry(raw_text)
        if parsed is None:
            flash(f'"{raw_text}"에서 금액을 찾지 못했어요. 예: 월세 50만원', "error")
            return redirect(url_for("recurring.index"))

        item, amount = parsed
        day_raw = request.form.get("day_of_month", "1").strip()
        day = int(day_raw) if day_raw.isdigit() else 1
        day = max(1, min(day, 31))

        item_type = request.form.get("type", "expense").strip()
        category = INCOME_CATEGORY if item_type == "income" else FIXED_EXPENSE_CATEGORY
        label = "고정수입" if category == INCOME_CATEGORY else "고정지출"

        db.session.add(
            RecurringItem(
                user_id=current_user.id, item=item, amount=amount, day_of_month=day, category=category
            )
        )
        db.session.commit()
        flash(f'{label}으로 등록했습니다: {item} · {amount:,}원 · 매달 {day}일', "success")
        return redirect(url_for("recurring.index"))

    recurring_items = (
        RecurringItem.query.filter_by(user_id=current_user.id)
        .order_by(RecurringItem.day_of_month)
        .all()
    )
    return render_template(
        "recurring.html", recurring_items=recurring_items, INCOME_CATEGORY=INCOME_CATEGORY
    )


@bp.route("/<int:item_id>/edit", methods=["POST"])
@login_required
def edit(item_id):
    recurring = RecurringItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()

    amount = parse_amount(request.form.get("amount", "").strip())
    if amount is not None:
        recurring.amount = amount

    day_raw = request.form.get("day_of_month", "").strip()
    if day_raw.isdigit():
        recurring.day_of_month = max(1, min(int(day_raw), 31))

    db.session.commit()
    flash(f'"{recurring.item}" 정보를 수정했습니다.', "info")
    return redirect(url_for("recurring.index"))


@bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete(item_id):
    recurring = RecurringItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    label = "고정수입" if recurring.category == INCOME_CATEGORY else "고정지출"
    db.session.delete(recurring)
    db.session.commit()
    flash(f"{label} 등록을 삭제했습니다.", "info")
    return redirect(url_for("recurring.index"))
