import os

from flask import Flask, send_from_directory

from .config import Config
from .extensions import db, login_manager
from .timeutil import to_kst

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    app.config.from_object(config_class)
    app.jinja_env.filters["kst"] = to_kst

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "로그인이 필요합니다."
    login_manager.login_message_category = "error"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .admin import bp as admin_bp
    from .auth import bp as auth_bp
    from .recurring import bp as recurring_bp
    from .routes import bp as ledger_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(recurring_bp)

    from .schema_sync import sync_schema

    sync_schema(app)

    @app.route("/sw.js")
    def service_worker():
        # 서비스워커는 자신이 서빙된 경로 아래로만 제어 범위(scope)가 잡히므로,
        # /static/sw.js가 아니라 루트에서 내려줘야 사이트 전체(/)를 제어할 수 있습니다.
        return send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")

    return app
