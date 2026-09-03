from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password: str) -> None:
        # 일부 환경(예: OpenSSL 없이 빌드된 Python)에서 기본값인 scrypt를 못 쓰는 경우가 있어
        # 호환성이 더 넓은 pbkdf2:sha256을 명시적으로 사용합니다.
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Entry(db.Model):
    __tablename__ = "entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    raw_text = db.Column(db.String(255), nullable=False)
    item = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    memo = db.Column(db.String(255), nullable=True)


class Budget(db.Model):
    __tablename__ = "budgets"
    __table_args__ = (db.UniqueConstraint("user_id", "category", name="uq_budget_user_category"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    monthly_amount = db.Column(db.Integer, nullable=False)


class LearnedCategory(db.Model):
    __tablename__ = "learned_categories"
    __table_args__ = (db.UniqueConstraint("user_id", "item_key", name="uq_learned_user_item"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item_key = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)


class RecurringItem(db.Model):
    __tablename__ = "recurring_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    day_of_month = db.Column(db.Integer, nullable=False)
    # "고정지출"(기존 기본값) 또는 "수입". 스키마 동기화는 새 컬럼을 항상 nullable로
    # 추가하므로, 기존에 저장된 행은 NULL일 수 있어 사용할 때 고정지출로 취급합니다.
    category = db.Column(db.String(50), nullable=True)
    # 마지막으로 자동 기록한 달 ("YYYY-MM"). 중복 기록을 막고, 사용자가 지운 자동 기록을
    # 같은 달에 다시 만들지 않기 위한 기준으로 씁니다.
    last_recorded_month = db.Column(db.String(7), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)


class SavingsGoal(db.Model):
    __tablename__ = "savings_goals"
    __table_args__ = (db.UniqueConstraint("user_id", "month", name="uq_savings_goal_user_month"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # "YYYY-MM"
    target_amount = db.Column(db.Integer, nullable=False)


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_category_user_name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    # 고정지출/기타는 앱 로직(자동 기록, 미분류 처리)에 꼭 필요해서 삭제할 수 없게 막습니다.
    is_protected = db.Column(db.Boolean, nullable=False, default=False)
