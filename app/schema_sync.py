from flask import Flask
from sqlalchemy import inspect, text

from .extensions import db


def sync_schema(app: Flask) -> None:
    """DB에 없는 테이블/컬럼을 자동으로 맞춰줍니다.

    이 프로젝트는 Alembic 같은 정식 마이그레이션 도구를 쓰지 않아서,
    모델에 새 컬럼을 추가해도 이미 만들어진 테이블에는 반영되지 않습니다.
    배포 때마다 이 함수가 부족한 테이블/컬럼을 자동으로 채워 넣어
    "column does not exist" 류의 에러를 막아줍니다.
    (컬럼 삭제·이름 변경·타입 변경 같은 복잡한 변경은 다루지 않습니다.)
    """
    with app.app_context():
        db.create_all()

        inspector = inspect(db.engine)
        for table in db.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue

            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue

                # 이미 데이터가 있는 테이블일 수 있으니 NOT NULL 제약은 걸지 않고,
                # 항상 널 허용 컬럼으로 추가합니다(크래시 방지가 목적이라 안전하게).
                col_type = column.type.compile(dialect=db.engine.dialect)
                ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'
                with db.engine.connect() as conn:
                    conn.execute(text(ddl))
                    conn.commit()
