"""
Servico de pedidos do Mercado Livre com streaming JSON - ULTRA RAPIDO.

Estrategia de velocidade:
1. Busca a 1a pagina de pedidos para saber o total
2. Busca TODAS as outras paginas em paralelo
3. Busca TODOS os discounts + shipments em UM unico gather massivo
4. Faz streaming dos resultados processados (instantaneo, so CPU)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List

import httpx

from .token_manager import token_manager

logger = logging.getLogger(__name__)

# =========================
# CONFIG - OTIMIZADO
# =========================
BASE_URL = "https://api.mercadolibre.com"
LIMIT = 50
MAX_RETRIES = 4
MAX_CONCURRENT = 60  # Aumentado para mais paralelismo

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


def process_order(order, discount_cache, shipment_cache):
    """Processa um pedido e retorna lista de rows."""
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

    rows = []
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

    for r in rows:
        r["gross_items_order"] = round(gross_items, 2)
        r["sale_fee_total_order"] = round(sale_fee_total, 2)
        r["marketplace_fee_order"] = round(marketplace_fee, 2)
        r["seller_shipping_cost"] = round(seller_shipping_cost, 2)
        r["net_order_simplified"] = round(net_order, 2)

    return rows


# =========================
# HTTP CLIENT ASYNC - OTIMIZADO
# =========================
@dataclass
class MeliOrdersClient:
    token: str

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
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
                    await asyncio.sleep(min(2 ** attempt, 8))
                    continue
                resp.raise_for_status()
                return resp.json() if resp.text else None
            except Exception:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(min(2 ** attempt, 8))
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
        return await self._request(
            client, "GET", f"/orders/{order_id}/discounts", allow_404_empty=True
        )

    async def get_shipment(self, client, shipment_id):
        return await self._request(
            client, "GET", f"/shipments/{shipment_id}", allow_404_empty=True
        )


# =========================
# STREAMING ULTRA RAPIDO
# =========================
async def stream_orders_async() -> AsyncGenerator[str, None]:
    """
    Async generator que faz yield de chunks JSON para streaming.

    ESTRATEGIA ULTRA RAPIDA:
    1) Busca 1a pagina -> descobre total
    2) Busca TODAS as paginas restantes em PARALELO
    3) Busca TODOS os discounts + TODOS os shipments em UM gather massivo
    4) Stream os resultados processados (instantaneo - so CPU)

    Formato de saida identico ao meli_vendas_detalhadas.json
    """
    t0 = time.perf_counter()

    # 1. Obter token do Supabase
    access_token = token_manager.ensure_valid_token()
    if not access_token:
        yield json.dumps({"error": "Nenhum token valido encontrado."})
        return

    meli = MeliOrdersClient(token=access_token)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Pool de conexoes otimizado
    limits = httpx.Limits(
        max_connections=MAX_CONCURRENT + 10,
        max_keepalive_connections=MAX_CONCURRENT,
    )

    async with httpx.AsyncClient(timeout=60.0, limits=limits) as http:

        # =============================================
        # FASE 1: Identificar seller + 1a pagina
        # =============================================
        me = await meli.get_me(http)
        seller_id = me.get("id")
        if not seller_id:
            yield json.dumps({"error": "Nao foi possivel identificar o seller."})
            return

        # Busca 1a pagina para descobrir o total
        first_page = await meli.search_orders(http, seller_id, 0)
        total_orders = first_page.get("paging", {}).get("total", 0)
        all_orders = first_page.get("results", []) or []

        t1 = time.perf_counter()
        logger.info(
            f"[myorders] Seller {seller_id} | Total: {total_orders} pedidos "
            f"| 1a pagina em {t1 - t0:.1f}s"
        )

        # =============================================
        # FASE 2: Buscar TODAS as paginas restantes em PARALELO
        # =============================================
        if total_orders > LIMIT:
            offsets = list(range(LIMIT, total_orders, LIMIT))

            async def fetch_page(offset):
                async with semaphore:
                    return await meli.search_orders(http, seller_id, offset)

            page_results = await asyncio.gather(
                *[fetch_page(off) for off in offsets]
            )

            for page in page_results:
                results = page.get("results", []) or []
                all_orders.extend(results)

        t2 = time.perf_counter()
        logger.info(
            f"[myorders] {len(all_orders)} pedidos carregados em {t2 - t0:.1f}s"
        )

        # =============================================
        # FASE 3: Buscar TODOS discounts + shipments EM PARALELO
        # =============================================
        # Coletar IDs unicos de shipments
        shipment_ids = list({
            order.get("shipping", {}).get("id")
            for order in all_orders
            if order.get("shipping", {}).get("id")
        })

        # Criar todas as tasks de uma vez
        async def fetch_discount(order_id):
            async with semaphore:
                return await meli.get_discounts(http, order_id)

        async def fetch_shipment(sid):
            async with semaphore:
                return await meli.get_shipment(http, sid)

        # Executar TUDO de uma vez - discounts + shipments juntos
        all_discount_tasks = [fetch_discount(o["id"]) for o in all_orders]
        all_shipment_tasks = [fetch_shipment(sid) for sid in shipment_ids]

        # Um unico gather massivo para tudo
        all_results = await asyncio.gather(
            asyncio.gather(*all_discount_tasks),
            asyncio.gather(*all_shipment_tasks),
        )

        disc_results = all_results[0]
        ship_results = all_results[1]

        # Montar caches globais
        discount_cache: Dict[Any, dict] = {
            order["id"]: disc or {}
            for order, disc in zip(all_orders, disc_results)
        }
        shipment_cache: Dict[Any, dict] = {
            sid: ship or {}
            for sid, ship in zip(shipment_ids, ship_results)
        }

        t3 = time.perf_counter()
        logger.info(
            f"[myorders] {len(disc_results)} discounts + {len(ship_results)} shipments "
            f"em {t3 - t2:.1f}s | Total fetch: {t3 - t0:.1f}s"
        )

    # =============================================
    # FASE 4: STREAMING - processar e enviar (instantaneo)
    # =============================================
    yield '{\n  "vendas_detalhadas": [\n'

    first_row = True
    all_rows_count = 0
    order_totals: Dict[str, dict] = {}

    for order in all_orders:
        rows = process_order(order, discount_cache, shipment_cache)

        # Acumular totais para o resumo
        if rows:
            oid = rows[0]["order_id"]
            if oid not in order_totals:
                order_totals[oid] = {
                    "gross": rows[0].get("gross_items_order", 0),
                    "fee": rows[0].get("marketplace_fee_order", 0),
                    "shipping": rows[0].get("seller_shipping_cost", 0),
                    "discount": rows[0].get("discount_total_order", 0),
                    "net": rows[0].get("net_order_simplified", 0),
                }

        for row in rows:
            prefix = "    " if first_row else ",\n    "
            yield prefix + json.dumps(row, ensure_ascii=False)
            first_row = False
            all_rows_count += 1

    # =============================================
    # FASE 5: Resumo financeiro + fechar JSON
    # =============================================
    total_gross = sum(o["gross"] for o in order_totals.values())
    total_fee = sum(o["fee"] for o in order_totals.values())
    total_shipping = sum(o["shipping"] for o in order_totals.values())
    total_discount = sum(o["discount"] for o in order_totals.values())
    total_net = sum(o["net"] for o in order_totals.values())

    resumo = {
        "bruto_total": round(total_gross, 2),
        "taxas_total": round(total_fee, 2),
        "frete_seller_total": round(total_shipping, 2),
        "descontos_total": round(total_discount, 2),
        "liquido_total": round(total_net, 2),
    }

    yield '\n  ],\n'
    yield f'  "total_pedidos": {len(all_orders)},\n'
    yield f'  "total_linhas": {all_rows_count},\n'
    yield f'  "resumo": {json.dumps(resumo, ensure_ascii=False)}\n'
    yield '}'

    t4 = time.perf_counter()
    logger.info(
        f"[myorders] COMPLETO: {len(all_orders)} pedidos, {all_rows_count} linhas "
        f"em {t4 - t0:.1f}s total"
    )


def sync_stream_orders():
    """
    Generator sincrono que converte o async generator para uso
    com StreamingHttpResponse do Django.
    """
    loop = asyncio.new_event_loop()
    try:
        agen = stream_orders_async()
        while True:
            try:
                chunk = loop.run_until_complete(agen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break
    finally:
        loop.close()
