import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _normalize_db_url(url: str) -> str:
    # Render(과거 Heroku)가 주는 "postgres://"는 SQLAlchemy 2.x에서 인식하지 못해서
    # "postgresql://"로 바꿔줘야 합니다.
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-dev-only")
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'ledger.db')}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 쉼표로 구분된 관리자 아이디 목록. 여기 포함된 아이디로 로그인해야 /admin/users를 볼 수 있습니다.
    ADMIN_USERNAMES = {
        u.strip() for u in os.environ.get("ADMIN_USERNAMES", "").split(",") if u.strip()
    }
