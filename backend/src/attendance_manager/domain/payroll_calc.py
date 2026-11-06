"""給与計算。

金額計算は ``Decimal`` で行い、各項目ごとに円未満を処理する。
- 支給項目: 四捨五入（50銭未満切捨て・50銭以上切上げ）
- 社会保険・雇用保険の従業員負担分: 50銭以下切捨て・50銭超切上げ
- 所得税: 円未満切捨て

社会保険料は本来「標準報酬月額」に料率を掛けるが、本システムでは簡易的に当月の総支給額を使う。
所得税も源泉徴収税額表ではなく、課税対象額 × 設定税率の簡易計算。
"""

from dataclasses import dataclass, field
from decimal import ROUND_DOWN, ROUND_HALF_DOWN, ROUND_HALF_UP, Decimal

from ..config import Settings
from ..models import EmploymentType
from .attendance_calc import MonthlySummary

_SIXTY = Decimal(60)


def round_pay(value: Decimal) -> int:
    """支給項目の端数処理: 四捨五入（50銭以上切上げ）。"""
    raise NotImplementedError("TODO: round_pay を実装してください")


def round_insurance(value: Decimal) -> int:
    """保険料（従業員負担分）の端数処理: 50銭以下切捨て・50銭超切上げ。"""
    raise NotImplementedError("TODO: round_insurance を実装してください")


def floor_yen(value: Decimal) -> int:
    """円未満切捨て（所得税）。"""
    raise NotImplementedError("TODO: floor_yen を実装してください")


@dataclass(frozen=True)
class PayInput:
    employment_type: EmploymentType
    base_salary: int
    hourly_wage: int
    commute_allowance: int
    summary: MonthlySummary


@dataclass
class PayResult:
    hourly_unit: Decimal = Decimal(0)
    base_pay: int = 0
    overtime_pay: int = 0
    late_night_pay: int = 0
    holiday_pay: int = 0
    paid_leave_pay: int = 0
    absence_deduction: int = 0
    commute_allowance: int = 0
    gross_pay: int = 0
    health_insurance: int = 0
    pension: int = 0
    employment_insurance: int = 0
    income_tax: int = 0
    total_deductions: int = 0
    net_pay: int = 0
    warnings: list[str] = field(default_factory=list)


def hourly_unit_price(inp: PayInput, settings: Settings) -> Decimal:
    """割増賃金の基礎となる1時間あたりの単価。"""
    raise NotImplementedError("TODO: hourly_unit_price を実装してください")


def calculate_pay(inp: PayInput, settings: Settings) -> PayResult:
    """月の給与を計算する（計算式はモジュール冒頭と設計書7章を参照）。

    共通: 時間外 = 単価×1.25×60h以内 + 単価×1.5×60h超、休日 = 単価×1.35×休日時間、
          深夜 = 単価×0.25×深夜時間
    時給制: 基本給 = 単価×(実働−時間外−休日)、有給手当 = 単価×8h×(有給+特別休暇日数)
    月給制: 基本給 = 月給、欠勤控除 = 月給÷monthly_scheduled_days×欠勤日数
    総支給 = 各支給 + 通勤手当 − 欠勤控除（0 未満にしない）
    控除: 健康保険・厚生年金・雇用保険 = 総支給×各料率（round_insurance）
          所得税 = (総支給 − min(通勤手当, 非課税限度) − 社会保険計) × 税率（floor_yen）
    単価が最低賃金未満なら warnings に「最低賃金」を含む文言を追加する。
    """
    raise NotImplementedError("TODO: calculate_pay を実装してください")
