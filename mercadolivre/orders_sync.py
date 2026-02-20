"""
Serviço de sincronização de pedidos Mercado Livre -> Supabase.
Roda em background a cada 1 hora, mantendo o cache atualizado.
Na rota /myorders a leitura é feita direto do Supabase (leve e rápido).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

from .token_manager import token_manager
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

ORDERS_TABLE = 'mercadolivre_orders'
SUMMARY_TABLE = 'mercadolivre_orders_summary'
SYNC_TABLE = 'mercadolivre_sync_control'
SYNC_TYPE = 'orders'
SYNC_INTERVAL_SECONDS = 3600  # 1 hora

BASE_URL = "https://api.mercadolibre.com"
LIMIT = 50
MAX_RETRIES = 4
MAX_CONCURRENT = 60
DATE_FROM = "2018-01-01T00:00:00.000-00:00"


# ─── helpers (mesmos do orders_service.py) ──────────────────────────
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
    return {"discount_total": total}


def calc_order_net(gross_items: float, marketplace_fee: float, seller_shipping_cost: float) -> float:
    return gross_items - marketplace_fee - seller_shipping_cost


def process_order(order, discount_cache, shipment_cache) -> List[dict]:
    """Processa um pedido e retorna lista de rows para o Supabase."""
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


# ─── HTTP client assíncrono ─────────────────────────────────────────
class _MeliClient:
    def __init__(self, token: str):
        self.token = token

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}

    async def _request(self, client, method, path, params=None, allow_404_empty=False):
        url = f"{BASE_URL}{path}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await client.request(method=method, url=url, headers=self._headers(), params=params)
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
        return await self._request(client, "GET", "/orders/search", params=params)

    async def get_discounts(self, client, order_id):
        return await self._request(client, "GET", f"/orders/{order_id}/discounts", allow_404_empty=True)

    async def get_shipment(self, client, shipment_id):
        return await self._request(client, "GET", f"/shipments/{shipment_id}", allow_404_empty=True)


# ─── fetch completo assíncrono ──────────────────────────────────────
async def _fetch_all_orders() -> tuple[list[dict], dict]:
    """
    Busca todos os pedidos do ML de forma assíncrona.
    Retorna (lista_de_rows, resumo).
    """
    access_token = token_manager.ensure_valid_token()
    if not access_token:
        raise RuntimeError('Nenhum token disponivel para sync de pedidos.')

    meli = _MeliClient(token=access_token)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    limits = httpx.Limits(max_connections=MAX_CONCURRENT + 10, max_keepalive_connections=MAX_CONCURRENT)

    async with httpx.AsyncClient(timeout=60.0, limits=limits) as http:
        # Fase 1: Identificar seller + 1a pagina
        me = await meli.get_me(http)
        seller_id = me.get("id")
        if not seller_id:
            raise RuntimeError('Nao foi possivel identificar o seller.')

        first_page = await meli.search_orders(http, seller_id, 0)
        total_orders = first_page.get("paging", {}).get("total", 0)
        all_orders = first_page.get("results", []) or []

        logger.info(f'[SYNC-ORDERS] Seller {seller_id} | Total: {total_orders} pedidos')

        # Fase 2: Buscar todas as paginas restantes em paralelo
        if total_orders > LIMIT:
            offsets = list(range(LIMIT, total_orders, LIMIT))

            async def fetch_page(offset):
                async with semaphore:
                    return await meli.search_orders(http, seller_id, offset)

            page_results = await asyncio.gather(*[fetch_page(off) for off in offsets])
            for page in page_results:
                results = page.get("results", []) or []
                all_orders.extend(results)

        logger.info(f'[SYNC-ORDERS] {len(all_orders)} pedidos carregados.')

        # Fase 3: Buscar todos discounts + shipments em paralelo
        shipment_ids = list({
            order.get("shipping", {}).get("id")
            for order in all_orders
            if order.get("shipping", {}).get("id")
        })

        async def fetch_discount(order_id):
            async with semaphore:
                return await meli.get_discounts(http, order_id)

        async def fetch_shipment(sid):
            async with semaphore:
                return await meli.get_shipment(http, sid)

        all_discount_tasks = [fetch_discount(o["id"]) for o in all_orders]
        all_shipment_tasks = [fetch_shipment(sid) for sid in shipment_ids]

        all_results = await asyncio.gather(
            asyncio.gather(*all_discount_tasks),
            asyncio.gather(*all_shipment_tasks),
        )

        disc_results = all_results[0]
        ship_results = all_results[1]

        discount_cache = {
            order["id"]: disc or {}
            for order, disc in zip(all_orders, disc_results)
        }
        shipment_cache = {
            sid: ship or {}
            for sid, ship in zip(shipment_ids, ship_results)
        }

        logger.info(f'[SYNC-ORDERS] {len(disc_results)} discounts + {len(ship_results)} shipments carregados.')

    # Fase 4: Processar todas as rows
    all_rows = []
    order_totals: Dict[str, dict] = {}

    for order in all_orders:
        rows = process_order(order, discount_cache, shipment_cache)
        all_rows.extend(rows)

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

    resumo = {
        "total_pedidos": len(all_orders),
        "total_linhas": len(all_rows),
        "bruto_total": round(sum(o["gross"] for o in order_totals.values()), 2),
        "taxas_total": round(sum(o["fee"] for o in order_totals.values()), 2),
        "frete_seller_total": round(sum(o["shipping"] for o in order_totals.values()), 2),
        "descontos_total": round(sum(o["discount"] for o in order_totals.values()), 2),
        "liquido_total": round(sum(o["net"] for o in order_totals.values()), 2),
    }

    logger.info(f'[SYNC-ORDERS] {len(all_rows)} linhas processadas.')
    return all_rows, resumo


# ─── upsert no Supabase ────────────────────────────────────────────
def _save_orders_to_supabase(rows: list[dict], resumo: dict):
    """Salva todos os pedidos no Supabase (limpa e reinsere)."""
    sb = get_supabase_client()
    now = datetime.now(timezone.utc).isoformat()

    # 1. Limpa a tabela de orders (replace completo - mais seguro)
    sb.table(ORDERS_TABLE).delete().neq('id', 0).execute()
    logger.info('[SYNC-ORDERS] Tabela de orders limpa.')

    # 2. Insere em lotes de 200
    batch_size = 200
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        # Adiciona synced_at em cada row
        for row in batch:
            row['synced_at'] = now
        sb.table(ORDERS_TABLE).insert(batch).execute()

    logger.info(f'[SYNC-ORDERS] {len(rows)} linhas inseridas no Supabase.')

    # 3. Salva/atualiza resumo
    resumo['synced_at'] = now
    # Limpa e reinsere (sempre 1 registro)
    sb.table(SUMMARY_TABLE).delete().neq('id', 0).execute()
    sb.table(SUMMARY_TABLE).insert(resumo).execute()

    logger.info('[SYNC-ORDERS] Resumo financeiro salvo.')


def _update_sync_status(status_str: str, total: int = 0, error: str = None):
    """Atualiza o registro de controle de sync para orders."""
    sb = get_supabase_client()
    data = {
        'status': status_str,
        'total_items': total,
        'error_message': error,
    }
    if status_str == 'completed':
        data['last_sync_at'] = datetime.now(timezone.utc).isoformat()

    sb.table(SYNC_TABLE).update(data).eq('sync_type', SYNC_TYPE).execute()


# ─── sync principal ────────────────────────────────────────────────
def run_orders_sync():
    """Executa um ciclo completo de sync de pedidos: ML API -> Supabase."""
    logger.info('[SYNC-ORDERS] Iniciando sincronizacao de pedidos...')
    _update_sync_status('syncing')

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        rows, resumo = loop.run_until_complete(_fetch_all_orders())
        loop.close()

        if rows:
            _save_orders_to_supabase(rows, resumo)

        _update_sync_status('completed', total=resumo.get('total_linhas', 0))
        logger.info(f'[SYNC-ORDERS] Sincronizacao concluida: {resumo.get("total_linhas", 0)} linhas.')

    except Exception as e:
        logger.error(f'[SYNC-ORDERS] Erro na sincronizacao: {e}')
        _update_sync_status('error', error=str(e))


# ─── leitura do cache ──────────────────────────────────────────────
def get_cached_orders() -> dict:
    """Le os pedidos do cache no Supabase. Formato identico ao meli_vendas_detalhadas.json."""
    sb = get_supabase_client()

    # Busca todas as linhas de orders
    # Supabase retorna max 1000 por padrão, paginar se necessário
    all_rows = []
    page = 0
    page_size = 1000

    while True:
        result = sb.table(ORDERS_TABLE).select('*').range(
            page * page_size, (page + 1) * page_size - 1
        ).execute()

        if not result.data:
            break

        all_rows.extend(result.data)

        if len(result.data) < page_size:
            break

        page += 1

    vendas = []
    for row in all_rows:
        vendas.append({
            "order_id": row['order_id'],
            "unit_price": float(row['unit_price']) if row['unit_price'] is not None else 0,
            "quantity": row['quantity'],
            "gross_item": float(row['gross_item']) if row['gross_item'] is not None else 0,
            "gross_items_order": float(row['gross_items_order']) if row['gross_items_order'] is not None else 0,
            "sale_fee_total_order": float(row['sale_fee_total_order']) if row['sale_fee_total_order'] is not None else 0,
            "marketplace_fee_order": float(row['marketplace_fee_order']) if row['marketplace_fee_order'] is not None else 0,
            "seller_shipping_cost": float(row['seller_shipping_cost']) if row['seller_shipping_cost'] is not None else 0,
            "net_order_simplified": float(row['net_order_simplified']) if row['net_order_simplified'] is not None else 0,
            "discount_total_order": float(row['discount_total_order']) if row['discount_total_order'] is not None else 0,
        })

    # Busca resumo
    summary_result = sb.table(SUMMARY_TABLE).select('*').limit(1).execute()
    resumo = {}
    if summary_result.data:
        s = summary_result.data[0]
        resumo = {
            "bruto_total": float(s['bruto_total']) if s['bruto_total'] is not None else 0,
            "taxas_total": float(s['taxas_total']) if s['taxas_total'] is not None else 0,
            "frete_seller_total": float(s['frete_seller_total']) if s['frete_seller_total'] is not None else 0,
            "descontos_total": float(s['descontos_total']) if s['descontos_total'] is not None else 0,
            "liquido_total": float(s['liquido_total']) if s['liquido_total'] is not None else 0,
        }

    return {
        "vendas_detalhadas": vendas,
        "total_pedidos": summary_result.data[0]['total_pedidos'] if summary_result.data else 0,
        "total_linhas": len(vendas),
        "resumo": resumo,
    }


def get_orders_sync_status() -> dict:
    """Retorna o status do ultimo sync de orders."""
    sb = get_supabase_client()
    result = sb.table(SYNC_TABLE).select('*').eq('sync_type', SYNC_TYPE).single().execute()
    return result.data


# ─── background scheduler ──────────────────────────────────────────
def _background_orders_sync_loop():
    """Loop que roda a cada SYNC_INTERVAL_SECONDS em background."""
    # Delay inicial maior (pedidos demoram mais que produtos)
    time.sleep(15)

    while True:
        try:
            logger.info('[SYNC-ORDERS] Verificando se precisa sincronizar pedidos...')

            sync_data = get_orders_sync_status()
            last_sync = sync_data.get('last_sync_at') if sync_data else None

            should_sync = True

            if last_sync:
                if isinstance(last_sync, str):
                    last_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                else:
                    last_dt = last_sync

                elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
                if elapsed < SYNC_INTERVAL_SECONDS:
                    remaining = int(SYNC_INTERVAL_SECONDS - elapsed)
                    logger.info(f'[SYNC-ORDERS] Ultimo sync recente. Proximo em {remaining}s.')
                    should_sync = False

            if should_sync:
                run_orders_sync()

        except Exception as e:
            logger.error(f'[SYNC-ORDERS] Erro no loop de sync: {e}')

        # Verifica a cada 60s
        time.sleep(60)


def start_orders_background_sync():
    """Inicia a thread de sincronizacao de pedidos em background."""
    thread = threading.Thread(target=_background_orders_sync_loop, daemon=True, name='orders-sync')
    thread.start()
    logger.info('[SYNC-ORDERS] Thread de sincronizacao de pedidos iniciada (intervalo: 1h).')
