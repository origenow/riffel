"""
Serviço de sincronização de produtos Mercado Livre -> Supabase.
Roda em background a cada 1 hora, mantendo o cache atualizado.
Na rota /myproducts a leitura é feita direto do Supabase (leve e rápido).
"""

import logging
import asyncio
import threading
import time
from datetime import datetime, timezone

import httpx
from django.conf import settings

from .token_manager import token_manager
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

PRODUCTS_TABLE = 'mercadolivre_products'
SYNC_TABLE = 'mercadolivre_sync_control'
SYNC_INTERVAL_SECONDS = 3600  # 1 hora

MAX_CONCURRENT = 50


# ─── helpers ────────────────────────────────────────────────────────
def _calcular_tts(start_time_str: str, sold_quantity: int) -> float | None:
    if not start_time_str or sold_quantity == 0:
        return None
    try:
        dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        horas = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        return round(horas / sold_quantity, 2) if horas > 0 else None
    except Exception:
        return None


def _extrair_dados(item: dict) -> dict:
    attrs = {a['id']: a.get('value_name') for a in item.get('attributes', [])}
    fotos = item.get('pictures', [])
    return {
        'item_id': item.get('id'),
        'titulo': item.get('title'),
        'preco': item.get('price'),
        'estoque_atual': item.get('available_quantity', 0),
        'quantidade_vendida': item.get('sold_quantity', 0),
        'data_de_criacao': item.get('start_time'),
        'permalink': item.get('permalink'),
        'foto': fotos[0].get('secure_url') if fotos else None,
        'modo_de_compra': item.get('shipping', {}).get('mode'),
        'tipo_logistico': item.get('shipping', {}).get('logistic_type'),
        'marca': attrs.get('BRAND'),
        'gtin': attrs.get('GTIN'),
        'sku': attrs.get('SELLER_SKU'),
        'tts_horas': _calcular_tts(item.get('start_time'), item.get('sold_quantity', 0)),
        'synced_at': datetime.now(timezone.utc).isoformat(),
    }


# ─── fetch assíncrono dos produtos ─────────────────────────────────
async def _fetch_all_item_ids(client: httpx.AsyncClient, headers: dict, user_id: int) -> list[str]:
    """Busca todos os IDs paginando de 50 em 50."""
    api_base = settings.ML_API_BASE
    ids = []
    offset = 0

    while True:
        try:
            resp = await client.get(
                f'{api_base}/users/{user_id}/items/search',
                headers=headers,
                params={'offset': offset, 'limit': 50},
            )
            resp.raise_for_status()
            results = resp.json().get('results', [])
            if not results:
                break
            ids.extend(results)
            offset += 50
        except Exception as e:
            logger.error(f'[SYNC] Erro ao buscar IDs (offset={offset}): {e}')
            break

    return ids


async def _fetch_item_detail(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    item_id: str,
    headers: dict,
) -> dict | None:
    api_base = settings.ML_API_BASE
    async with semaphore:
        try:
            resp = await client.get(f'{api_base}/items/{item_id}', headers=headers)
            resp.raise_for_status()
            return _extrair_dados(resp.json())
        except Exception as e:
            logger.error(f'[SYNC] Erro ao buscar item {item_id}: {e}')
            return None


async def _fetch_all_products() -> list[dict]:
    """Busca todos os produtos de forma assíncrona e retorna lista de dicts."""
    token_data = token_manager.get_token()
    if not token_data:
        raise RuntimeError('Nenhum token disponivel para sync de produtos.')

    access_token = token_manager.ensure_valid_token(token_data['user_id'])
    if not access_token:
        raise RuntimeError('Token invalido/expirado para sync de produtos.')

    user_id = token_data['user_id']
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Busca IDs
        item_ids = await _fetch_all_item_ids(client, headers, user_id)
        logger.info(f'[SYNC] {len(item_ids)} IDs encontrados.')

        if not item_ids:
            return []

        # 2. Busca detalhes em paralelo
        sem = asyncio.Semaphore(MAX_CONCURRENT)
        tasks = [_fetch_item_detail(client, sem, iid, headers) for iid in item_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    produtos = [r for r in results if r and not isinstance(r, Exception)]
    logger.info(f'[SYNC] {len(produtos)} produtos obtidos com sucesso.')
    return produtos


# ─── upsert no Supabase ────────────────────────────────────────────
def _upsert_products(produtos: list[dict]):
    """Faz upsert (insert ou update) de todos os produtos no Supabase."""
    sb = get_supabase_client()

    # Upsert em lotes de 100 (limite seguro do Supabase)
    batch_size = 100
    for i in range(0, len(produtos), batch_size):
        batch = produtos[i:i + batch_size]
        sb.table(PRODUCTS_TABLE).upsert(
            batch,
            on_conflict='item_id',
        ).execute()

    logger.info(f'[SYNC] {len(produtos)} produtos upsertados no Supabase.')

    # Remove produtos que nao existem mais no ML
    existing_ids = {p['item_id'] for p in produtos}
    db_items = sb.table(PRODUCTS_TABLE).select('item_id').execute()
    to_delete = [row['item_id'] for row in db_items.data if row['item_id'] not in existing_ids]

    if to_delete:
        for item_id in to_delete:
            sb.table(PRODUCTS_TABLE).delete().eq('item_id', item_id).execute()
        logger.info(f'[SYNC] {len(to_delete)} produtos removidos (nao existem mais no ML).')


def _update_sync_status(status_str: str, total: int = 0, error: str = None):
    """Atualiza o registro de controle de sync."""
    sb = get_supabase_client()
    data = {
        'status': status_str,
        'total_items': total,
        'error_message': error,
    }
    if status_str == 'completed':
        data['last_sync_at'] = datetime.now(timezone.utc).isoformat()

    sb.table(SYNC_TABLE).update(data).eq('sync_type', 'products').execute()


# ─── sync principal ────────────────────────────────────────────────
def run_sync():
    """Executa um ciclo completo de sync: ML API -> Supabase."""
    logger.info('[SYNC] Iniciando sincronizacao de produtos...')
    _update_sync_status('syncing')

    try:
        # Cria event loop novo para rodar o async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        produtos = loop.run_until_complete(_fetch_all_products())
        loop.close()

        if produtos:
            _upsert_products(produtos)

        _update_sync_status('completed', total=len(produtos))
        logger.info(f'[SYNC] Sincronizacao concluida: {len(produtos)} produtos.')

    except Exception as e:
        logger.error(f'[SYNC] Erro na sincronizacao: {e}')
        _update_sync_status('error', error=str(e))


# ─── leitura do cache ──────────────────────────────────────────────
def get_cached_products() -> dict:
    """Le os produtos do cache no Supabase. Retorno no mesmo formato da API."""
    sb = get_supabase_client()

    # Busca todos ordenados por TTS
    result = sb.table(PRODUCTS_TABLE).select('*').order(
        'tts_horas', desc=False, nullsfirst=False
    ).execute()

    produtos = []
    for row in result.data:
        produtos.append({
            'ID': row['item_id'],
            'titulo': row['titulo'],
            'preco': float(row['preco']) if row['preco'] is not None else None,
            'estoque_atual': row['estoque_atual'],
            'quantidade_vendida': row['quantidade_vendida'],
            'data_de_criacao': row['data_de_criacao'],
            'permalink': row['permalink'],
            'foto': row['foto'],
            'modo_de_compra': row['modo_de_compra'],
            'tipo_logistico': row['tipo_logistico'],
            'Marca': row['marca'],
            'GTIN': row['gtin'],
            'SKU': row['sku'],
            'TTS_horas': float(row['tts_horas']) if row['tts_horas'] is not None else None,
        })

    return {
        'total_produtos': len(produtos),
        'produtos': produtos,
    }


def get_sync_status() -> dict:
    """Retorna o status do ultimo sync."""
    sb = get_supabase_client()
    result = sb.table(SYNC_TABLE).select('*').eq('sync_type', 'products').single().execute()
    return result.data


# ─── background scheduler ──────────────────────────────────────────
def _background_sync_loop():
    """Loop que roda a cada SYNC_INTERVAL_SECONDS em background."""
    # Delay inicial para garantir que tudo inicializou
    time.sleep(5)

    while True:
        try:
            logger.info('[SYNC] Verificando se precisa sincronizar...')

            sync_data = get_sync_status()
            last_sync = sync_data.get('last_sync_at') if sync_data else None

            should_sync = True

            if last_sync:
                from datetime import datetime as dt
                if isinstance(last_sync, str):
                    last_dt = dt.fromisoformat(last_sync.replace('Z', '+00:00'))
                else:
                    last_dt = last_sync

                elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
                if elapsed < SYNC_INTERVAL_SECONDS:
                    remaining = int(SYNC_INTERVAL_SECONDS - elapsed)
                    logger.info(f'[SYNC] Ultimo sync recente. Proximo em {remaining}s.')
                    should_sync = False

            if should_sync:
                run_sync()

        except Exception as e:
            logger.error(f'[SYNC] Erro no loop de sync: {e}')

        # Dorme 60s e verifica novamente
        time.sleep(60)


def start_background_sync():
    """Inicia a thread de sincronizacao em background."""
    thread = threading.Thread(target=_background_sync_loop, daemon=True, name='products-sync')
    thread.start()
    logger.info('[SYNC] Thread de sincronizacao de produtos iniciada (intervalo: 1h).')
