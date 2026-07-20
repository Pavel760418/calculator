"""Доменные модели данных для расчёта юнит-экономики.

Модели намеренно «плоские» и не зависят ни от Streamlit, ни от формата хранения
тарифов — это делает бизнес-логику тестируемой и переиспользуемой.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class ProductInput:
    """Входные параметры по товару и налогам (задаёт пользователь)."""

    price: float                      # цена продажи покупателю, ₽
    cost_price: float                 # закупочная себестоимость на единицу, ₽
    weight_kg: float = 0.0
    volume_l: float = 0.0
    category: str = "default"
    tax_regime: str = "УСН Доходы-Расходы 15%"
    drr_pct: float = 0.0              # ДРР — реклама как % от цены
    ad_fixed: float = 0.0            # доп. реклама фикс. суммой на единицу, ₽
    buyout_pct: float = 100.0        # процент выкупа (0..100)
    defect_pct: float = 0.0          # процент брака/потерь от себестоимости
    extra_cogs: float = 0.0          # доп. себестоимость на единицу (упаковка и т.п.), ₽
    storage_days: int = 15           # срок хранения для оценки, дней
    fixed_costs_month: float = 0.0   # постоянные расходы в месяц, ₽ (для точки безубыточности в штуках)


@dataclass
class MarketplaceParams:
    """Тарифы маркетплейса, уже приведённые к конкретной схеме/категории.

    Все поля можно переопределить вручную в интерфейсе — движок не знает,
    откуда взялись значения (из JSON, из ручной правки или из сценария).
    """

    name: str
    scheme: str
    commission_pct: float = 0.0
    acquiring_pct: float = 0.0
    logistics_to: float = 0.0        # логистика до покупателя на 1 отправление, ₽
    return_logistics: float = 0.0    # обратная логистика на 1 возврат, ₽
    returns_processing: float = 0.0  # обработка возврата, ₽
    storage_per_liter_day: float = 0.0
    extra_fees: list[dict] = field(default_factory=list)


@dataclass
class UnitEconomics:
    """Результат расчёта юнит-экономики на единицу товара."""

    revenue: float = 0.0
    commission: float = 0.0
    acquiring: float = 0.0
    logistics: float = 0.0
    storage: float = 0.0
    returns_cost: float = 0.0
    advertising: float = 0.0
    other_costs: float = 0.0
    cogs: float = 0.0
    tax: float = 0.0

    total_mp_costs: float = 0.0       # все расходы на стороне МП (без себестоимости и налога)
    gross_profit: float = 0.0         # выручка − себестоимость
    operating_profit: float = 0.0     # прибыль до налога
    net_profit: float = 0.0           # чистая прибыль на единицу
    margin_pct: float = 0.0           # маржинальность к цене, %
    markup_pct: float = 0.0           # наценка к себестоимости, %
    roi_pct: float = 0.0              # рентабельность инвестиций (к себестоимости), %
    romi_pct: float = 0.0             # рентабельность рекламы, %

    break_even_price: float = 0.0     # минимальная цена безубыточности, ₽
    break_even_units: float = 0.0     # точка безубыточности в штуках (если заданы пост. расходы)

    other_fees_detail: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
