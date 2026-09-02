import secrets
import string
from datetime import datetime, timedelta

from flask import Blueprint, abort, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from .extensions import db
from .models import Entry, User
from .timeutil import KST_OFFSET, to_kst

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin() -> None:
    if current_user.username not in current_app.config["ADMIN_USERNAMES"]:
        abort(403)


@bp.route("/users")
@login_required
def users():
    _require_admin()
    all_users = User.query.order_by(User.created_at.desc()).all()

    today = to_kst(datetime.now()).date()
    monday = today - timedelta(days=today.weekday())
    week_start = datetime.combine(monday, datetime.min.time()) - KST_OFFSET

    entry_counts = dict(
        db.session.query(Entry.user_id, func.count(Entry.id)).group_by(Entry.user_id).all()
    )
    last_entry_map = dict(
        db.session.query(Entry.user_id, func.max(Entry.created_at)).group_by(Entry.user_id).all()
    )

    users_data = [
        {
            "user": user,
            "entry_count": entry_counts.get(user.id, 0),
            "last_entry_at": last_entry_map.get(user.id),
        }
        for user in all_users
    ]

    stats = {
        "total_users": len(all_users),
        "new_this_week": sum(1 for u in all_users if u.created_at >= week_start),
        "active_this_week": sum(1 for u in all_users if u.last_login_at and u.last_login_at >= week_start),
    }

    return render_template("admin_users.html", users_data=users_data, stats=stats)


@bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
def reset_password(user_id):
    _require_admin()
    user = User.query.get_or_404(user_id)
    temp_password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    user.set_password(temp_password)
    db.session.commit()
    flash(
        f'"{user.username}"의 비밀번호를 임시 비밀번호로 초기화했습니다: {temp_password} '
        f'(사용자에게 안내한 뒤, 로그인 후 "비밀번호 변경"으로 바꾸도록 알려주세요.)',
        "success",
    )
    return redirect(url_for("admin.users"))
