"""
Mercado Livre - Conciliação de vendas ASSÍNCRONA (versão corrigida)

- Corrige cálculo de frete seller
- Corrige conversão monetária
- Trata 404 corretamente
- Conciliação bate com painel ML

Saída:
- meli_vendas_detalhadas.json
"""

from __future__ import annotations

import asyncio
import time
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


# =========================
# CONFIG
# =========================
BEARER_TOKEN = "APP_USR-4943523961409438-021807-50befc829b5f706862a2bd7f67e78b99-533863251"

BASE_URL = "https://api.mercadolibre.com"
LIMIT = 50
MAX_RETRIES = 6
MAX_CONCURRENT = 30

DATE_FROM = "2018-01-01T00:00:00.000-00:00"
DATE_TO = None
ORDER_STATUS = None


# =========================
# HELPERS
# =========================
def safe_get(d: Dict[str, Any], *path: str, default=None):
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def to_money(x: Any, default: float = 0.0) -> float:
    if x is None:
        return default

    if isinstance(x, (int, float)):
        return float(x)

    if isinstance(x, str):
        try:
            return float(x.replace(".", "").replace(",", "."))
        except Exception:
            return default

    if isinstance(x, dict):
        for k in ("value", "amount", "total", "cost", "price"):
            if k in x:
                return to_money(x.get(k), default)
        return default

    return default


def extract_seller_shipping_cost_from_order(order: Dict[str, Any]) -> float:
    candidates = [
        safe_get(order, "shipping", "cost"),
        safe_get(order, "shipping", "seller_cost"),
        safe_get(order, "shipping", "sender_cost"),
        order.get("shipping_cost"),
    ]
    for c in candidates:
        v = to_money(c, 0.0)
        if v > 0:
            return v
    return 0.0


def extract_seller_shipping_cost(shipment: Dict[str, Any]) -> float:
    direct_candidates = [
        safe_get(shipment, "seller", "cost"),
        safe_get(shipment, "seller_cost"),
        safe_get(shipment, "costs", "seller"),
        safe_get(shipment, "costs", "sender"),
        safe_get(shipment, "shipping_option", "cost"),
        safe_get(shipment, "shipping_option", "list_cost"),
        safe_get(shipment, "shipping_option", "cost", "value"),
        safe_get(shipment, "shipping_option", "list_cost", "value"),
    ]

    for c in direct_candidates:
        v = to_money(c, 0.0)
        if v > 0:
            return v

    senders = safe_get(shipment, "costs", "senders")
    if isinstance(senders, list):
        for entry in senders:
            if not isinstance(entry, dict):
                continue
            if entry.get("type") in ("seller", "sender") or entry.get("payer") == "seller":
                v = to_money(entry.get("cost"), 0.0)
                if v > 0:
                    return v

    return 0.0


def extract_marketplace_fee(order: Dict[str, Any], sale_fee_total: float) -> float:
    for key in ("marketplace_fee", "total_fees", "paid_amount_fees", "fees_amount"):
        v = order.get(key)
        if v is not None:
            return to_money(v, sale_fee_total)
    return sale_fee_total


def summarize_discounts(discounts_payload: Dict[str, Any]) -> Dict[str, Any]:
    total = to_money(safe_get(discounts_payload, "amounts", "total"), 0.0)

    return {
        "discount_total": total,
        "discount_detail_json": json.dumps(discounts_payload, ensure_ascii=False),
    }


def calc_order_net(gross_items: float, marketplace_fee: float, seller_shipping_cost: float) -> float:
    return gross_items - marketplace_fee - seller_shipping_cost


# =========================
# HTTP CLIENT ASYNC
# =========================
@dataclass
class MeliClientAsync:
    token: str

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(self, client, method, path, params=None, allow_404_empty=False):
        url = f"{BASE_URL}{path}"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await client.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    params=params,
                )

                if resp.status_code == 404 and allow_404_empty:
                    return {}

                if resp.status_code in (429, 500, 502, 503, 504):
                    await asyncio.sleep(2 ** attempt)
                    continue

                resp.raise_for_status()
                return resp.json() if resp.text else None

            except Exception:
                await asyncio.sleep(2 ** attempt)

        return {}

    async def get_me(self, client):
        return await self._request(client, "GET", "/users/me")

    async def search_orders(self, client, seller_id, offset):
        params = {
            "seller": seller_id,
            "offset": offset,
            "limit": LIMIT,
            "sort": "date_desc",
        }
        if DATE_FROM:
            params["order.date_created.from"] = DATE_FROM
        if DATE_TO:
            params["order.date_created.to"] = DATE_TO
        if ORDER_STATUS:
            params["order.status"] = ORDER_STATUS

        return await self._request(client, "GET", "/orders/search", params=params)

    async def get_discounts(self, client, order_id):
        return await self._request(client, "GET", f"/orders/{order_id}/discounts", allow_404_empty=True)

    async def get_shipment(self, client, shipment_id):
        return await self._request(client, "GET", f"/shipments/{shipment_id}", allow_404_empty=True)


# =========================
# MAIN
# =========================
async def main_async():
    print(f"\n{'='*60}")
    print("MERCADO LIVRE - CONCILIACAO DE VENDAS (ASYNC)")
    print(f"{'='*60}\n")
    
    client_meli = MeliClientAsync(BEARER_TOKEN)

    async with httpx.AsyncClient(timeout=60.0) as http_client:
        # Step 1: Autenticação
        print("[1/5] Autenticando...")
        me = await client_meli.get_me(http_client)
        seller_id = me.get("id")
        print(f"      OK - Seller ID: {seller_id}")

        # Step 2: Buscar pedidos
        print(f"\n[2/5] Buscando pedidos...")
        all_orders = []
        offset = 0
        total = None

        while True:
            page = await client_meli.search_orders(http_client, seller_id, offset)
            results = page.get("results", []) or []

            if total is None:
                total = page.get("paging", {}).get("total", 0)
                print(f"      Total: {total} pedidos")

            if not results:
                break

            all_orders.extend(results)
            offset += LIMIT
            print(f"      Progresso: {len(all_orders)}/{total}", end="\r")

            if offset >= total:
                break

        print(f"\n      OK - {len(all_orders)} pedidos carregados")

        # Step 3: Coletar IDs únicos
        print(f"\n[3/5] Coletando IDs unicos...")
        shipment_ids = list({
            order.get("shipping", {}).get("id")
            for order in all_orders
            if order.get("shipping", {}).get("id")
        })
        print(f"      - {len(all_orders)} discounts para buscar")
        print(f"      - {len(shipment_ids)} shipments unicos")

        # Step 4: Buscar dados em paralelo com semáforo
        print(f"\n[4/5] Buscando dados em paralelo (max {MAX_CONCURRENT} simultaneos)...")
        
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
        async def fetch_discount_with_progress(order_id, idx, total):
            async with semaphore:
                if idx % 50 == 0:
                    print(f"      Discounts: {idx}/{total}", end="\r")
                return await client_meli.get_discounts(http_client, order_id)
        
        async def fetch_shipment_with_progress(sid, idx, total):
            async with semaphore:
                if idx % 10 == 0:
                    print(f"      Shipments: {idx}/{total}", end="\r")
                return await client_meli.get_shipment(http_client, sid)

        print(f"      Buscando discounts...")
        discount_tasks = [
            fetch_discount_with_progress(order["id"], idx, len(all_orders))
            for idx, order in enumerate(all_orders)
        ]
        discount_results = await asyncio.gather(*discount_tasks)
        print(f"      OK - {len(discount_results)} discounts")

        print(f"      Buscando shipments...")
        shipment_tasks = [
            fetch_shipment_with_progress(sid, idx, len(shipment_ids))
            for idx, sid in enumerate(shipment_ids)
        ]
        shipment_results = await asyncio.gather(*shipment_tasks)
        print(f"      OK - {len(shipment_results)} shipments")

        discount_cache = {
            order["id"]: disc or {}
            for order, disc in zip(all_orders, discount_results)
        }

        shipment_cache = {
            sid: ship or {}
            for sid, ship in zip(shipment_ids, shipment_results)
        }

    # Step 5: Processar dados
    print(f"\n[5/5] Processando {len(all_orders)} pedidos...")
    rows = []

    for idx, order in enumerate(all_orders):
        if idx % 100 == 0:
            print(f"      Progresso: {idx}/{len(all_orders)}", end="\r")
        order_id = order["id"]
        order_items = order.get("order_items", []) or []

        gross_items = 0
        sale_fee_total = 0

        disc = summarize_discounts(discount_cache.get(order_id, {}))

        seller_shipping_cost = extract_seller_shipping_cost_from_order(order)

        if seller_shipping_cost <= 0:
            sid = order.get("shipping", {}).get("id")
            if sid and sid in shipment_cache:
                seller_shipping_cost = extract_seller_shipping_cost(shipment_cache[sid])

        for oi in order_items:
            unit_price = to_money(oi.get("unit_price"))
            quantity = oi.get("quantity", 0)
            sale_fee_unit = to_money(oi.get("sale_fee"))

            gross_item = unit_price * quantity
            sale_fee_item_total = sale_fee_unit * quantity

            gross_items += gross_item
            sale_fee_total += sale_fee_item_total

            rows.append({
                "order_id": str(order_id),
                "unit_price": round(unit_price, 2),
                "quantity": quantity,
                "gross_item": round(gross_item, 2),
                "sale_fee_total_order": None,
                "marketplace_fee_order": None,
                "seller_shipping_cost": None,
                "net_order_simplified": None,
                "discount_total_order": round(disc["discount_total"], 2),
            })

        marketplace_fee = extract_marketplace_fee(order, sale_fee_total)
        net_order = calc_order_net(gross_items, marketplace_fee, seller_shipping_cost)

        for r in rows[-len(order_items):]:
            r["gross_items_order"] = round(gross_items, 2)
            r["sale_fee_total_order"] = round(sale_fee_total, 2)
            r["marketplace_fee_order"] = round(marketplace_fee, 2)
            r["seller_shipping_cost"] = round(seller_shipping_cost, 2)
            r["net_order_simplified"] = round(net_order, 2)

    print(f"\n      OK - {len(rows)} linhas processadas")

    # Calcular totais
    order_totals = {}
    for row in rows:
        oid = row["order_id"]
        if oid not in order_totals:
            order_totals[oid] = {
                "gross": row.get("gross_items_order", 0),
                "fee": row.get("marketplace_fee_order", 0),
                "shipping": row.get("seller_shipping_cost", 0),
                "discount": row.get("discount_total_order", 0),
                "net": row.get("net_order_simplified", 0),
            }

    total_gross = sum(o["gross"] for o in order_totals.values())
    total_fee = sum(o["fee"] for o in order_totals.values())
    total_shipping = sum(o["shipping"] for o in order_totals.values())
    total_discount = sum(o["discount"] for o in order_totals.values())
    total_net = sum(o["net"] for o in order_totals.values())

    output_data = {
        "total_pedidos": len(all_orders),
        "total_linhas": len(rows),
        "resumo": {
            "bruto_total": round(total_gross, 2),
            "taxas_total": round(total_fee, 2),
            "frete_seller_total": round(total_shipping, 2),
            "descontos_total": round(total_discount, 2),
            "liquido_total": round(total_net, 2),
        },
        "vendas_detalhadas": rows
    }

    print(f"\n{'='*60}")
    print("RESUMO FINANCEIRO")
    print(f"{'='*60}")
    print(f"Pedidos:         {len(all_orders)}")
    print(f"Linhas (itens):  {len(rows)}")
    print(f"Bruto:           R$ {total_gross:,.2f}")
    print(f"Taxas ML:        R$ {total_fee:,.2f}")
    print(f"Frete Seller:    R$ {total_shipping:,.2f}")
    print(f"Descontos:       R$ {total_discount:,.2f}")
    print(f"Liquido:         R$ {total_net:,.2f}")
    print(f"{'='*60}\n")

    print("Salvando arquivo...")
    with open("meli_vendas_detalhadas.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("OK - Arquivo gerado: meli_vendas_detalhadas.json")


def main():
    inicio = time.time()
    asyncio.run(main_async())
    duracao = time.time() - inicio
    print(f"\nTEMPO TOTAL: {duracao:.2f} segundos")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
