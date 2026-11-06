"""アプリケーション設定。

環境変数（接頭辞 ``AM_``）または ``.env`` で上書きできる。
保険料率・税率などの値は **サンプル値** であり、実運用では必ず最新の公的な料率に置き換えること。
"""

from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AM_", env_file=".env", extra="ignore")

    # --- システム ---
    database_url: str = "sqlite:///./attendance.db"
    jwt_secret: str = "dev-only-secret-change-me-in-production-0123456789"
    jwt_expire_minutes: int = 60 * 12
    cors_origins: list[str] = ["http://localhost:5173"]
    seed_demo_data: bool = True

    # --- 労働時間 ---
    legal_daily_minutes: int = 8 * 60  # 法定労働時間（1日）
    late_night_start_hour: int = 22  # 深夜時間帯 22:00〜翌5:00
    late_night_end_hour: int = 5
    legal_holiday_weekday: int = 6  # 法定休日（0=月 … 6=日）

    # --- 割増率（労働基準法第37条・割増賃金令の下限値） ---
    overtime_rate: Decimal = Decimal("1.25")
    overtime_over_60h_rate: Decimal = Decimal("1.50")
    holiday_rate: Decimal = Decimal("1.35")
    late_night_premium: Decimal = Decimal("0.25")
    overtime_60h_threshold_minutes: int = 60 * 60

    # --- 月給者の単価計算 ---
    # 月平均所定労働時間（就業規則に合わせる）
    monthly_avg_scheduled_hours: Decimal = Decimal("160")
    monthly_scheduled_days: Decimal = Decimal("20")  # 欠勤控除に使う月所定労働日数

    # --- 控除（従業員負担分・サンプル値） ---
    health_insurance_rate: Decimal = Decimal("0.04955")  # 健康保険（サンプル）
    pension_rate: Decimal = Decimal("0.0915")  # 厚生年金 18.3% の折半
    employment_insurance_rate: Decimal = Decimal("0.0055")  # 雇用保険（サンプル）
    income_tax_rate: Decimal = Decimal("0.03063")  # 所得税の簡易計算用（サンプル）
    commute_tax_free_limit: int = 150_000  # 通勤手当の非課税限度額（月額）

    # --- チェック ---
    minimum_wage: int = 1226  # 最低賃金（時給）。実際の地域・年度の額に更新すること
    overtime_warning_hours: int = 45  # 36協定の原則的上限（月45時間）
    overtime_alert_hours: int = 80


@lru_cache
def get_settings() -> Settings:
    return Settings()
