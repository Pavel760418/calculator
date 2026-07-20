"""Глобальные настройки приложения (пути, налоговые режимы, сценарии, категории).

Всё, что относится к «правилам предметной области», вынесено сюда и в data/tariffs/*.json,
чтобы бизнес-логику и интерфейс можно было менять независимо от конкретных чисел.
"""
from __future__ import annotations

from pathlib import Path

# --- Пути ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TARIFFS_DIR = DATA_DIR / "tariffs"
USER_DIR = DATA_DIR / "user"

APP_TITLE = "Калькулятор юнит-экономики маркетплейсов"
APP_ICON = "📊"

# --- Налоговые режимы ------------------------------------------------------
# type:
#   "income"  — налог считается от выручки (P * rate)
#   "profit"  — налог считается от прибыли до налога (max(profit,0) * rate)
#   "fixed"   — фиксированный/патентный режим, на единицу не относим (rate=0)
TAX_REGIMES: dict[str, dict] = {
    "УСН Доходы 6%": {"type": "income", "rate": 0.06},
    "УСН Доходы-Расходы 15%": {"type": "profit", "rate": 0.15},
    "ОСН 20% (упрощённо)": {"type": "profit", "rate": 0.20},
    "Патент": {"type": "fixed", "rate": 0.0},
    "Самозанятость 4%": {"type": "income", "rate": 0.04},
}
DEFAULT_TAX_REGIME = "УСН Доходы-Расходы 15%"

# --- Сценарии --------------------------------------------------------------
# Мультипликаторы применяются к соответствующим параметрам; buyout_delta —
# аддитивная поправка к проценту выкупа (в процентных пунктах).
SCENARIOS: dict[str, dict] = {
    "Базовый": {
        "price": 1.0, "commission": 1.0, "drr": 1.0,
        "logistics": 1.0, "storage": 1.0, "buyout_delta": 0.0,
    },
    "Оптимистичный": {
        "price": 1.05, "commission": 0.95, "drr": 0.8,
        "logistics": 0.95, "storage": 0.9, "buyout_delta": 5.0,
    },
    "Пессимистичный": {
        "price": 0.95, "commission": 1.05, "drr": 1.25,
        "logistics": 1.15, "storage": 1.2, "buyout_delta": -10.0,
    },
    "Ручной": {
        "price": 1.0, "commission": 1.0, "drr": 1.0,
        "logistics": 1.0, "storage": 1.0, "buyout_delta": 0.0,
    },
}
DEFAULT_SCENARIO = "Базовый"

# Базовый набор категорий (для UI). Конкретные ставки берутся из тарифов МП.
PRODUCT_CATEGORIES: list[str] = [
    "default",
    "Красота и здоровье",
    "Одежда и обувь",
    "Электроника",
    "Дом и сад",
    "Товары для детей",
    "Продукты питания",
]

# Базы, по которым может начисляться дополнительная статья расходов.
EXTRA_FEE_BASES: list[str] = ["price", "revenue", "cogs", "fixed"]
EXTRA_FEE_BASE_LABELS: dict[str, str] = {
    "price": "% от цены",
    "revenue": "% от выручки после комиссии",
    "cogs": "% от себестоимости",
    "fixed": "фикс. сумма на единицу, ₽",
}
