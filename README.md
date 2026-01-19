# Billing Core (Domain) + FastAPI Demo

Переиспользуемое доменное ядро биллинга (Python-пакет) + демо API на FastAPI со Swagger UI.  
Фокус: **чистая бизнес-логика**, **архитектура по слоям**, **тестируемость**, **запуск в Docker**.

---

## Что умеет

### Plans (тарифные планы)
Поддерживаются 3 типа планов:

- **Free** — цена 0
- **Flat monthly** — фиксированная цена в месяц (пример: `20 EUR`)
- **Per-seat monthly** — `base + per_seat * seats` (пример: `10 + 5 * seats`)

План имеет:
- `code` (уникальный идентификатор: `FREE`, `PRO`, `TEAM`)
- `name`
- `currency`
- полиморфную стратегию расчёта цены

### Subscriptions (подписки)
Подписка привязана к:
- `customer_id`
- `plan_code`

Состояния:
- `trialing`
- `active`
- `canceled`

Операции:
- создать подписку (с trial или без)
- отменить
- апгрейд плана в середине периода (**proration**)
- сменить `seats` (**proration**)
- применить промокод

Computed свойства:
- `is_active`
- `days_left_in_period`

### Invoices (инвойсы)
Инвойс создаётся на события:
- создание платной подписки (если не trial и не free)
- upgrade / change seats (proration доплата или кредит)

Статусы:
- `draft`
- `issued`
- `paid`

Операции:
- issue
- pay

### Promo Codes (промокоды)
Типы:
- процентный (например, `-20%`)
- фиксированный (например, `-5 EUR`)

Ограничения:
- действует до даты `valid_until` (включительно)
- одноразовый/многоразовый (для демо — по `customer_id`)
- итог не может быть ниже 0

---

## Архитектура

Проект разделён на слои:

- **domain** — чистая бизнес-логика (не знает про HTTP, FastAPI, БД)
- **application** — use-case’ы/оркестрация (сервисы + транзакционный контекст)
- **infrastructure** — реализации репозиториев (в демо: in-memory)
- **api** — FastAPI слой (эндпоинты + схемы + Swagger)

```
src/billing_core/
  domain/
  application/
  infrastructure/
  api/
tests/
```

---

## Стек

- Python 3.13
- FastAPI + Swagger UI
- Pytest + coverage
- Ruff (lint + format)
- Docker / docker-compose

---

## Быстрый старт (локально)

### 1) Установка
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -U pip
pip install -e ".[dev,api]"
```

### 2) Запуск API
```bash
uvicorn billing_core.api.main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/healthz`

---

## Запуск в Docker

### 1) Поднять контейнер
```bash
docker compose up --build
```

### 2) Проверить
- `http://localhost:8000/healthz`
- `http://localhost:8000/docs`

Остановить:
```bash
docker compose down
```

---

## Полезные команды разработки

### Ruff
```bash
ruff format .
ruff check .
```

### Тесты + покрытие
```bash
pytest --cov
```

---

## API Endpoints

### Health
- `GET /healthz`

### Plans
- `POST /plans` — создать план
- `GET /plans` — список планов
- `GET /plans/{code}` — получить план

### Subscriptions
- `POST /subscriptions` — создать подписку
- `GET /subscriptions/{id}` — получить подписку
- `POST /subscriptions/{id}/cancel`
- `POST /subscriptions/{id}/upgrade`
- `POST /subscriptions/{id}/change-seats`
- `POST /subscriptions/{id}/apply-promo`

### Invoices
- `GET /invoices/{id}`
- `POST /invoices/{id}/issue`
- `POST /invoices/{id}/pay`

### Promos
- `POST /promos` — создать промокод

---

## Примеры запросов (curl)

### 1) Создать подписку (платный план)
```bash
curl -X POST http://127.0.0.1:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_1",
    "plan_code": "PRO",
    "start_date": "2026-01-01",
    "seats": 1,
    "trial_days": 0,
    "period_days": 30
  }'
```

Ответ вернёт `subscription` и (если платно) `invoice_id`.

### 2) Upgrade подписки (proration)
```bash
curl -X POST http://127.0.0.1:8000/subscriptions/<SUB_ID>/upgrade \
  -H "Content-Type: application/json" \
  -d '{
    "new_plan_code": "TEAM",
    "change_date": "2026-01-16"
  }'
```

### 3) Получить инвойс
```bash
curl http://127.0.0.1:8000/invoices/<INVOICE_ID>
```

### 4) Выпустить и оплатить инвойс
```bash
curl -X POST http://127.0.0.1:8000/invoices/<INVOICE_ID>/issue
curl -X POST http://127.0.0.1:8000/invoices/<INVOICE_ID>/pay
```
