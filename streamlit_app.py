"""Точка входа для Streamlit Community Cloud.

Streamlit Community Cloud по умолчанию ищет файл `streamlit_app.py` в корне
репозитория. Этот файл — тонкая обёртка над `app.py`: импорт `app` выполняет
`st.set_page_config(...)` на уровне модуля (первой командой Streamlit), после
чего вызывается основная навигация `app.main()`.

Локально можно запускать любым из способов:
    streamlit run streamlit_app.py
    streamlit run app.py
"""
from __future__ import annotations

import app

if __name__ == "__main__":
    app.main()
else:
    # Streamlit исполняет скрипт как модуль верхнего уровня (__name__ != "__main__"),
    # поэтому запускаем навигацию и в этом случае.
    app.main()
