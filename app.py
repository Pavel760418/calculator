"""Точка входа Streamlit-приложения «Калькулятор юнит-экономики маркетплейсов».

Запуск:  streamlit run app.py

Навигация построена через st.navigation, что даёт чистые русскоязычные названия
страниц без привязки к именам файлов.
"""
from __future__ import annotations

import streamlit as st

from configs.settings import APP_TITLE, APP_ICON
from ui import main_calc, tariffs, compare, scenarios, help as help_page

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")


def main() -> None:
    pages = [
        st.Page(main_calc.render, title="Калькулятор", icon="📊", default=True),
        st.Page(compare.render, title="Сравнение МП", icon="⚖️"),
        st.Page(scenarios.render, title="Сценарии", icon="🎯"),
        st.Page(tariffs.render, title="Тарифы маркетплейсов", icon="📦"),
        st.Page(help_page.render, title="Справка", icon="ℹ️"),
    ]
    st.navigation(pages).run()


if __name__ == "__main__":
    main()
