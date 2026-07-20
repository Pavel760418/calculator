# AGENTS.md

## Cursor Cloud specific instructions

This repository contains two things:

1. `app.py` + `calculators/ services/ ui/ configs/ utils/ data/` — the primary
   product: a **Streamlit** app "Калькулятор юнит-экономики маркетплейсов"
   (marketplace unit-economics calculator). Data-driven: tariffs live in
   `data/tariffs/*.json`, separate from the calculation engine.
2. `index.html` — the legacy self-contained static calculator (still served on
   GitHub Pages). No build/deps; open directly or via `python3 -m http.server`.

### Streamlit app — run / test

- Dependencies: `pip install -r requirements.txt` (Streamlit, pandas, plotly). The startup update script already runs this.
- Run (dev): `python3 -m streamlit run app.py --server.port 8501 --server.headless true`, then open `http://localhost:8501`. Note the `streamlit` console script installs to `~/.local/bin` (not always on PATH) — invoking via `python3 -m streamlit` is the reliable form.
- No automated test suite. Validate tariff JSON integrity with `python3 -m sources.fetch_tariffs` (prints OK / issues per file).
- Lint/build: none configured (pure Python + Streamlit; no compile step).

### Non-obvious gotchas

- Navigation uses `st.navigation` with page callables all named `render`; each `st.Page` MUST set a unique `url_path` or Streamlit raises a duplicate-URL error.
- Cross-page state: the shared product sidebar keys are "touched" (re-committed) in `ui/state.py:init_state()` on every run. Without this, Streamlit garbage-collects widget-key state when switching pages and inputs reset to 0. Keep that touch loop if editing state handling.
- `runOnSave` is enabled in `.streamlit/config.toml`; editing many modules rapidly can leave a stale import cache — restart the Streamlit process after multi-file edits if you see a transient `KeyError: 'ui.<module>'`.
- Tariffs are data, not code: edit via the "Тарифы маркетплейсов" page (writes `data/tariffs/*.json` + appends version history) or edit the JSON directly. Bundled tariff values are baseline and meant to be verified against official seller offers. See `docs/UPDATING_TARIFFS.md`.
