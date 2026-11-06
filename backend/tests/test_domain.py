"""ドメインロジック（時間変換・勤怠計算・給与計算）の単体テスト。"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from attendance_manager.config import Settings
from attendance_manager.domain.attendance_calc import (
    DailyInput,
    LeaveSummary,
    MonthlySummary,
    calc_daily,
    summarize_month,
)
from attendance_manager.domain.payroll_calc import (
    PayInput,
    calculate_pay,
    round_insurance,
    round_pay,
)
from attendance_manager.domain.time_utils import (
    format_minutes,
    month_range,
    parse_clock,
    parse_hours,
    parse_year_month,
)
from attendance_manager.errors import InvalidRecordError
from attendance_manager.models import EmploymentType

D = date(2026, 10, 1)  # 木曜
SUN = date(2026, 10, 4)  # 日曜


def dt(d: date, h: int, m: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day) + timedelta(hours=h, minutes=m)


# ---------------------------------------------------------------- time_utils
@pytest.mark.parametrize(("text", "expected"), [("8:30", 8.5), ("8.5", 8.5), ("8", 8.0), ("0", 0)])
def test_parse_hours_ok(text: str, expected: float) -> None:
    assert parse_hours(text) == expected


@pytest.mark.parametrize("text", ["8:75", "abc", "", "-1"])
def test_parse_hours_invalid(text: str) -> None:
    with pytest.raises(InvalidRecordError):
        parse_hours(text)


def test_parse_clock_next_day_notation() -> None:
    assert parse_clock(D, "26:30") == datetime(2026, 10, 2, 2, 30)


@pytest.mark.parametrize("text", ["9", "9:60", "48:00", "aa:bb"])
def test_parse_clock_invalid(text: str) -> None:
    with pytest.raises(InvalidRecordError):
        parse_clock(D, text)


def test_format_and_month_helpers() -> None:
    assert format_minutes(510) == "8:30"
    assert format_minutes(-5) == "-0:05"
    assert parse_year_month("2026-10") == (2026, 10)
    assert month_range(2026, 12) == (date(2026, 12, 1), date(2026, 12, 31))
    assert month_range(2028, 2)[1] == date(2028, 2, 29)
    with pytest.raises(InvalidRecordError):
        parse_year_month("2026-13")


# ---------------------------------------------------------------- 日次計算
def test_daily_normal(settings: Settings) -> None:
    r = calc_daily(DailyInput(D, dt(D, 9), dt(D, 18), 60), settings)
    assert (r.work_minutes, r.overtime_minutes, r.late_night_minutes) == (480, 0, 0)


def test_daily_overtime(settings: Settings) -> None:
    r = calc_daily(DailyInput(D, dt(D, 9), dt(D, 20, 30), 60), settings)
    assert r.work_minutes == 630  # 11.5h − 休憩1h
    assert r.overtime_minutes == 150


def test_daily_late_night_across_midnight(settings: Settings) -> None:
    # 18:00〜翌3:00、休憩60分 → 実働8h、深夜 22:00〜3:00 = 5h
    r = calc_daily(DailyInput(D, dt(D, 18), dt(D, 27), 60), settings)
    assert r.work_minutes == 480
    assert r.late_night_minutes == 300
    assert r.overtime_minutes == 0


def test_daily_early_morning_late_night(settings: Settings) -> None:
    r = calc_daily(DailyInput(D, dt(D, 4), dt(D, 13), 60), settings)
    assert r.late_night_minutes == 60  # 4:00〜5:00


def test_daily_legal_holiday(settings: Settings) -> None:
    r = calc_daily(DailyInput(SUN, dt(SUN, 9), dt(SUN, 19), 60), settings)
    assert r.is_legal_holiday
    assert r.holiday_minutes == 540
    assert r.overtime_minutes == 0


def test_daily_incomplete(settings: Settings) -> None:
    assert calc_daily(DailyInput(D, dt(D, 9), None), settings).incomplete
    assert not calc_daily(DailyInput(D, None, None), settings).incomplete
    assert calc_daily(DailyInput(D, dt(D, 18), dt(D, 9)), settings).incomplete


# ---------------------------------------------------------------- 月次集計
def test_summary_splits_60h_and_warns(settings: Settings) -> None:
    # 1日あたり残業4h × 20日 = 80h
    days = [
        calc_daily(
            DailyInput(date(2026, 10, d), dt(date(2026, 10, d), 8), dt(date(2026, 10, d), 21), 60),
            settings,
        )
        for d in range(1, 31)
        if date(2026, 10, d).weekday() < 5
    ][:20]
    s = summarize_month(days, LeaveSummary(), settings)
    assert s.overtime_minutes == 80 * 60
    assert s.overtime_within_60h_minutes == 60 * 60
    assert s.overtime_over_60h_minutes == 20 * 60
    assert any("80時間以上" in w for w in s.warnings)


def test_summary_45h_warning_and_incomplete(settings: Settings) -> None:
    days = [calc_daily(DailyInput(D, dt(D, 9), dt(D, 18), 60), settings)] * 1
    s = summarize_month(days, LeaveSummary(paid_days=1.5), settings)
    assert s.warnings == []
    assert s.paid_leave_days == 1.5

    long_day = calc_daily(DailyInput(D, dt(D, 0), dt(D, 23, 59), 0), settings)  # 残業 15h59m
    s = summarize_month(
        [long_day] * 3 + [calc_daily(DailyInput(D, dt(D, 9), None), settings)],
        LeaveSummary(),
        settings,
    )
    assert any("45時間以上" in w for w in s.warnings)
    assert any("打刻が不完全" in w for w in s.warnings)


# ---------------------------------------------------------------- 給与計算
def test_rounding_rules() -> None:
    assert round_pay(Decimal("100.5")) == 101
    assert round_pay(Decimal("100.49")) == 100
    assert round_insurance(Decimal("100.5")) == 100  # 50銭以下切捨て
    assert round_insurance(Decimal("100.51")) == 101


def _summary(**kw: int | float) -> MonthlySummary:
    s = MonthlySummary(**kw)  # type: ignore[arg-type]
    s.overtime_within_60h_minutes = min(s.overtime_minutes, 3600)
    s.overtime_over_60h_minutes = max(0, s.overtime_minutes - 3600)
    return s


def test_hourly_pay_example(settings: Settings) -> None:
    # 時給1,500円・所定内152h・残業8.5h → 228,000 + 15,938 = 243,938
    s = _summary(work_minutes=(152 * 60) + 510, overtime_minutes=510)
    r = calculate_pay(PayInput(EmploymentType.HOURLY, 0, 1500, 0, s), settings)
    assert r.base_pay == 228_000
    assert r.overtime_pay == 15_938
    assert r.gross_pay == 243_938


def test_monthly_pay_with_premiums(settings: Settings) -> None:
    # 月給320,000 / 160h = 単価2,000円
    s = _summary(
        work_minutes=200 * 60,
        overtime_minutes=70 * 60,
        late_night_minutes=120,
        holiday_minutes=300,
        absence_days=1,
    )
    r = calculate_pay(PayInput(EmploymentType.MONTHLY, 320_000, 0, 10_000, s), settings)
    assert r.hourly_unit == Decimal(2000)
    assert r.overtime_pay == 2000 * 125 // 100 * 60 + 2000 * 150 // 100 * 10  # 150,000 + 30,000
    assert r.late_night_pay == 1000  # 2000 × 0.25 × 2h
    assert r.holiday_pay == 13_500  # 2000 × 1.35 × 5h
    assert r.absence_deduction == 16_000  # 320,000 / 20日
    assert r.gross_pay == 320_000 + 180_000 + 1000 + 13_500 + 10_000 - 16_000
    assert r.net_pay == r.gross_pay - r.total_deductions
    assert r.total_deductions == (
        r.health_insurance + r.pension + r.employment_insurance + r.income_tax
    )


def test_deductions_and_tax(settings: Settings) -> None:
    s = _summary()
    r = calculate_pay(PayInput(EmploymentType.MONTHLY, 300_000, 0, 20_000, s), settings)
    assert r.gross_pay == 320_000
    assert r.pension == 29_280  # 320,000 × 9.15%
    assert r.health_insurance == 15_856  # 320,000 × 4.955%
    assert r.employment_insurance == 1_760
    taxable = 320_000 - 20_000 - (29_280 + 15_856 + 1_760)
    assert r.income_tax == int(taxable * Decimal("0.03063"))


def test_paid_leave_pay_for_hourly(settings: Settings) -> None:
    s = _summary(paid_leave_days=1.5)
    r = calculate_pay(PayInput(EmploymentType.HOURLY, 0, 1500, 0, s), settings)
    assert r.paid_leave_pay == 18_000  # 1500 × 8h × 1.5日


def test_minimum_wage_warning(settings: Settings) -> None:
    r = calculate_pay(PayInput(EmploymentType.HOURLY, 0, 1000, 0, _summary()), settings)
    assert any("最低賃金" in w for w in r.warnings)
    ok = calculate_pay(
        PayInput(EmploymentType.HOURLY, 0, settings.minimum_wage, 0, _summary()), settings
    )
    assert ok.warnings == []
