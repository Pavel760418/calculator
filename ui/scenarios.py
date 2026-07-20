"""Страница сценариев: базовый / оптимистичный / пессимистичный / ручной."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculators import compute_unit_economics, apply_scenario
from configs.settings import SCENARIOS
from services import load_all_tariffs, resolve_params
from utils import fmt_currency, fmt_percent
from .state import render_product_sidebar


def render() -> None:
    st.title("🎯 Сценарии")
    st.caption(
        "Стресс-анализ: как меняется экономика при разных допущениях по цене, "
        "комиссии, рекламе, логистике и выкупу."
    )

    product = render_product_sidebar()
    tariffs = load_all_tariffs()
    if not tariffs:
        st.error("Тарифы не найдены.")
        return

    mp_ids = list(tariffs.keys())
    mp_id = st.selectbox(
        "Маркетплейс", mp_ids,
        format_func=lambda x: tariffs[x].get("name", x), key="scen_mp",
    )
    config = tariffs[mp_id]
    scheme = st.selectbox("Схема", config.get("schemes", ["FBO"]), key="scen_scheme")
    base_params = resolve_params(
        config, scheme, product.category, product.weight_kg, product.volume_l
    )

    # Ручной сценарий — настраиваемые мультипликаторы.
    st.markdown("#### Настройка ручного сценария")
    c1, c2, c3 = st.columns(3)
    with c1:
        m_price = st.slider("Цена, ×", 0.5, 1.5, 1.0, 0.01)
        m_comm = st.slider("Комиссия, ×", 0.5, 1.5, 1.0, 0.01)
    with c2:
        m_drr = st.slider("ДРР, ×", 0.0, 2.0, 1.0, 0.05)
        m_log = st.slider("Логистика, ×", 0.5, 2.0, 1.0, 0.05)
    with c3:
        m_stor = st.slider("Хранение, ×", 0.5, 2.0, 1.0, 0.05)
        d_buyout = st.slider("Выкуп, +п.п.", -30.0, 15.0, 0.0, 1.0)

    manual_overrides = {
        "price": m_price, "commission": m_comm, "drr": m_drr,
        "logistics": m_log, "storage": m_stor, "buyout_delta": d_buyout,
    }

    rows = []
    charts = {}
    for name in SCENARIOS:
        ov = manual_overrides if name == "Ручной" else None
        p, params = apply_scenario(product, base_params, name, ov)
        res = compute_unit_economics(p, params)
        rows.append(
            {
                "Сценарий": name,
                "Цена, ₽": round(p.price, 0),
                "Чистая прибыль, ₽": round(res.net_profit, 0),
                "Маржа, %": round(res.margin_pct, 1),
                "ROI, %": round(res.roi_pct, 1),
                "Цена б/у, ₽": None if res.break_even_price == float("inf") else round(res.break_even_price, 0),
            }
        )
        charts[name] = res.net_profit

    df = pd.DataFrame(rows)
    st.markdown("#### Сравнение сценариев")
    st.dataframe(
        df.style.highlight_max(subset=["Чистая прибыль, ₽"], color="#d1fae5")
        .highlight_min(subset=["Чистая прибыль, ₽"], color="#fee2e2"),
        hide_index=True, width="stretch",
    )

    colors = {"Базовый": "#2c5aa0", "Оптимистичный": "#10b981",
              "Пессимистичный": "#ef4444", "Ручной": "#f59e0b"}
    fig = go.Figure(
        go.Bar(
            x=list(charts.keys()),
            y=[round(v, 0) for v in charts.values()],
            marker_color=[colors.get(k, "#2c5aa0") for k in charts],
        )
    )
    fig.update_layout(title="Чистая прибыль на единицу по сценариям, ₽", height=380)
    st.plotly_chart(fig, width="stretch")

    base = next(r for r in rows if r["Сценарий"] == "Базовый")
    st.info(
        f"База: {fmt_currency(base['Чистая прибыль, ₽'])} / шт, маржа "
        f"{fmt_percent(base['Маржа, %'])}. Сравните с оптимистичным и пессимистичным "
        "прогнозами, чтобы оценить устойчивость модели."
    )
