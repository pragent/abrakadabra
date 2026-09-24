#!/usr/bin/env python3
"""
Corezoid Git Call — Monobank Currency Rates
============================================
Приймає task-параметри від Corezoid через JSON-RPC 2.0,
звертається до api.monobank.ua для отримання курсів валют,
повертає результат назад у Corezoid.

Вхідні параметри (params з Corezoid task):
  - name        (str, required) : ім'я для привітання
  - currencies  (list, optional): список кодів валют ISO 4217
                                  default: [840, 978] (USD, EUR)
  - api_token   (str, optional) : Monobank API token (якщо потрібен)

Вихід (result → Corezoid task):
  - greeting    (str)  : привітання з іменем
  - rates       (list) : масив курсів валют
  - source      (str)  : джерело даних
  - fetched_at  (str)  : час отримання даних (ISO 8601)
"""

import http.server
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


# ── Monobank currency codes ─────────────────────────────────────────────────
CURRENCY_NAMES = {
    840: "USD",
    978: "EUR",
    826: "GBP",
    756: "CHF",
    985: "PLN",
    203: "CZK",
    980: "UAH",
}

MONOBANK_API_URL = "https://api.monobank.ua/bank/currency"


# ── Business logic ───────────────────────────────────────────────────────────
def fetch_monobank_rates(token: str | None = None) -> list:
    """Отримати курси від api.monobank.ua"""
    req = urllib.request.Request(MONOBANK_API_URL)
    req.add_header("User-Agent", "corezoid-gitcall/1.0")
    if token:
        req.add_header("X-Token", token)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Monobank API error: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def filter_rates(all_rates: list, currency_codes: list[int]) -> list:
    """Відфільтрувати потрібні валютні пари (X → UAH)"""
    result = []
    for rate in all_rates:
        code_a = rate.get("currencyCodeA")
        code_b = rate.get("currencyCodeB")
        # Беремо тільки пари X/UAH (980)
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


def usercode(params: dict) -> dict:
    """
    Основна функція — викликається Corezoid через Git Call.
    params = task-параметри із Corezoid процесу.
    """
    name          = params.get("name", "друже")
    raw_codes     = params.get("currencies", [840, 978])   # USD, EUR за замовчуванням
    api_token     = params.get("api_token")                 # опціонально

    # Нормалізуємо коди — Corezoid може передати рядки або числа
    currency_codes = [int(c) for c in raw_codes]

    # Отримуємо курси
    all_rates    = fetch_monobank_rates(api_token)
    rates        = filter_rates(all_rates, currency_codes)
    fetched_at   = datetime.now(tz=timezone.utc).isoformat()

    return {
        "greeting":   f"Привіт, {name}! Ось курси валют від api.monobank.ua",
        "rates":      rates,
        "source":     MONOBANK_API_URL,
        "fetched_at": fetched_at,
        # Прокидаємо вхідні параметри назад у task (зручно для debug)
        "input_name":       name,
        "input_currencies": currency_codes,
    }


# ── JSON-RPC 2.0 HTTP server (required by Corezoid Git Call) ─────────────────
class GitCallHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Перевизначаємо щоб контролювати формат логів
        print(f"[{self.log_date_time_string()}] {fmt % args}", file=sys.stdout, flush=True)

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)

        jsonrpc = "2.0"
        req_id  = None

        try:
            req     = json.loads(body)
            jsonrpc = req.get("jsonrpc", "2.0")
            req_id  = req.get("id")
            params  = req.get("params", {})

            print(f"[req] id={req_id} params_keys={list(params.keys())}", flush=True)

            if not isinstance(params, dict):
                raise ValueError("params must be an object")

            result   = usercode(params)
            response = {"jsonrpc": jsonrpc, "id": req_id, "result": result}

        except Exception as exc:
            print(f"[err] id={req_id} error={exc}", flush=True)
            response = {
                "jsonrpc": jsonrpc,
                "id":      req_id,
                "error":   {"code": -32000, "message": str(exc)},
            }

        payload = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        print(f"[res] id={req_id}", flush=True)

    def do_GET(self):
        # Health-check endpoint
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')


if __name__ == "__main__":
    port = int(os.environ.get("GITCALL_PORT", 8080))
    server = http.server.HTTPServer(("0.0.0.0", port), GitCallHandler)
    print(f"[start] listening on 0.0.0.0:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[stop] shutting down", flush=True)
        server.server_close()
