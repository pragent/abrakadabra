# -*- coding: utf-8 -*-
"""
Corezoid Git Call — Monobank & PrivatBank Currency Rates
=========================================================
Вхід (params з Corezoid task):
  - name        (str)        : ім'я для привітання
  - currencies  (list[int])  : коди валют ISO 4217, default [840, 978]
  - api_token   (str)        : Monobank token (опціонально)

Вихід (повертається в Corezoid task):
  - greeting    (str)
  - recommendation (str)     : рекомендація якого банку використати
  - monobank    (dict)       : курси Monobank
  - privatbank  (dict)       : курси PrivatBank
  - comparison  (dict)       : аналіз порівняння
  - fetched_at  (str)
"""

import urllib.request
import urllib.error
import json
from datetime import datetime, timezone

MONOBANK_API_URL = "https://api.monobank.ua/bank/currency"
PRIVATBANK_API_URL = "https://api.privatbank.ua/p24api/pubinfo"

CURRENCY_NAMES = {
    840: "USD",
    978: "EUR",
    826: "GBP",
    756: "CHF",
    985: "PLN",
    980: "UAH",
}

CURRENCY_CODES_TO_CCY = {v: k for k, v in CURRENCY_NAMES.items()}
CURRENCY_CODES_TO_CCY.update({
    "USD": 840, "EUR": 978, "GBP": 826, "CHF": 756, "PLN": 985, "UAH": 980
})


def fetch_monobank_rates(token=None):
    req = urllib.request.Request(MONOBANK_API_URL)
    req.add_header("User-Agent", "corezoid-gitcall/1.0")
    if token:
        req.add_header("X-Token", token)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_privatbank_rates():
    req = urllib.request.Request(PRIVATBANK_API_URL + "?json")
    req.add_header("User-Agent", "corezoid-gitcall/1.0")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def filter_monobank_rates(all_rates, currency_codes):
    result = {}
    for rate in all_rates:
        code_a = rate.get("currencyCodeA")
        code_b = rate.get("currencyCodeB")
        if code_a in currency_codes and code_b == 980:
            ccy = CURRENCY_NAMES.get(code_a, str(code_a))
            result[ccy] = {
                "buy":  rate.get("rateBuy"),
                "sell": rate.get("rateSell"),
            }
    return result


def filter_privatbank_rates(all_rates, currency_codes):
    result = {}
    valid_ccys = set(CURRENCY_NAMES.values())

    for rate in all_rates:
        ccy = rate.get("ccy", "").upper()
        base_ccy = rate.get("base_ccy", "").upper()

        if base_ccy == "UAH" and ccy in valid_ccys:
            code = CURRENCY_CODES_TO_CCY.get(ccy)
            if code and code in currency_codes:
                try:
                    result[ccy] = {
                        "buy":  float(rate.get("buy", 0)),
                        "sell": float(rate.get("sale", 0)),
                    }
                except (ValueError, TypeError):
                    pass
    return result


def compare_rates(mono_rates, priv_rates, currency_codes):
    comparison = {}

    for code in currency_codes:
        ccy = CURRENCY_NAMES.get(code)
        if not ccy:
            continue

        mono = mono_rates.get(ccy)
        priv = priv_rates.get(ccy)

        if not mono or not priv:
            continue

        mono_buy = mono.get("buy", 0)
        mono_sell = mono.get("sell", 0)
        priv_buy = priv.get("buy", 0)
        priv_sell = priv.get("sell", 0)

        better_buy = "Monobank" if mono_buy >= priv_buy else "PrivatBank"
        better_sell = "Monobank" if mono_sell <= priv_sell else "PrivatBank"

        comparison[ccy] = {
            "monobank": {"buy": mono_buy, "sell": mono_sell},
            "privatbank": {"buy": priv_buy, "sell": priv_sell},
            "better_buy": better_buy,
            "better_sell": better_sell,
            "buy_diff": abs(mono_buy - priv_buy),
            "sell_diff": abs(mono_sell - priv_sell),
        }

    return comparison


def generate_recommendation(comparison):
    if not comparison:
        return "На жаль, не вдалося порівняти курси."

    banks_buy = {}
    banks_sell = {}

    for ccy, data in comparison.items():
        better_buy = data["better_buy"]
        better_sell = data["better_sell"]

        banks_buy[better_buy] = banks_buy.get(better_buy, 0) + 1
        banks_sell[better_sell] = banks_sell.get(better_sell, 0) + 1

    msg = "📊 **Аналіз курсів:**\n"

    for ccy, data in comparison.items():
        msg += f"\n{ccy}:\n"
        msg += f"  💰 Купівля: {data['better_buy']} краще (+{data['buy_diff']:.2f})\n"
        msg += f"  💵 Продаж: {data['better_sell']} краще (-{data['sell_diff']:.2f})\n"

    msg += "\n✅ **Рекомендація:**\n"

    if banks_buy.get("Monobank", 0) >= len(comparison) / 2:
        msg += "• Для **купівлі** валюти: скористайтесь **Monobank** 🟦\n"
    else:
        msg += "• Для **купівлі** валюти: скористайтесь **PrivatBank** 🏦\n"

    if banks_sell.get("Monobank", 0) >= len(comparison) / 2:
        msg += "• Для **продажу** валюти: скористайтесь **Monobank** 🟦\n"
    else:
        msg += "• Для **продажу** валюти: скористайтесь **PrivatBank** 🏦\n"

    return msg


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

    try:
        mono_all = fetch_monobank_rates(api_token)
        mono_rates = filter_monobank_rates(mono_all, currency_codes)
    except Exception:
        mono_rates = {}
        mono_all = []

    try:
        priv_all = fetch_privatbank_rates()
        priv_rates = filter_privatbank_rates(priv_all, currency_codes)
    except Exception:
        priv_rates = {}
        priv_all = []

    comparison = compare_rates(mono_rates, priv_rates, currency_codes)
    recommendation = generate_recommendation(comparison)

    data["greeting"]      = f"Привіт, {name}! 👋 Ось порівняння курсів Monobank і PrivatBank"
    data["recommendation"] = recommendation
    data["monobank"]       = mono_rates
    data["privatbank"]     = priv_rates
    data["comparison"]     = comparison
    data["fetched_at"]     = datetime.now(tz=timezone.utc).isoformat()

    return data
