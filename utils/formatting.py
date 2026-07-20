"""Утилиты форматирования чисел для интерфейса (рубли, проценты)."""
from __future__ import annotations

import math


def _nbsp_thousands(value: float, decimals: int = 0) -> str:
    """Форматирует число с пробелом-разделителем тысяч (как принято в РФ)."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    rounded = round(value, decimals)
    text = f"{rounded:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return text


def fmt_currency(value: float, decimals: int = 0) -> str:
    """Денежный формат: '1 234 ₽'. Бесконечность → 'недостижимо'."""
    if value == float("inf"):
        return "недостижимо"
    return f"{_nbsp_thousands(value, decimals)} ₽"


def fmt_percent(value: float, decimals: int = 1) -> str:
    """Процентный формат: '42,6%'."""
    if value == float("inf"):
        return "∞"
    return f"{_nbsp_thousands(value, decimals)}%"


def fmt_number(value: float, decimals: int = 2) -> str:
    """Обычное число с разделителями."""
    return _nbsp_thousands(value, decimals)
