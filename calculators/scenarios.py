"""Применение сценариев (базовый/оптимистичный/пессимистичный/ручной).

Сценарий — это набор мультипликаторов к части входных параметров. Он не меняет
формулы расчёта, а лишь корректирует входы, что удобно для стресс-анализа.
"""
from __future__ import annotations

from dataclasses import replace

from configs.settings import SCENARIOS
from .models import ProductInput, MarketplaceParams


def apply_scenario(
    product: ProductInput,
    params: MarketplaceParams,
    scenario_name: str,
    overrides: dict | None = None,
) -> tuple[ProductInput, MarketplaceParams]:
    """Возвращает скорректированные (product, params) для заданного сценария.

    overrides позволяет переопределить мультипликаторы для «Ручного» сценария.
    """
    cfg = dict(SCENARIOS.get(scenario_name, SCENARIOS["Базовый"]))
    if overrides:
        cfg.update(overrides)

    new_price = product.price * cfg.get("price", 1.0)
    new_drr = product.drr_pct * cfg.get("drr", 1.0)
    new_buyout = min(max(product.buyout_pct + cfg.get("buyout_delta", 0.0), 1.0), 100.0)

    new_product = replace(
        product, price=new_price, drr_pct=new_drr, buyout_pct=new_buyout
    )

    commission_mult = cfg.get("commission", 1.0)
    logistics_mult = cfg.get("logistics", 1.0)
    storage_mult = cfg.get("storage", 1.0)

    new_params = replace(
        params,
        commission_pct=params.commission_pct * commission_mult,
        logistics_to=params.logistics_to * logistics_mult,
        return_logistics=params.return_logistics * logistics_mult,
        storage_per_liter_day=params.storage_per_liter_day * storage_mult,
    )

    return new_product, new_params
