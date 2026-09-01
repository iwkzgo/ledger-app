from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .aggregator import (
    EXPENSE_CATEGORIES,
    build_budget_status,
    build_monthly_summary,
    current_month,
)
from .categorizer import categorize_item, learn_category
from .extensions import db
from .models import Budget, Entry
from .recurring import sync_recurring_items
from .rules import (
    EXPENSE_CATEGORY_ORDER,
    FALLBACK_CATEGORY,
    FIXED_EXPENSE_CATEGORY,
    INCOME_CATEGORY,
    SAVINGS_CATEGORY,
)
from .text_parser import parse_amount, parse_entry

bp = Blueprint("ledger", __name__)

CATEGORY_CHOICES = [INCOME_CATEGORY, SAVINGS_CATEGORY] + EXPENSE_CATEGORY_ORDER


def flash_budget_warning(category: str) -> None:
    if category in (INCOME_CATEGORY, SAVINGS_CATEGORY):
        return
    for status in build_budget_status(current_user.id):
        if status["category"] != category:
            continue
        if status["level"] == "over":
            flash(
                f'⚠️ "{category}" 예산을 초과했습니다! '
                f'({status["spent"]:,}원 / {status["budget"]:,}원, {status["percent"]}%)',
                "danger",
            )
        elif status["level"] == "warning":
            flash(
                f'"{category}" 예산의 {status["percent"]}%를 사용했습니다. '
                f'({status["spent"]:,}원 / {status["budget"]:,}원)',
                "warning",
            )
        break


@bp.route("/")
@login_required
def index():
    recorded = sync_recurring_items(current_user.id)
    if recorded:
        flash("고정지출이 자동 기록되었습니다: " + ", ".join(recorded), "info")
        flash_budget_warning(FIXED_EXPENSE_CATEGORY)

    recent_entries = (
        Entry.query.filter_by(user_id=current_user.id)
        .order_by(Entry.id.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "index.html",
        summary=build_monthly_summary(current_user.id),
        categories=EXPENSE_CATEGORIES,
        recent_entries=recent_entries,
        category_choices=CATEGORY_CHOICES,
        budget_status=build_budget_status(current_user.id),
        current_month=current_month(),
    )


@bp.route("/entry", methods=["POST"])
@login_required
def create_entry():
    raw_text = request.form.get("raw_text", "").strip()
    if not raw_text:
        flash("입력할 내용이 없습니다.", "error")
        return redirect(url_for("ledger.index"))

    parsed = parse_entry(raw_text)
    if parsed is None:
        flash(f'"{raw_text}"에서 금액을 찾지 못했어요. 예: 스벅 5천원', "error")
        return redirect(url_for("ledger.index"))

    item, amount = parsed
    category = categorize_item(item, current_user.id)

    if category == FALLBACK_CATEGORY:
        return render_template(
            "confirm_category.html",
            raw_text=raw_text,
            item=item,
            amount=amount,
            categories=CATEGORY_CHOICES,
        )

    db.session.add(
        Entry(user_id=current_user.id, raw_text=raw_text, item=item, amount=amount, category=category)
    )
    db.session.commit()
    learn_category(item, category, current_user.id)
    flash(f'저장했습니다: {item} · {amount:,}원 · {category}', "success")
    flash_budget_warning(category)
    return redirect(url_for("ledger.index"))


@bp.route("/entry/confirm", methods=["POST"])
@login_required
def confirm_entry():
    raw_text = request.form.get("raw_text", "")
    item = request.form.get("item", "")
    amount = int(request.form.get("amount", "0"))
    category = request.form.get("category", FALLBACK_CATEGORY)

    db.session.add(
        Entry(user_id=current_user.id, raw_text=raw_text, item=item, amount=amount, category=category)
    )
    db.session.commit()
    learn_category(item, category, current_user.id)
    flash(f'저장했습니다: {item} · {amount:,}원 · {category}', "success")
    flash_budget_warning(category)
    return redirect(url_for("ledger.index"))


@bp.route("/entry/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    entry = Entry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash("삭제했습니다.", "info")
    return redirect(url_for("ledger.index"))


@bp.route("/entry/<int:entry_id>/category", methods=["POST"])
@login_required
def update_entry_category(entry_id):
    category = request.form.get("category", FALLBACK_CATEGORY)
    entry = Entry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    entry.category = category
    db.session.commit()
    learn_category(entry.item, category, current_user.id)
    flash(f'카테고리를 "{category}"(으)로 수정했습니다.', "info")
    return redirect(url_for("ledger.index"))


@bp.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets_page():
    if request.method == "POST":
        for category in EXPENSE_CATEGORY_ORDER:
            raw_value = request.form.get(f"budget__{category}", "").strip()
            amount = parse_amount(raw_value) or 0
            budget = Budget.query.filter_by(user_id=current_user.id, category=category).first()
            if budget is None:
                db.session.add(Budget(user_id=current_user.id, category=category, monthly_amount=amount))
            else:
                budget.monthly_amount = amount
        db.session.commit()
        flash("예산을 저장했습니다.", "success")
        return redirect(url_for("ledger.index"))

    budgets = {
        b.category: b.monthly_amount
        for b in Budget.query.filter_by(user_id=current_user.id).all()
    }
    return render_template("budgets.html", categories=EXPENSE_CATEGORY_ORDER, budgets=budgets)
