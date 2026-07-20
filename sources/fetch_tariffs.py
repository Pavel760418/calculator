"""Вспомогательный (полуавтоматический) модуль обновления тарифов.

Автоматический парсинг оферт маркетплейсов ненадёжен: страницы требуют
авторизации продавца, часто меняют вёрстку и защищены от роботов. Поэтому
рекомендуемая модель — **полуавтоматическая**:

1. Оператор вручную сверяет ставки в личном кабинете / оферте маркетплейса.
2. Заполняет значения через страницу «Тарифы маркетплейсов» в приложении
   (или правит JSON в data/tariffs/ вручную).
3. Каждое изменение фиксируется в истории версий (дата, источник, комментарий).

Этот модуль предоставляет утилиты, которые помогают в шаге обновления:
- валидация структуры тарифа;
- шаблон нового тарифа для нового маркетплейса.

Функцию реального парсинга (`fetch_from_url`) намеренно оставляем заглушкой:
подключайте её точечно под конкретный источник, только если он отдаёт
машиночитаемые данные и это не нарушает условия использования.
"""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED_KEYS = {"id", "name", "source", "schemes", "categories", "logistics"}


def validate_tariff(config: dict) -> list[str]:
    """Проверяет структуру тарифа. Возвращает список проблем (пустой = ок)."""
    problems: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in config:
            problems.append(f"Отсутствует обязательный ключ: '{key}'")

    src = config.get("source", {})
    if not src.get("url"):
        problems.append("Не указан источник (source.url)")
    if not src.get("updated_at"):
        problems.append("Не указана дата актуальности (source.updated_at)")

    cats = config.get("categories", {})
    if "default" not in cats:
        problems.append("В categories должна быть запись 'default'")

    return problems


def new_tariff_template(mp_id: str, name: str, source_url: str) -> dict:
    """Возвращает пустой шаблон тарифа для нового маркетплейса."""
    return {
        "id": mp_id,
        "name": name,
        "source": {"url": source_url, "note": "Заполните описание источника.", "updated_at": ""},
        "currency": "RUB",
        "default_scheme": "FBO",
        "schemes": ["FBO", "FBS"],
        "acquiring_pct": 0.0,
        "categories": {"default": {"commission_pct": 0.0}},
        "logistics": {
            "FBO": {"base_cost": 0.0, "per_liter": 0.0, "per_kg": 0.0, "min_cost": 0.0},
            "FBS": {"base_cost": 0.0, "per_liter": 0.0, "per_kg": 0.0, "min_cost": 0.0},
        },
        "storage_per_liter_day": 0.0,
        "return_logistics": 0.0,
        "returns_processing": 0.0,
        "extra_fees": [],
        "history": [],
    }


def fetch_from_url(url: str) -> dict:  # pragma: no cover - точка расширения
    """Заглушка автоматического парсинга.

    Реализуйте под конкретный официальный источник только при наличии
    машиночитаемого API/выгрузки и допустимости автоматического доступа.
    """
    raise NotImplementedError(
        "Автоматический парсинг не реализован. Используйте полуавтоматическую "
        "модель: обновляйте тарифы через страницу «Тарифы маркетплейсов»."
    )


if __name__ == "__main__":
    # Мини-проверка всех тарифов в data/tariffs.
    base = Path(__file__).resolve().parent.parent / "data" / "tariffs"
    for path in sorted(base.glob("*.json")):
        cfg = json.loads(path.read_text(encoding="utf-8"))
        issues = validate_tariff(cfg)
        status = "OK" if not issues else "; ".join(issues)
        print(f"{path.name}: {status}")
