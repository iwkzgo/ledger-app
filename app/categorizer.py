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


def categorize_item(item: str) -> str:
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

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if _normalize(keyword) in normalized:
                return category

    return FALLBACK_CATEGORY
