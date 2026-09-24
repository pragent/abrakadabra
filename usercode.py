# -*- coding: utf-8 -*-
"""
Corezoid Git Call — Monobank Currency Rates
============================================
Вхід (params з Corezoid task):
  - name        (str)        : ім'я для привітання
  - currencies  (list[int])  : коди валют ISO 4217, default [840, 978]
  - api_token   (str)        : Monobank token (опціонально)

Вихід (повертається в Corezoid task):
  - greeting    (str)
  - rates       (list)
  - source      (str)
  - fetched_at  (str)
"""

import urllib.request
import urllib.error
import json
from datetime import datetime, timezone

MONOBANK_API_URL = "https://api.monobank.ua/bank/currency"

CURRENCY_NAMES = {
    840: "USD",
    978: "EUR",
    826: "GBP",
    756: "CHF",
    985: "PLN",
    980: "UAH",
}


def fetch_rates(token=None):
    req = urllib.request.Request(MONOBANK_API_URL)
    req.add_header("User-Agent", "corezoid-gitcall/1.0")
    if token:
        req.add_header("X-Token", token)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def filter_rates(all_rates, currency_codes):
    result = []
    for rate in all_rates:
        code_a = rate.get("currencyCodeA")
        code_b = rate.get("currencyCodeB")
        if code_a in currency_codes and code_b == 980:
            result.append({
                "currency":   CURRENCY_NAMES.get(code_a, str(code_a)),
                "code":       code_a,
                "buy":        rate.get("rateBuy"),
                "sell":       rate.get("rateSell"),
                "cross":      rate.get("rateCross"),
                "updated_at": datetime.fromtimestamp(
                    rate.get("date", 0), tz=timezone.utc
                ).isoformat(),
            })
    return result


def handle(data):
    """
    Точка входу для Corezoid Git Call.
    data — dict з параметрами Corezoid task.
    Повертає dict який стане параметрами task після ноди.
    """
    name           = data.get("name", "друже")
    raw_codes      = data.get("currencies", [840, 978])
    api_token      = data.get("api_token")

    currency_codes = [int(c) for c in raw_codes]

    all_rates = fetch_rates(api_token)
    rates     = filter_rates(all_rates, currency_codes)

    data["greeting"]   = f"Привіт, {name}! Ось курси валют від api.monobank.ua"
    data["rates"]      = rates
    data["source"]     = MONOBANK_API_URL
    data["fetched_at"] = datetime.now(tz=timezone.utc).isoformat()

    return data
