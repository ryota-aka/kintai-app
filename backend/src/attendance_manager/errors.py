"""独自例外。すべて AttendanceError を継承する。"""


class AttendanceError(Exception):
    """本システムの業務例外の基底クラス。"""


class InvalidRecordError(AttendanceError):
    """勤怠データの値が不正。"""


class EncodingDetectionError(AttendanceError):
    """CSV の文字コードを判定できない。"""


class MissingColumnError(AttendanceError):
    """CSV に必須列がない。"""


class ClockStateError(AttendanceError):
    """打刻の順序が不正（未出勤で退勤など）。"""


class PeriodClosedError(AttendanceError):
    """締め済みの月を変更しようとした。"""
