"""現在時刻の取得（テストで差し替えられるよう関数に分離）。"""

from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _jst() -> tzinfo:
    # Windows には IANA タイムゾーンDBがないため tzdata パッケージが必要。
    # 万一読めなくても、日本は夏時間がないので UTC+9 固定で代用できる。
    try:
        return ZoneInfo("Asia/Tokyo")
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=9), "JST")


JST = _jst()


def now_jst() -> datetime:
    """日本時間の現在時刻（タイムゾーンなし・秒切捨て）。"""
    return datetime.now(JST).replace(tzinfo=None, second=0, microsecond=0)


def get_now() -> datetime:
    """FastAPI の依存性として使う現在時刻（テストで上書きする）。"""
    return now_jst()
