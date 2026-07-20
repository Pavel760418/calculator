# Как обновлять тарифы маркетплейсов

Приложение построено по принципу **data-driven**: все ставки хранятся в
`data/tariffs/*.json`, а код расчёта от них не зависит. Обновление условий —
это редактирование данных, а не логики.

## Модель обновления (полуавтоматическая)

Автоматический парсинг оферт ненадёжен (авторизация продавца, частая смена
вёрстки, защита от роботов), поэтому рекомендуется полуавтоматический цикл:

1. **Сверьте ставки** в официальном источнике:
   - Ozon Seller — https://seller.ozon.com/
   - Wildberries (WB Partners) — https://seller.wildberries.ru/terms
   - Яндекс Маркет для партнёров — https://partner.market.yandex.com/
2. **Обновите значения** одним из способов:
   - через интерфейс: страница **«Тарифы маркетплейсов»** (рекомендуется);
   - вручную: отредактируйте соответствующий `data/tariffs/<mp>.json`.
3. **Зафиксируйте изменение**: при сохранении через интерфейс автоматически
   пишется запись в `history` (дата, источник, комментарий). При ручной правке
   добавьте такую запись самостоятельно.

## Структура файла тарифа

```jsonc
{
  "id": "ozon",
  "name": "Ozon",
  "source": { "url": "...", "note": "...", "updated_at": "YYYY-MM-DD" },
  "default_scheme": "FBO",
  "schemes": ["FBO", "FBS", "realFBS"],
  "acquiring_pct": 1.5,                 // эквайринг/обработка платежей, %
  "categories": {                        // комиссия по категориям, %
    "default": { "commission_pct": 15.0 }
  },
  "logistics": {                         // логистика на 1 отправление
    "FBO": { "base_cost": 76, "per_liter": 12, "per_kg": 0, "min_cost": 76 }
  },
  "storage_per_liter_day": 0.15,         // хранение, ₽/л·день
  "return_logistics": 60,                // обратная логистика, ₽
  "returns_processing": 0,               // обработка возврата, ₽
  "extra_fees": [                        // произвольные статьи (data-driven)
    { "name": "Последняя миля", "base": "price", "rate": 5.5, "amount": 0 }
  ],
  "history": [ { "updated_at": "...", "comment": "...", "source_url": "..." } ]
}
```

### Базы начисления `extra_fees.base`
- `price` — процент от цены (`rate`, %)
- `revenue` — процент от выручки после комиссии (`rate`, %)
- `cogs` — процент от себестоимости (`rate`, %)
- `fixed` — фиксированная сумма на единицу (`amount`, ₽)

## Добавление нового маркетплейса

1. Создайте `data/tariffs/<new_id>.json`. Быстрый шаблон:
   ```bash
   python -c "import json,sys; from sources.fetch_tariffs import new_tariff_template; \
   print(json.dumps(new_tariff_template('kazanexpress','KazanExpress','https://...'), ensure_ascii=False, indent=2))" \
   > data/tariffs/kazanexpress.json
   ```
2. Заполните комиссии, логистику и прочее.
3. Приложение подхватит новый файл автоматически — код менять не нужно.

## Валидация тарифов

```bash
python -m sources.fetch_tariffs
```
Выведет статус каждого файла (`OK` или список проблем).
