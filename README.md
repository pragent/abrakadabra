# corezoid-monobank-rates

Модуль для Corezoid **Git Call** — отримує актуальні курси валют від [api.monobank.ua](https://api.monobank.ua) і повертає результат у Corezoid task.

## Як це працює

```
Corezoid Process
  └── Start  →  Git Call (цей репо)  →  End
                    │
                    ├── приймає: name, currencies, api_token
                    ├── звертається до api.monobank.ua
                    └── повертає: greeting, rates[], fetched_at
```

## Налаштування в Corezoid

### 1. Git Call node settings

| Поле | Значення |
|------|----------|
| Language | Python |
| Repo URL | `https://github.com/YOUR_USERNAME/corezoid-monobank-rates` |
| Tag / Branch | `main` або `master` — **перевір яка гілка є в репо** |
| Project path | *(порожньо — usercode.py в корені)* |
| Build command | *(порожньо — залежностей немає)* |

> ⚠️ **Важливо:** помилка `Git reference is invalid or does not exist` означає що гілка не знайдена.
> Перевір назву гілки в GitHub (може бути `main` або `master`) і вкажи точно її.

### 2. Вхідні параметри task

| Параметр | Тип | Обов'язковий | Опис |
|----------|-----|:---:|------|
| `name` | string | ✅ | Ім'я для привітання |
| `currencies` | array[int] | ❌ | Коди валют ISO 4217. Default: `[840, 978]` (USD, EUR) |
| `api_token` | string | ❌ | Monobank API token (для підвищеного rate limit) |

**Популярні коди валют:**
- `840` — USD
- `978` — EUR  
- `826` — GBP
- `756` — CHF
- `985` — PLN

### 3. Вихідні параметри task

```json
{
  "greeting": "Привіт, Іванко! Ось курси валют від api.monobank.ua",
  "rates": [
    {
      "currency": "USD",
      "code": 840,
      "buy": 41.50,
      "sell": 42.10,
      "cross": null,
      "updated_at": "2026-09-24T10:00:00+00:00"
    },
    {
      "currency": "EUR",
      "code": 978,
      "buy": 45.20,
      "sell": 46.00,
      "cross": null,
      "updated_at": "2026-09-24T10:00:00+00:00"
    }
  ],
  "source": "https://api.monobank.ua/bank/currency",
  "fetched_at": "2026-09-24T10:01:23+00:00"
}
```

## Структура репозиторію

```
corezoid-monobank-rates/
├── usercode.py       # Основний файл (назва обов'язкова для Corezoid Git Call)
├── requirements.txt  # Залежності (stdlib only)
├── Dockerfile        # Для локального тестування
└── README.md
```

> **Чому `usercode.py`?** Corezoid Git Call для Python очікує файл з назвою `usercode.py` в корені проєкту (або в папці вказаній в Project path).

## Локальне тестування

### Запуск сервера

```bash
GITCALL_PORT=8080 python usercode.py
```

### Тестовий запит (curl)

```bash
curl http://127.0.0.1:8080 \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "Usercode.Run",
    "params": {
      "name": "Іванко",
      "currencies": [840, 978]
    }
  }'
```

### Docker

```bash
docker build -t corezoid-monobank-rates .
docker run --rm -p 8080:8080 -e GITCALL_PORT=8080 --user 501:501 --read-only corezoid-monobank-rates
```

## Важливо

- Модуль використовує **тільки стандартну бібліотеку Python 3.12** — `pip install` не потрібен
- Monobank API публічний, токен не обов'язковий для базових запитів
- Corezoid викликає Git Call з IP: `54.171.15.37`, `108.128.68.222`, `63.33.226.230`
