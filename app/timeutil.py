from datetime import timedelta

# Render 서버는 UTC로 동작하기 때문에 datetime.now()로 저장된 시각은 UTC 기준입니다.
# 화면에 보여줄 때만 한국 시간(KST, UTC+9)으로 변환합니다.
KST_OFFSET = timedelta(hours=9)


def to_kst(value):
    if value is None:
        return None
    return value + KST_OFFSET
