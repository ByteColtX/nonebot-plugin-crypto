"""行情数据格式化工具。"""

from datetime import datetime
from decimal import Decimal, DecimalException
from zoneinfo import ZoneInfo


def format_decimal(value: object, places: int = 2, *, signed: bool = False) -> str:
    """将数值格式化为带千位分隔符的十进制文本。"""
    if value is None or value == "":
        return "-"

    try:
        number = Decimal(str(value))
    except (DecimalException, TypeError, ValueError):
        return str(value)

    result = f"{number:,.{places}f}"
    if signed and number > 0:
        return f"+{result}"
    return result


def format_time(value: object) -> str:
    """将 Binance 的毫秒时间戳转换为上海时区文本。"""
    try:
        timestamp = int(str(value)) / 1000
        date_time = datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC"))
        return date_time.astimezone(ZoneInfo("Asia/Shanghai")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except (TypeError, ValueError, OSError):
        return "-"
