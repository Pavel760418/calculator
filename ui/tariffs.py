"""Страница «Тарифы маркетплейсов»: просмотр, ручное редактирование, версии.

Служебный/админский режим. Позволяет обновлять условия МП без правок в коде:
все изменения пишутся в data/tariffs/*.json и фиксируются в истории версий.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from configs.settings import EXTRA_FEE_BASES
from services import list_marketplaces, load_tariff, save_tariff
from services.tariff_repository import TariffError


def _categories_df(config: dict) -> pd.DataFrame:
    cats = config.get("categories", {})
    return pd.DataFrame(
        [{"category": name, "commission_pct": v.get("commission_pct", 0.0)} for name, v in cats.items()]
    )


def _logistics_df(config: dict) -> pd.DataFrame:
    log = config.get("logistics", {})
    rows = []
    for scheme, cfg in log.items():
        rows.append(
            {
                "scheme": scheme,
                "base_cost": cfg.get("base_cost", 0.0),
                "per_liter": cfg.get("per_liter", 0.0),
                "per_kg": cfg.get("per_kg", 0.0),
                "min_cost": cfg.get("min_cost", 0.0),
            }
        )
    return pd.DataFrame(rows)


def render() -> None:
    st.title("📦 Тарифы маркетплейсов")
    st.caption(
        "Служебный режим. Здесь редактируются официальные условия МП. "
        "Каждое сохранение фиксирует дату, источник и комментарий в истории версий."
    )

    marketplaces = list_marketplaces()
    if not marketplaces:
        st.error("Тарифы не найдены в data/tariffs/.")
        return

    mp_id = st.selectbox(
        "Маркетплейс",
        [m["id"] for m in marketplaces],
        format_func=lambda x: next((m["name"] for m in marketplaces if m["id"] == x), x),
    )

    try:
        config = load_tariff(mp_id)
    except TariffError as exc:
        st.error(str(exc))
        return

    src = config.get("source", {})
    st.markdown(f"**Источник:** [{src.get('url', '—')}]({src.get('url', '#')})")
    st.markdown(f"**Актуальность:** {src.get('updated_at', '—')}")
    if src.get("note"):
        st.info(src["note"])

    with st.form("tariff_form"):
        st.subheader("Общие параметры")
        c1, c2 = st.columns(2)
        with c1:
            source_url = st.text_input("Ссылка на источник", value=src.get("url", ""))
            acquiring = st.number_input(
                "Эквайринг / обработка платежей, %",
                min_value=0.0, max_value=100.0, step=0.1,
                value=float(config.get("acquiring_pct", 0.0)),
            )
            storage = st.number_input(
                "Хранение, ₽/л·день", min_value=0.0, step=0.01,
                value=float(config.get("storage_per_liter_day", 0.0)),
            )
        with c2:
            return_logistics = st.number_input(
                "Обратная логистика, ₽", min_value=0.0, step=1.0,
                value=float(config.get("return_logistics", 0.0)),
            )
            returns_processing = st.number_input(
                "Обработка возврата, ₽", min_value=0.0, step=1.0,
                value=float(config.get("returns_processing", 0.0)),
            )

        st.subheader("Комиссии по категориям, %")
        cats_edited = st.data_editor(
            _categories_df(config), num_rows="dynamic", use_container_width=True,
            column_config={
                "category": st.column_config.TextColumn("Категория"),
                "commission_pct": st.column_config.NumberColumn("Комиссия, %", min_value=0.0, max_value=100.0),
            },
            key="edit_categories",
        )

        st.subheader("Логистика по схемам")
        log_edited = st.data_editor(
            _logistics_df(config), num_rows="dynamic", use_container_width=True,
            column_config={
                "scheme": st.column_config.TextColumn("Схема"),
                "base_cost": st.column_config.NumberColumn("База, ₽", min_value=0.0),
                "per_liter": st.column_config.NumberColumn("₽/литр", min_value=0.0),
                "per_kg": st.column_config.NumberColumn("₽/кг", min_value=0.0),
                "min_cost": st.column_config.NumberColumn("Мин., ₽", min_value=0.0),
            },
            key="edit_logistics",
        )

        st.subheader("Дополнительные статьи расходов")
        fees_df = pd.DataFrame(config.get("extra_fees", []))
        for col in ["name", "base", "rate", "amount", "note"]:
            if col not in fees_df.columns:
                fees_df[col] = [] if fees_df.empty else ""
        fees_edited = st.data_editor(
            fees_df, num_rows="dynamic", use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Статья"),
                "base": st.column_config.SelectboxColumn("База", options=EXTRA_FEE_BASES),
                "rate": st.column_config.NumberColumn("Ставка, %", min_value=0.0),
                "amount": st.column_config.NumberColumn("Фикс, ₽", min_value=0.0),
                "note": st.column_config.TextColumn("Комментарий"),
            },
            key="edit_fees",
        )

        comment = st.text_area("Комментарий к изменению", placeholder="Например: обновил комиссии по оферте от 07.2026")
        submitted = st.form_submit_button("💾 Сохранить тариф", type="primary")

    if submitted:
        try:
            new_config = dict(config)
            new_config["acquiring_pct"] = float(acquiring)
            new_config["storage_per_liter_day"] = float(storage)
            new_config["return_logistics"] = float(return_logistics)
            new_config["returns_processing"] = float(returns_processing)

            new_config["categories"] = {
                str(r["category"]): {"commission_pct": float(r["commission_pct"] or 0.0)}
                for _, r in cats_edited.iterrows()
                if str(r.get("category", "")).strip()
            }
            new_config["logistics"] = {
                str(r["scheme"]): {
                    "base_cost": float(r["base_cost"] or 0.0),
                    "per_liter": float(r["per_liter"] or 0.0),
                    "per_kg": float(r["per_kg"] or 0.0),
                    "min_cost": float(r["min_cost"] or 0.0),
                }
                for _, r in log_edited.iterrows()
                if str(r.get("scheme", "")).strip()
            }
            new_config["schemes"] = list(new_config["logistics"].keys()) or config.get("schemes", [])
            new_config["extra_fees"] = (
                fees_edited.fillna(0).to_dict("records") if not fees_edited.empty else []
            )

            save_tariff(mp_id, new_config, comment=comment, source_url=source_url)
            st.success("Тариф сохранён. История версий обновлена.")
        except (TariffError, ValueError, KeyError) as exc:
            st.error(f"Не удалось сохранить: {exc}")

    st.divider()
    st.subheader("🕓 История изменений")
    history = load_tariff(mp_id).get("history", [])
    if history:
        st.dataframe(pd.DataFrame(history[::-1]), hide_index=True, use_container_width=True)
    else:
        st.caption("История пуста.")
