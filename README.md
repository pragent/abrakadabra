# corezoid-monobank-rates

Модуль для Corezoid **Git Call** — отримує актуальні курси валют від [Monobank](https://api.monobank.ua) та [PrivatBank](https://api.privatbank.ua), порівнює їх і рекомендує клієнту найвигідніший варіант.

## Як це працює

```
Corezoid Process
  └── Start  →  Git Call (цей репо)  →  End
                    │
                    ├── приймає: name, currencies, api_token
                    ├── звертається до:
                    │   ├── api.monobank.ua/bank/currency
                    │   └── api.privatbank.ua/p24api/pubinfo
                    ├── порівнює курси
                    └── повертає: greeting, recommendation, monobank, 
                                   privatbank, comparison, fetched_at
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
  "greeting": "Привіт, Іванко! 👋 Ось порівняння курсів Monobank і PrivatBank",
  "recommendation": "📊 **Аналіз курсів:**\n\nUSD:\n  💰 Купівля: Monobank краще (+0.15)\n  💵 Продаж: PrivatBank краще (-0.25)\n\n✅ **Рекомендація:**\n• Для **купівлі** валюти: скористайтесь **Monobank** 🟦",
  "monobank": {
    "USD": {"buy": 41.50, "sell": 42.10},
    "EUR": {"buy": 45.20, "sell": 46.00}
  },
  "privatbank": {
    "USD": {"buy": 41.35, "sell": 42.35},
    "EUR": {"buy": 45.50, "sell": 45.90}
  },
  "comparison": {
    "USD": {
      "monobank": {"buy": 41.50, "sell": 42.10},
      "privatbank": {"buy": 41.35, "sell": 42.35},
      "better_buy": "PrivatBank",
      "better_sell": "Monobank",
      "buy_diff": 0.15,
      "sell_diff": 0.25
    }
  },
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
      "currencies": [840, 978, 826]
    }
  }'
```

### Docker

```bash
docker build -t corezoid-monobank-rates .
docker run --rm -p 8080:8080 -e GITCALL_PORT=8080 --user 501:501 --read-only corezoid-monobank-rates
```

## Що програма робить

1. **Отримує курси** від Monobank та PrivatBank
2. **Порівнює** купівельні і продажні курси для кожної валюти
3. **Аналізує** різницю в ціні (спред)
4. **Рекомендує** найвигідніший банк для купівлі і продажу
5. **Форматує** результат у вигляді зручної таблиці з емодзі

## Важливо

- Модуль використовує **тільки стандартну бібліотеку Python 3.12** — `pip install` не потрібен
- Обидва API публічні, токен не обов'язковий
- Corezoid викликає Git Call з IP: `54.171.15.37`, `108.128.68.222`, `63.33.226.230`
- Якщо один з API недоступний, програма все одно працює з доступним
