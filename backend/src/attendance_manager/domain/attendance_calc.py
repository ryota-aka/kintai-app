"""勤怠の日次計算・月次集計。

前提（簡易化している点）:
- 時間外労働は「1日8時間超」で判定する（週40時間超の判定は対象外）。
- 法定休日（既定は日曜）の労働はすべて休日労働とし、時間外には含めない。
- 深夜時間は出勤〜退勤の区間と 22:00〜翌5:00 の重なりで求め、休憩は深夜帯以外で取ったものとみなす。
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ..config import Settings
from .time_utils import minutes_between


@dataclass(frozen=True)
class DailyInput:
    work_date: date  # 勤務対象日
    clock_in: datetime | None  # 出勤日時。未打刻の場合は None
    clock_out: datetime | None  # 退勤日時。未打刻の場合は None
    break_minutes: int = 0  # 休憩時間（分）


@dataclass(frozen=True)
class DailyResult:
    work_date: date  # 勤務対象日
    work_minutes: int = 0  # 休憩を除いた実働時間（分）
    overtime_minutes: int = 0  # 法定労働時間を超えた時間（分）
    late_night_minutes: int = 0  # 深夜時間帯に働いた時間（分）
    holiday_minutes: int = 0  # 法定休日に働いた時間（分）
    is_legal_holiday: bool = False  # 勤務対象日が法定休日か
    incomplete: bool = False  # 出勤・退勤の打刻が不完全か


@dataclass
class LeaveSummary:
    paid_days: float = 0.0  # 有給（半休は0.5）
    special_days: float = 0.0  # 特別休暇日数
    absence_days: float = 0.0  # 欠勤日数


@dataclass
class MonthlySummary:
    work_days: int = 0  # 実働があった日数
    work_minutes: int = 0  # 月間の実働時間（分）
    overtime_minutes: int = 0  # 月間の時間外労働時間（分）
    overtime_within_60h_minutes: int = 0  # 月60時間以内の時間外労働（分）
    overtime_over_60h_minutes: int = 0  # 月60時間を超えた時間外労働（分）
    late_night_minutes: int = 0  # 月間の深夜労働時間（分）
    holiday_minutes: int = 0  # 月間の法定休日労働時間（分）
    paid_leave_days: float = 0.0  # 有給休暇日数（半休は0.5日）
    special_leave_days: float = 0.0  # 特別休暇日数
    absence_days: float = 0.0  # 欠勤日数
    incomplete_dates: list[date] = field(default_factory=list)  # 打刻が不完全な日付
    warnings: list[str] = field(default_factory=list)  # 月次集計で発生した警告


def late_night_overlap(start: datetime, end: datetime, settings: Settings) -> int:
    """[start, end) と深夜帯（22:00〜翌5:00）の重なり（分）。"""
    total = 0
    day = start.date() - timedelta(days=1)
    while day <= end.date():
        base = datetime.combine(day,datetime.min.time())
        window_start = base + timedelta(hours= settings.late_night_start_hour)
        window_end = base + timedelta(days= 1,hours=settings.late_night_end_hour)
        lo = max(start,window_start)
        hi = min(end,window_end)
        if hi> lo :
            total += minutes_between(lo,hi)
        day += timedelta(days=1)
    return total

def calc_daily(inp: DailyInput, settings: Settings) -> DailyResult:
    """1日分の勤怠を計算する。

    - 出勤も退勤もない日: 0 の結果（incomplete=False）
    - 出勤だけ・退勤 ≦ 出勤: incomplete=True（時間は 0）
    - 実働 = (退勤 − 出勤) − 休憩（0 未満にしない）
    - 深夜 = late_night_overlap()（実働を上限）
    - 法定休日（settings.legal_holiday_weekday）は実働すべてを holiday_minutes にし、時間外は 0
    - それ以外は 時間外 = max(0, 実働 − settings.legal_daily_minutes)
    """
    holiday = inp.work_date.weekday() == settings.legal_holiday_weekday
    if inp.clock_in is None and inp.clock_out is None:
        return DailyResult(inp.work_date,is_legal_holiday= holiday,incomplete= inp.clock_in is not None)
    if inp.clock_in >= inp.clock_out:
        return DailyResult(inp.work_date,is_legal_holiday= holiday,incomplete=True)
    span = minutes_between(inp.clock_in,inp.clock_out)
    work = max(0,span- inp.break_minutes)
    late_night = min(work,late_night_overlap(inp.clock_in,inp.clock_out,settings))

    if holiday:
        return DailyResult(
            inp.work_date,
            work_minutes= work,
            late_night_minutes= late_night,
            holiday_minutes= work,
            is_legal_holiday= True
        )

    overtime = max(0,work - settings.legal_daily_minutes)

    return DailyResult(
        inp.work_date,
        work_minutes= work,
        overtime_minutes= overtime,
        late_night_minutes= late_night
    )

def summarize_month(
    dailies: list[DailyResult], leaves: LeaveSummary, settings: Settings
) -> MonthlySummary:
    """日次結果を月次に集計する。

    - incomplete の日は incomplete_dates に入れ、時間には加えない
    - 実働 > 0 の日を出勤日数に数える
    - 時間外を 60時間以内（overtime_within_60h_minutes）と超過分に分ける
    - 警告: 時間外が overtime_alert_hours 以上なら「時間外労働が80時間以上です（xx.xh）」、
      そうでなく overtime_warning_hours 以上なら「…45時間以上です…」、
      不完全な日ごとに「YYYY-MM-DD の打刻が不完全です（退勤なし・時刻不正）」
    """

    
    raise NotImplementedError("TODO: summarize_month を実装してください")
