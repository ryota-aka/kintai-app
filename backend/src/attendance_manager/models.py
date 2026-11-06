"""列挙型（段階3でテーブル定義を追加する）。"""

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class EmploymentType(StrEnum):
    MONTHLY = "monthly"  # 月給制
    HOURLY = "hourly"  # 時給制


class LeaveType(StrEnum):
    PAID_FULL = "paid_full"  # 有給（全日）
    PAID_HALF_AM = "paid_half_am"  # 有給（午前半休）
    PAID_HALF_PM = "paid_half_pm"  # 有給（午後半休）
    ABSENCE = "absence"  # 欠勤（無給）
    SPECIAL = "special"  # 特別休暇（有給扱い・残日数を消化しない）


class RequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PayrollStatus(StrEnum):
    DRAFT = "draft"
    CLOSED = "closed"
