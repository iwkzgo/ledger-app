from flask import Flask, flash, redirect, render_template, request, url_for

from app import db
from app.aggregator import (
    EXPENSE_CATEGORIES,
    build_budget_status,
    build_monthly_summary,
    current_month,
)
from app.categorizer import categorize_item, learn_category
from app.rules import (
    EXPENSE_CATEGORY_ORDER,
    FALLBACK_CATEGORY,
    INCOME_CATEGORY,
    SAVINGS_CATEGORY,
)
from app.text_parser import parse_amount, parse_entry

app = Flask(__name__)
app.secret_key = "local-dev-only"

db.init_db()

CATEGORY_CHOICES = [INCOME_CATEGORY, SAVINGS_CATEGORY] + EXPENSE_CATEGORY_ORDER


def flash_budget_warning(category: str) -> None:
    if category in (INCOME_CATEGORY, SAVINGS_CATEGORY):
        return
    for status in build_budget_status():
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


@app.route("/")
def index():
    return render_template(
        "index.html",
        summary=build_monthly_summary(),
        categories=EXPENSE_CATEGORIES,
        recent_entries=db.fetch_recent_entries(),
        category_choices=CATEGORY_CHOICES,
        budget_status=build_budget_status(),
        current_month=current_month(),
    )


@app.route("/entry", methods=["POST"])
def create_entry():
    raw_text = request.form.get("raw_text", "").strip()
    if not raw_text:
        flash("입력할 내용이 없습니다.", "error")
        return redirect(url_for("index"))

    parsed = parse_entry(raw_text)
    if parsed is None:
        flash(f'"{raw_text}"에서 금액을 찾지 못했어요. 예: 스벅 5천원', "error")
        return redirect(url_for("index"))

    item, amount = parsed
    category = categorize_item(item)

    if category == FALLBACK_CATEGORY:
        return render_template(
            "confirm_category.html",
            raw_text=raw_text,
            item=item,
            amount=amount,
            categories=CATEGORY_CHOICES,
        )

    db.insert_entry(raw_text, item, amount, category)
    flash(f'저장했습니다: {item} · {amount:,}원 · {category}', "success")
    flash_budget_warning(category)
    return redirect(url_for("index"))


@app.route("/entry/confirm", methods=["POST"])
def confirm_entry():
    raw_text = request.form.get("raw_text", "")
    item = request.form.get("item", "")
    amount = request.form.get("amount", "0")
    category = request.form.get("category", FALLBACK_CATEGORY)

    db.insert_entry(raw_text, item, int(amount), category)
    learn_category(item, category)
    flash(f'저장했습니다: {item} · {int(amount):,}원 · {category}', "success")
    flash_budget_warning(category)
    return redirect(url_for("index"))


@app.route("/entry/<int:entry_id>/delete", methods=["POST"])
def delete_entry(entry_id):
    db.delete_entry(entry_id)
    flash("삭제했습니다.", "info")
    return redirect(url_for("index"))


@app.route("/entry/<int:entry_id>/category", methods=["POST"])
def update_entry_category(entry_id):
    category = request.form.get("category", FALLBACK_CATEGORY)
    entry = db.get_entry(entry_id)
    db.update_entry_category(entry_id, category)
    if entry is not None:
        learn_category(entry["item"], category)
    flash(f'카테고리를 "{category}"(으)로 수정했습니다.', "info")
    return redirect(url_for("index"))


@app.route("/budgets", methods=["GET", "POST"])
def budgets_page():
    if request.method == "POST":
        for category in EXPENSE_CATEGORY_ORDER:
            raw_value = request.form.get(f"budget__{category}", "").strip()
            amount = parse_amount(raw_value) or 0
            db.set_budget(category, amount)
        flash("예산을 저장했습니다.", "success")
        return redirect(url_for("index"))

    return render_template(
        "budgets.html",
        categories=EXPENSE_CATEGORY_ORDER,
        budgets=db.get_budgets(),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
