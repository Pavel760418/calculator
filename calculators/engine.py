"""Движок расчёта юнит-экономики.

Ключевые идеи модели:

1. Расходы, зависящие от процента выкупа (логистика «туда» и «обратно»),
   пересчитываются на одну ПРОДАННУЮ единицу. Если выкуп b (доля), то чтобы
   продать 1 шт. нужно отгрузить 1/b шт., а (1-b)/b шт. вернутся.
2. Комиссия, эквайринг и реклама начисляются на фактическую продажу (цену).
3. Точка безубыточности по цене находится численно (бисекция) — это позволяет
   поддерживать произвольную структуру расходов без переписывания формул.
"""
from __future__ import annotations

from dataclasses import replace

from configs.settings import TAX_REGIMES
from .models import ProductInput, MarketplaceParams, UnitEconomics


def _compute_tax(tax_regime: str, revenue: float, profit_before_tax: float) -> float:
    """Расчёт налога на единицу по выбранному режиму."""
    regime = TAX_REGIMES.get(tax_regime)
    if not regime:
        return 0.0
    if regime["type"] == "income":
        return revenue * regime["rate"]
    if regime["type"] == "profit":
        return max(profit_before_tax, 0.0) * regime["rate"]
    return 0.0  # fixed / патент — на единицу не относим


def _extra_fees_amount(
    extra_fees: list[dict], price: float, revenue_after_commission: float, cogs: float
) -> tuple[float, list[dict]]:
    """Суммирует дополнительные (пользовательские) статьи расходов.

    Каждая статья описывается базой начисления, что делает модель data-driven:
    добавление новой статьи не требует правок в коде движка.
    """
    total = 0.0
    detail: list[dict] = []
    for fee in extra_fees or []:
        base = fee.get("base", "fixed")
        rate = float(fee.get("rate", 0.0) or 0.0)
        amount = float(fee.get("amount", 0.0) or 0.0)
        if base == "price":
            value = price * rate / 100.0
        elif base == "revenue":
            value = revenue_after_commission * rate / 100.0
        elif base == "cogs":
            value = cogs * rate / 100.0
        else:  # fixed
            value = amount
        total += value
        detail.append({"name": fee.get("name", "Прочее"), "value": value})
    return total, detail


def _compute_core(product: ProductInput, params: MarketplaceParams) -> UnitEconomics:
    """Расчёт всех показателей КРОМЕ точки безубыточности.

    Выделено отдельно, чтобы break_even_price мог многократно вызывать расчёт
    без рекурсии.
    """
    price = max(product.price, 0.0)

    # Доля выкупа (0..1). Защищаемся от деления на ноль.
    buyout = min(max(product.buyout_pct, 1.0), 100.0) / 100.0
    shipped_per_sale = 1.0 / buyout
    returns_qty = shipped_per_sale - 1.0

    # --- Расходы маркетплейса, зависящие от цены ---
    commission = price * params.commission_pct / 100.0
    acquiring = price * params.acquiring_pct / 100.0
    revenue_after_commission = price - commission - acquiring

    # --- Логистика (с учётом невыкупов) ---
    forward_logistics = params.logistics_to * shipped_per_sale
    return_logistics = (params.return_logistics + params.returns_processing) * returns_qty
    logistics = forward_logistics + return_logistics
    returns_cost = return_logistics

    # --- Хранение ---
    storage = params.storage_per_liter_day * product.volume_l * product.storage_days

    # --- Себестоимость ---
    cogs = product.cost_price + product.extra_cogs
    defect = cogs * product.defect_pct / 100.0
    cogs_total = cogs + defect

    # --- Реклама ---
    advertising = price * product.drr_pct / 100.0 + product.ad_fixed

    # --- Прочие статьи (data-driven) ---
    other_costs, other_detail = _extra_fees_amount(
        params.extra_fees, price, revenue_after_commission, cogs_total
    )

    total_mp_costs = commission + acquiring + logistics + storage + other_costs

    operating_profit = (
        price
        - commission
        - acquiring
        - logistics
        - storage
        - other_costs
        - advertising
        - cogs_total
    )

    tax = _compute_tax(product.tax_regime, price, operating_profit)
    net_profit = operating_profit - tax

    gross_profit = price - cogs_total

    margin_pct = (net_profit / price * 100.0) if price > 0 else 0.0
    markup_pct = (net_profit / cogs_total * 100.0) if cogs_total > 0 else 0.0
    romi_pct = (net_profit / advertising * 100.0) if advertising > 0 else 0.0

    return UnitEconomics(
        revenue=price,
        commission=commission,
        acquiring=acquiring,
        logistics=logistics,
        storage=storage,
        returns_cost=returns_cost,
        advertising=advertising,
        other_costs=other_costs,
        cogs=cogs_total,
        tax=tax,
        total_mp_costs=total_mp_costs,
        gross_profit=gross_profit,
        operating_profit=operating_profit,
        net_profit=net_profit,
        margin_pct=margin_pct,
        markup_pct=markup_pct,
        roi_pct=markup_pct,
        romi_pct=romi_pct,
        other_fees_detail=other_detail,
    )


def break_even_price(
    product: ProductInput, params: MarketplaceParams, tol: float = 0.01
) -> float:
    """Численно находит минимальную цену, при которой чистая прибыль ≥ 0.

    Бисекция устойчива к любой структуре расходов (в т.ч. к процентным статьям
    и налогам), поэтому не требует аналитических формул.
    """

    def net_at(price: float) -> float:
        return _compute_core(replace(product, price=price), params).net_profit

    low = 0.0
    high = max(product.cost_price, product.price, 100.0) * 20.0 + 1000.0

    if net_at(high) < 0:
        return float("inf")  # безубыточность недостижима при текущих расходах
    if net_at(low) >= 0:
        return 0.0

    for _ in range(100):
        mid = (low + high) / 2.0
        if net_at(mid) >= 0:
            high = mid
        else:
            low = mid
        if high - low < tol:
            break
    return round(high, 2)


def compute_unit_economics(
    product: ProductInput, params: MarketplaceParams
) -> UnitEconomics:
    """Полный расчёт юнит-экономики, включая точку безубыточности."""
    result = _compute_core(product, params)
    result.break_even_price = break_even_price(product, params)

    if product.fixed_costs_month > 0 and result.net_profit > 0:
        result.break_even_units = product.fixed_costs_month / result.net_profit
    else:
        result.break_even_units = 0.0

    return result
