"""Главная страница: ввод данных и расчёт юнит-экономики одного товара."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculators import compute_unit_economics
from configs.settings import EXTRA_FEE_BASES
from services import load_all_tariffs, resolve_params, resolve_logistics_cost
from utils import fmt_currency, fmt_percent
from .state import render_product_sidebar, status_badge


def _seed_overrides(prefix: str, params) -> None:
    st.session_state.setdefault(prefix + "commission_pct", params.commission_pct)
    st.session_state.setdefault(prefix + "acquiring_pct", params.acquiring_pct)
    st.session_state.setdefault(prefix + "logistics_to", params.logistics_to)
    st.session_state.setdefault(prefix + "return_logistics", params.return_logistics)
    st.session_state.setdefault(prefix + "returns_processing", params.returns_processing)
    st.session_state.setdefault(prefix + "storage_per_liter_day", params.storage_per_liter_day)


def _cost_breakdown_chart(res) -> go.Figure:
    items = [
        ("Себестоимость", res.cogs),
        ("Комиссия МП", res.commission),
        ("Эквайринг", res.acquiring),
        ("Логистика", res.logistics),
        ("Хранение", res.storage),
        ("Реклама", res.advertising),
        ("Прочее", res.other_costs),
        ("Налог", res.tax),
    ]
    labels = [i[0] for i in items if i[1] > 0]
    values = [round(i[1], 2) for i in items if i[1] > 0]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color="#2c5aa0"))
    fig.update_layout(
        title="Структура расходов на единицу, ₽",
        height=340,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def render() -> None:
    st.title("📊 Калькулятор юнит-экономики маркетплейсов")
    st.caption(
        "Data-driven расчёт по официальным тарифам. Тарифы можно менять на странице "
        "«Тарифы маркетплейсов» или вручную ниже — бизнес-логика при этом не меняется."
    )

    product = render_product_sidebar()

    tariffs = load_all_tariffs()
    if not tariffs:
        st.error("Не найдено ни одного тарифа в data/tariffs/. Проверьте установку данных.")
        return

    mp_ids = list(tariffs.keys())
    mp_names = {mid: tariffs[mid].get("name", mid) for mid in mp_ids}

    col_top1, col_top2 = st.columns(2)
    with col_top1:
        mp_id = st.selectbox(
            "Маркетплейс", mp_ids, format_func=lambda x: mp_names[x], key="calc_mp"
        )
    config = tariffs[mp_id]
    schemes = config.get("schemes", ["FBO"])
    with col_top2:
        scheme = st.selectbox("Схема работы", schemes, key="calc_scheme")

    # Базовые (из тарифа) параметры под текущие условия.
    base_params = resolve_params(
        config, scheme, product.category, product.weight_kg, product.volume_l
    )

    prefix = f"ov_{mp_id}_{scheme}_"
    with st.expander("⚙️ Расходы маркетплейса — ручная правка (переопределяет тариф)", expanded=False):
        st.caption(
            "Логистика рассчитана из тарифа под ваш объём/вес. Любое поле можно "
            "изменить вручную под конкретный кейс."
        )
        c1, c2, c3 = st.columns(3)
        _seed_overrides(prefix, base_params)
        with c1:
            st.number_input("Комиссия МП, %", min_value=0.0, max_value=100.0, step=0.5,
                            key=prefix + "commission_pct")
            st.number_input("Эквайринг, %", min_value=0.0, max_value=100.0, step=0.1,
                            key=prefix + "acquiring_pct")
        with c2:
            st.number_input("Логистика до покупателя, ₽", min_value=0.0, step=1.0,
                            key=prefix + "logistics_to")
            st.number_input("Обратная логистика, ₽", min_value=0.0, step=1.0,
                            key=prefix + "return_logistics")
        with c3:
            st.number_input("Обработка возврата, ₽", min_value=0.0, step=1.0,
                            key=prefix + "returns_processing")
            st.number_input("Хранение, ₽/л·день", min_value=0.0, step=0.01,
                            key=prefix + "storage_per_liter_day")

        if st.button("↺ Сбросить к тарифу", key=prefix + "reset"):
            for suffix in [
                "commission_pct", "acquiring_pct", "logistics_to",
                "return_logistics", "returns_processing", "storage_per_liter_day",
            ]:
                st.session_state.pop(prefix + suffix, None)
            st.rerun()

        st.markdown("**Дополнительные статьи расходов** (добавляйте/удаляйте строки)")
        default_fees = base_params.extra_fees
        fees_df = pd.DataFrame(default_fees) if default_fees else pd.DataFrame(
            columns=["name", "base", "rate", "amount", "note"]
        )
        for col in ["name", "base", "rate", "amount", "note"]:
            if col not in fees_df.columns:
                fees_df[col] = [] if fees_df.empty else ""
        edited = st.data_editor(
            fees_df,
            num_rows="dynamic",
            width="stretch",
            key=prefix + "fees",
            column_config={
                "name": st.column_config.TextColumn("Статья"),
                "base": st.column_config.SelectboxColumn("База", options=EXTRA_FEE_BASES),
                "rate": st.column_config.NumberColumn("Ставка, %", min_value=0.0),
                "amount": st.column_config.NumberColumn("Фикс, ₽", min_value=0.0),
                "note": st.column_config.TextColumn("Комментарий"),
            },
        )
        extra_fees = edited.fillna(0).to_dict("records") if not edited.empty else []

    overrides = {
        "commission_pct": st.session_state[prefix + "commission_pct"],
        "acquiring_pct": st.session_state[prefix + "acquiring_pct"],
        "logistics_to": st.session_state[prefix + "logistics_to"],
        "return_logistics": st.session_state[prefix + "return_logistics"],
        "returns_processing": st.session_state[prefix + "returns_processing"],
        "storage_per_liter_day": st.session_state[prefix + "storage_per_liter_day"],
        "extra_fees": extra_fees,
    }
    params = resolve_params(
        config, scheme, product.category, product.weight_kg, product.volume_l, overrides
    )

    if product.price <= 0:
        st.warning("Укажите цену продажи больше нуля, чтобы увидеть расчёт.")
        return

    res = compute_unit_economics(product, params)

    # --- Итоговые метрики ---
    badge_text, badge_color = status_badge(res.margin_pct)
    st.markdown("### Итог")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Чистая прибыль / шт", fmt_currency(res.net_profit))
    m2.metric("Маржинальность", fmt_percent(res.margin_pct))
    m3.metric("ROI (к себестоимости)", fmt_percent(res.roi_pct))
    m4.metric("Цена безубыточности", fmt_currency(res.break_even_price))
    st.markdown(
        f"<span style='background:{badge_color};color:#fff;padding:6px 14px;"
        f"border-radius:16px;font-weight:700'>{badge_text}</span>",
        unsafe_allow_html=True,
    )

    st.divider()
    left, right = st.columns([1, 1])

    with left:
        st.markdown("#### Детализация на единицу")
        rows = [
            ("Выручка (цена)", res.revenue),
            ("− Комиссия МП", -res.commission),
            ("− Эквайринг", -res.acquiring),
            ("− Логистика (с невыкупами)", -res.logistics),
            ("  в т.ч. обратная логистика", -res.returns_cost),
            ("− Хранение", -res.storage),
            ("− Реклама", -res.advertising),
            ("− Прочие расходы МП", -res.other_costs),
            ("− Себестоимость", -res.cogs),
            ("= Операционная прибыль", res.operating_profit),
            ("− Налог", -res.tax),
            ("= Чистая прибыль", res.net_profit),
        ]
        df = pd.DataFrame(
            [{"Статья": n, "Сумма, ₽": fmt_currency(v)} for n, v in rows]
        )
        st.dataframe(df, hide_index=True, width="stretch")

        st.markdown("#### Ключевые показатели")
        kpi = [
            ("Валовая прибыль (выручка − себестоимость)", fmt_currency(res.gross_profit)),
            ("Наценка к себестоимости", fmt_percent(res.markup_pct)),
            ("ROMI (отдача рекламы)", fmt_percent(res.romi_pct) if res.advertising > 0 else "—"),
            ("Расходы МП всего", fmt_currency(res.total_mp_costs)),
        ]
        if res.break_even_units > 0:
            kpi.append(("Точка безубыточности, шт/мес", f"{res.break_even_units:,.0f}".replace(",", " ")))
        st.dataframe(
            pd.DataFrame([{"Показатель": k, "Значение": v} for k, v in kpi]),
            hide_index=True, width="stretch",
        )

    with right:
        st.plotly_chart(_cost_breakdown_chart(res), width="stretch")
        if res.break_even_price == float("inf"):
            st.error(
                "При текущих расходах безубыточность недостижима — расходы превышают "
                "любую разумную цену. Снизьте издержки или пересмотрите модель."
            )

    # --- Сравнение схем текущего МП ---
    st.divider()
    st.markdown("#### ⚖️ Сравнение схем поставки на этом маркетплейсе")
    comp_rows = []
    for s in schemes:
        p = resolve_params(config, s, product.category, product.weight_kg, product.volume_l)
        r = compute_unit_economics(product, p)
        comp_rows.append(
            {
                "Схема": s,
                "Логистика, ₽": resolve_logistics_cost(
                    config.get("logistics", {}).get(s, {}), product.weight_kg, product.volume_l
                ),
                "Комиссия, %": p.commission_pct,
                "Чистая прибыль, ₽": round(r.net_profit, 0),
                "Маржа, %": round(r.margin_pct, 1),
            }
        )
    comp_df = pd.DataFrame(comp_rows)
    st.dataframe(
        comp_df.style.highlight_max(subset=["Чистая прибыль, ₽"], color="#d1fae5"),
        hide_index=True, width="stretch",
    )

    src = config.get("source", {})
    st.caption(
        f"Источник тарифов: [{src.get('url', '—')}]({src.get('url', '#')}) · "
        f"актуальность: {src.get('updated_at', '—')}. "
        "Значения baseline — проверяйте в личном кабинете продавца."
    )
