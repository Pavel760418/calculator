"""Слой доступа к данным: чтение/запись тарифов маркетплейсов.

Тарифы хранятся в data/tariffs/*.json. Каждое сохранение фиксирует запись в
истории версий (updated_at, комментарий, источник), что даёт «data-driven»
обновление условий без изменения кода.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from configs.settings import TARIFFS_DIR
from calculators.models import MarketplaceParams


class TariffError(Exception):
    """Ошибка чтения/записи тарифов."""


def _tariff_path(mp_id: str) -> Path:
    return TARIFFS_DIR / f"{mp_id}.json"


def list_marketplaces() -> list[dict]:
    """Список доступных маркетплейсов: [{id, name}] по файлам в data/tariffs."""
    result: list[dict] = []
    if not TARIFFS_DIR.exists():
        return result
    for path in sorted(TARIFFS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            result.append({"id": data.get("id", path.stem), "name": data.get("name", path.stem)})
        except (json.JSONDecodeError, OSError):
            # Битый файл не должен ронять всё приложение.
            continue
    return result


def load_tariff(mp_id: str) -> dict:
    """Загружает конфиг тарифа одного маркетплейса."""
    path = _tariff_path(mp_id)
    if not path.exists():
        raise TariffError(f"Тариф '{mp_id}' не найден: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TariffError(f"Некорректный JSON в тарифе '{mp_id}': {exc}") from exc


def load_all_tariffs() -> dict[str, dict]:
    """Загружает все тарифы: {mp_id: config}."""
    tariffs: dict[str, dict] = {}
    for item in list_marketplaces():
        try:
            tariffs[item["id"]] = load_tariff(item["id"])
        except TariffError:
            continue
    return tariffs


def save_tariff(mp_id: str, config: dict, comment: str = "", source_url: str = "") -> None:
    """Сохраняет тариф на диск с записью в историю версий."""
    config = dict(config)
    today = date.today().isoformat()

    src = dict(config.get("source", {}))
    if source_url:
        src["url"] = source_url
    src["updated_at"] = today
    config["source"] = src

    history = list(config.get("history", []))
    history.append(
        {
            "updated_at": today,
            "comment": comment or "Ручное обновление тарифов через интерфейс.",
            "source_url": source_url or src.get("url", ""),
        }
    )
    config["history"] = history

    path = _tariff_path(mp_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        raise TariffError(f"Не удалось сохранить тариф '{mp_id}': {exc}") from exc


def resolve_logistics_cost(logistics_cfg: dict, weight_kg: float, volume_l: float) -> float:
    """Логистика на 1 отправление: base + per_liter*V + per_kg*W, но не ниже min."""
    if not logistics_cfg:
        return 0.0
    base = float(logistics_cfg.get("base_cost", 0.0))
    per_liter = float(logistics_cfg.get("per_liter", 0.0))
    per_kg = float(logistics_cfg.get("per_kg", 0.0))
    min_cost = float(logistics_cfg.get("min_cost", 0.0))
    cost = base + per_liter * max(volume_l, 0.0) + per_kg * max(weight_kg, 0.0)
    return max(cost, min_cost)


def resolve_params(
    config: dict,
    scheme: str,
    category: str,
    weight_kg: float,
    volume_l: float,
    overrides: dict | None = None,
) -> MarketplaceParams:
    """Строит MarketplaceParams из конфига тарифа под конкретные условия.

    overrides — ручные правки пользователя (перекрывают значения из тарифа).
    Поддерживаемые ключи: commission_pct, acquiring_pct, logistics_to,
    return_logistics, returns_processing, storage_per_liter_day, extra_fees.
    """
    overrides = overrides or {}

    categories = config.get("categories", {})
    cat = categories.get(category) or categories.get("default") or {}
    commission_pct = float(cat.get("commission_pct", 0.0))

    logistics_cfg = config.get("logistics", {}).get(scheme, {})
    logistics_to = resolve_logistics_cost(logistics_cfg, weight_kg, volume_l)

    params = MarketplaceParams(
        name=config.get("name", config.get("id", "МП")),
        scheme=scheme,
        commission_pct=float(overrides.get("commission_pct", commission_pct)),
        acquiring_pct=float(overrides.get("acquiring_pct", config.get("acquiring_pct", 0.0))),
        logistics_to=float(overrides.get("logistics_to", logistics_to)),
        return_logistics=float(overrides.get("return_logistics", config.get("return_logistics", 0.0))),
        returns_processing=float(overrides.get("returns_processing", config.get("returns_processing", 0.0))),
        storage_per_liter_day=float(
            overrides.get("storage_per_liter_day", config.get("storage_per_liter_day", 0.0))
        ),
        extra_fees=list(overrides.get("extra_fees", config.get("extra_fees", []))),
    )
    return params
