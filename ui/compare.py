"""Страница сравнения: юнит-экономика одного товара на разных маркетплейсах."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculators import compute_unit_economics
from services import load_all_tariffs, resolve_params
from utils import fmt_currency, fmt_percent
from .state import render_product_sidebar


def render() -> None:
    st.title("⚖️ Сравнение маркетплейсов")
    st.caption("Один и тот же товар на разных площадках по их актуальным тарифам.")

    product = render_product_sidebar()
    tariffs = load_all_tariffs()
    if not tariffs:
        st.error("Тарифы не найдены.")
        return

    if product.price <= 0:
        st.warning("Укажите цену продажи больше нуля.")
        return

    rows = []
    for mp_id, config in tariffs.items():
        scheme = config.get("default_scheme", config.get("schemes", ["FBO"])[0])
        params = resolve_params(
            config, scheme, product.category, product.weight_kg, product.volume_l
        )
        res = compute_unit_economics(product, params)
        rows.append(
            {
                "Маркетплейс": config.get("name", mp_id),
                "Схема": scheme,
                "Комиссия, %": round(params.commission_pct, 1),
                "Расходы МП, ₽": round(res.total_mp_costs, 0),
                "Чистая прибыль, ₽": round(res.net_profit, 0),
                "Маржа, %": round(res.margin_pct, 1),
                "ROI, %": round(res.roi_pct, 1),
                "Цена б/у, ₽": None if res.break_even_price == float("inf") else round(res.break_even_price, 0),
            }
        )

    df = pd.DataFrame(rows).sort_values("Чистая прибыль, ₽", ascending=False)

    best = df.iloc[0]
    st.success(
        f"Лучшая площадка по чистой прибыли: **{best['Маркетплейс']}** — "
        f"{fmt_currency(best['Чистая прибыль, ₽'])} / шт, маржа {fmt_percent(best['Маржа, %'])}."
    )

    st.dataframe(
        df.style.highlight_max(subset=["Чистая прибыль, ₽", "Маржа, %"], color="#d1fae5"),
        hide_index=True, width="stretch",
    )

    fig = go.Figure()
    fig.add_bar(x=df["Маркетплейс"], y=df["Чистая прибыль, ₽"], name="Чистая прибыль, ₽",
                marker_color="#2c5aa0")
    fig.update_layout(title="Чистая прибыль на единицу по маркетплейсам, ₽", height=380)
    st.plotly_chart(fig, width="stretch")

    fig2 = go.Figure()
    fig2.add_bar(x=df["Маркетплейс"], y=df["Маржа, %"], name="Маржа, %", marker_color="#10b981")
    fig2.update_layout(title="Маржинальность по маркетплейсам, %", height=380)
    st.plotly_chart(fig2, width="stretch")
