"""時刻・時間表記の変換。"""

import re
from datetime import date, datetime, timedelta

from ..errors import InvalidRecordError

# HH:MM 形式の時刻表記（0:00～23:59）を表す正規表現
_HHMM = re.compile(r"^(\d{1,2}):(\d{2})$")


def parse_hours(value: str) -> float:
    """「H:MM」または時間数の文字列を時間（float）に変換する。"""
    text = value.strip() #空白除去 
    if not text :
        raise InvalidRecordError("時間が入力されていません")
    match = _HHMM.fullmatch(text)
    if match:
        hour,minutes = int(match.group(1)),int(match.group(2))
        if minutes >= 60:
            raise InvalidRecordError(f"「分」が不正な値です:{value!r}")
        return hour + minutes/60
    try:
        result = float(text)
    except ValueError as exc:
        raise InvalidRecordError(f"「時刻」が不正な値です:{value!r}")
    if result < 0:
        raise InvalidRecordError(f"負の時刻です:{value!r}")
    return result

def parse_clock(work_date: date, value: str) -> datetime:
    """勤務日と「HH:MM」形式の時刻から、日付をまたぐ場合も含めて日時を作る。"""
    match = _HHMM.match(value.strip())
    if not match:
        raise InvalidRecordError(f"時刻が「HH:MM」形式ではありません:{value!r}")
    hours,minutes = int(match.group(1)),int(match.group(2))
    if hours >= 48 or minutes >= 60:
        raise InvalidRecordError(f"時刻が不正な値です:{value!r}")
    return datetime.combine(work_date,datetime.min.time()) + timedelta(hours= hours, minutes= minutes)

def minutes_between(start: datetime, end: datetime) -> int:
    """開始日時から終了日時までの経過時間を分（int）で返す。"""
    return int((end - start).total_seconds()//60)
 
def format_minutes(minutes: int) -> str:
    """分数を「H:MM」形式の文字列に変換する。負数は先頭にマイナスを付ける。"""
    sign = "-" if minutes < 0 else ""
    m = abs(minutes)
    return f"{sign}{m // 60}:{m % 60:02d}"

def parse_year_month(value: str) -> tuple[int, int]:
    """「YYYY-MM」形式の文字列を（年, 月）の整数タプルに変換する。"""
    match = re.match(r"^(\d{4})-(\d{2})$",value)
    if not match or not 1 <= int(match.group(2)) <= 12:
        raise InvalidRecordError(f"年月は YYYY-MM 形式で指定してください: {value!r}")
    return int(match.group(1)),int(match.group(2))


def month_range(year: int, month: int) -> tuple[date, date]:
    """指定した月の初日と末日を返す。"""
    first = date(year,month,1)
    next = date(year +1,1,1) if month == 12 else date(year,month+1,1)
    return first, next-timedelta(days=1)
