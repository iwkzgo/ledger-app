"""Render(gunicorn)에서 사용하는 프로덕션 진입점입니다.

로컬 개발은 `python3 server.py`를 계속 사용하세요. 배포 환경에서는
`gunicorn wsgi:app` 명령으로 이 파일의 `app`을 구동합니다.
"""

from app import create_app

app = create_app()
