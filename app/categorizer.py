from .extensions import db
from .models import LearnedCategory
from .rules import (
    CATEGORY_RULES,
    DATE_CATEGORY,
    DATE_KEYWORDS,
    FALLBACK_CATEGORY,
    INCOME_CATEGORY,
    INCOME_KEYWORDS,
    SAVINGS_CATEGORY,
    SAVINGS_KEYWORDS,
)


def _normalize(text: str) -> str:
    return text.replace(" ", "").upper()


def categorize_item(item: str, user_id: int) -> str:
    normalized = _normalize(item)

    for keyword in INCOME_KEYWORDS:
        if _normalize(keyword) in normalized:
            return INCOME_CATEGORY

    for keyword in SAVINGS_KEYWORDS:
        if _normalize(keyword) in normalized:
            return SAVINGS_CATEGORY

    for keyword in DATE_KEYWORDS:
        if _normalize(keyword) in normalized:
            return DATE_CATEGORY

    # 사용자가 이전에 같은 항목명에 직접 지정해둔 카테고리가 있으면 그것을 우선 사용합니다.
    learned = LearnedCategory.query.filter_by(user_id=user_id, item_key=normalized).first()
    if learned:
        return learned.category

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if _normalize(keyword) in normalized:
                return category

    return FALLBACK_CATEGORY


def learn_category(item: str, category: str, user_id: int) -> None:
    """사용자가 직접 지정한 항목명 → 카테고리 매핑을 저장해서 다음부터 자동 적용되게 합니다."""
    normalized = _normalize(item)
    existing = LearnedCategory.query.filter_by(user_id=user_id, item_key=normalized).first()
    if existing:
        existing.category = category
    else:
        db.session.add(LearnedCategory(user_id=user_id, item_key=normalized, category=category))
    db.session.commit()
