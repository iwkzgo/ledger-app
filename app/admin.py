from flask import Blueprint, abort, current_app, render_template
from flask_login import current_user, login_required

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
