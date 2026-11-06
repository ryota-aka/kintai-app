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
    work_date: date
    clock_in: datetime | None
    clock_out: datetime | None
    break_minutes: int = 0


@dataclass(frozen=True)
class DailyResult:
    work_date: date
    work_minutes: int = 0
    overtime_minutes: int = 0
    late_night_minutes: int = 0
    holiday_minutes: int = 0
    is_legal_holiday: bool = False
    incomplete: bool = False  # 退勤打刻なし等


@dataclass
class LeaveSummary:
    paid_days: float = 0.0  # 有給（半休は0.5）
    special_days: float = 0.0
    absence_days: float = 0.0


@dataclass
class MonthlySummary:
    work_days: int = 0
    work_minutes: int = 0
    overtime_minutes: int = 0
    overtime_within_60h_minutes: int = 0
    overtime_over_60h_minutes: int = 0
    late_night_minutes: int = 0
    holiday_minutes: int = 0
    paid_leave_days: float = 0.0
    special_leave_days: float = 0.0
    absence_days: float = 0.0
    incomplete_dates: list[date] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def late_night_overlap(start: datetime, end: datetime, settings: Settings) -> int:
    """[start, end) と深夜帯（22:00〜翌5:00）の重なり（分）。"""
    raise NotImplementedError("TODO: late_night_overlap を実装してください")


def calc_daily(inp: DailyInput, settings: Settings) -> DailyResult:
    """1日分の勤怠を計算する。

    - 出勤も退勤もない日: 0 の結果（incomplete=False）
    - 出勤だけ・退勤 ≦ 出勤: incomplete=True（時間は 0）
    - 実働 = (退勤 − 出勤) − 休憩（0 未満にしない）
    - 深夜 = late_night_overlap()（実働を上限）
    - 法定休日（settings.legal_holiday_weekday）は実働すべてを holiday_minutes にし、時間外は 0
    - それ以外は 時間外 = max(0, 実働 − settings.legal_daily_minutes)
    """
    raise NotImplementedError("TODO: calc_daily を実装してください")


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
