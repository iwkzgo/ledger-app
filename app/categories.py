from typing import List

from .extensions import db
from .models import Category
from .rules import EXPENSE_CATEGORY_ORDER, FALLBACK_CATEGORY, FIXED_EXPENSE_CATEGORY

PROTECTED_CATEGORIES = {FIXED_EXPENSE_CATEGORY, FALLBACK_CATEGORY}


def ensure_default_categories(user_id: int) -> None:
    """사용자에게 지출 카테고리가 하나도 없으면 기본 카테고리들을 만들어줍니다."""
    if Category.query.filter_by(user_id=user_id).first() is not None:
        return

    for position, name in enumerate(EXPENSE_CATEGORY_ORDER):
        db.session.add(
            Category(
                user_id=user_id,
                name=name,
                position=position,
                is_protected=name in PROTECTED_CATEGORIES,
            )
        )
    db.session.commit()


def get_expense_categories(user_id: int) -> List[str]:
    """사용자의 지출 카테고리 목록을 등록 순서대로 반환합니다. 없으면 기본값으로 채웁니다."""
    ensure_default_categories(user_id)
    rows = Category.query.filter_by(user_id=user_id).order_by(Category.position).all()
    return [row.name for row in rows]
