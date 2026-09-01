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
    # 마지막으로 자동 기록한 달 ("YYYY-MM"). 중복 기록을 막고, 사용자가 지운 자동 기록을
    # 같은 달에 다시 만들지 않기 위한 기준으로 씁니다.
    last_recorded_month = db.Column(db.String(7), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
