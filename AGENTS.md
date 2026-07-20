# AGENTS.md

## Cursor Cloud specific instructions

This repository is a single self-contained static page: `index.html` (a Russian-language
"Калькулятор Юнит-Экономики Маркетплейсов" / Marketplace Unit Economics Calculator). All
CSS and JavaScript are inlined in that one file.

- No dependencies, package manager, build step, or automated tests exist. There is nothing to install; the startup update script is a no-op.
- Run (development): serve the folder statically and open the page, e.g. `python3 -m http.server 8000` then visit `http://localhost:8000/index.html`. Opening `index.html` directly as a `file://` URL also works.
- Lint / test / build: none configured. "Building" is unnecessary since the file is served as-is.
- The calculator auto-runs `calculate()` on page load (`window.onload`), so results are populated immediately; editing inputs and clicking "🔄 Рассчитать" recomputes them.
