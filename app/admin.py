import secrets
import string

from flask import Blueprint, abort, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from .extensions import db
from .models import User

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin() -> None:
    if current_user.username not in current_app.config["ADMIN_USERNAMES"]:
        abort(403)


@bp.route("/users")
@login_required
def users():
    _require_admin()
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=all_users)


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
