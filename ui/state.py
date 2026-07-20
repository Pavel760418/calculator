"""Общее состояние и переиспользуемые элементы интерфейса.

Здесь собраны инициализация session_state и боковая форма ввода параметров
товара — чтобы одни и те же входные данные были доступны на всех страницах.
"""
from __future__ import annotations

import streamlit as st

from configs.settings import (
    TAX_REGIMES,
    DEFAULT_TAX_REGIME,
    PRODUCT_CATEGORIES,
)
from calculators.models import ProductInput

# Значения по умолчанию берут «дух» исходного калькулятора (спрей, 472/1890 и т.п.).
_DEFAULTS: dict = {
    "product_name": "спрей_женский_6шт",
    "price": 1890.0,
    "cost_price": 472.0,
    "weight": 0.45,
    "volume": 1.2,
    "category": "Красота и здоровье",
    "tax_regime": DEFAULT_TAX_REGIME,
    "drr": 12.0,
    "ad_fixed": 0.0,
    "buyout": 85.0,
    "defect": 2.0,
    "extra_cogs": 0.0,
    "storage_days": 15,
    "fixed_costs": 0.0,
}


def init_state() -> None:
    """Идемпотентно задаёт значения по умолчанию и сохраняет их между страницами.

    Особенность Streamlit: состояние виджета с ключом «сборщик мусора» удаляет
    при переходе на другую страницу (виджет не отрисован на предыдущей). Поэтому
    перед созданием виджетов мы «касаемся» ключей (переприсваиваем сами себе) —
    это фиксирует значения в session_state и сохраняет ввод пользователя между
    страницами «Калькулятор», «Сравнение», «Сценарии».
    """
    for key, value in _DEFAULTS.items():
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
        else:
            st.session_state[key] = value


def build_product_input() -> ProductInput:
    """Собирает ProductInput из текущего состояния сессии."""
    return ProductInput(
        price=float(st.session_state["price"]),
        cost_price=float(st.session_state["cost_price"]),
        weight_kg=float(st.session_state["weight"]),
        volume_l=float(st.session_state["volume"]),
        category=st.session_state["category"],
        tax_regime=st.session_state["tax_regime"],
        drr_pct=float(st.session_state["drr"]),
        ad_fixed=float(st.session_state["ad_fixed"]),
        buyout_pct=float(st.session_state["buyout"]),
        defect_pct=float(st.session_state["defect"]),
        extra_cogs=float(st.session_state["extra_cogs"]),
        storage_days=int(st.session_state["storage_days"]),
        fixed_costs_month=float(st.session_state["fixed_costs"]),
    )


def render_product_sidebar() -> ProductInput:
    """Рисует боковую форму ввода параметров товара и возвращает ProductInput."""
    init_state()
    with st.sidebar:
        st.header("🧾 Параметры товара")

        st.text_input("Наименование товара", key="product_name")

        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Цена продажи, ₽", min_value=0.0, step=10.0, key="price")
            st.number_input("Вес, кг", min_value=0.0, step=0.01, key="weight")
        with col2:
            st.number_input("Себестоимость, ₽", min_value=0.0, step=10.0, key="cost_price")
            st.number_input("Объём, л", min_value=0.0, step=0.1, key="volume")

        st.selectbox("Категория товара", PRODUCT_CATEGORIES, key="category")
        st.selectbox("Налоговый режим", list(TAX_REGIMES.keys()), key="tax_regime")

        st.divider()
        st.subheader("Реклама и потери")
        col3, col4 = st.columns(2)
        with col3:
            st.number_input("ДРР, %", min_value=0.0, max_value=100.0, step=0.5, key="drr")
            st.number_input("Выкуп, %", min_value=1.0, max_value=100.0, step=1.0, key="buyout")
        with col4:
            st.number_input("Реклама фикс., ₽/шт", min_value=0.0, step=1.0, key="ad_fixed")
            st.number_input("Брак/потери, %", min_value=0.0, max_value=100.0, step=0.5, key="defect")

        st.divider()
        st.subheader("Дополнительно")
        st.number_input("Доп. себестоимость (упаковка и т.п.), ₽/шт", min_value=0.0, step=1.0, key="extra_cogs")
        st.number_input("Срок хранения для оценки, дней", min_value=0, step=1, key="storage_days")
        st.number_input("Постоянные расходы в месяц, ₽", min_value=0.0, step=1000.0, key="fixed_costs",
                        help="Используется для точки безубыточности в штуках.")

    return build_product_input()


def status_badge(margin_pct: float) -> tuple[str, str]:
    """Возвращает (текст, цвет) статуса по маржинальности."""
    if margin_pct >= 20:
        return "✅ ОТЛИЧНО", "#10b981"
    if margin_pct >= 15:
        return "👍 ХОРОШО", "#3b82f6"
    if margin_pct >= 10:
        return "⚠️ НОРМА", "#f59e0b"
    return "❌ УБЫТОЧНО / НИЗКО", "#ef4444"
