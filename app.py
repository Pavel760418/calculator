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
    # url_path задаём явно и уникально: иначе st.navigation выводит его из имени
    # функции (у всех страниц функция называется render → конфликт путей).
    pages = [
        st.Page(main_calc.render, title="Калькулятор", icon="📊", url_path="calculator", default=True),
        st.Page(compare.render, title="Сравнение МП", icon="⚖️", url_path="compare"),
        st.Page(scenarios.render, title="Сценарии", icon="🎯", url_path="scenarios"),
        st.Page(tariffs.render, title="Тарифы маркетплейсов", icon="📦", url_path="tariffs"),
        st.Page(help_page.render, title="Справка", icon="ℹ️", url_path="help"),
    ]
    st.navigation(pages).run()


if __name__ == "__main__":
    main()
