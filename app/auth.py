from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from .extensions import db
from .models import User

bp = Blueprint("auth", __name__)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            flash("아이디와 비밀번호를 입력해주세요.", "error")
            return redirect(url_for("auth.signup"))
        if password != confirm:
            flash("비밀번호가 서로 일치하지 않습니다.", "error")
            return redirect(url_for("auth.signup"))
        if User.query.filter_by(username=username).first() is not None:
            flash("이미 사용 중인 아이디입니다.", "error")
            return redirect(url_for("auth.signup"))

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("가입을 환영합니다!", "success")
        return redirect(url_for("ledger.index"))

    return render_template("signup.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash("아이디 또는 비밀번호가 올바르지 않습니다.", "error")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("ledger.index"))

    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
