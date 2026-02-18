"""
Cliente assíncrono para a API do Mercado Livre.
Usa httpx para requisições paralelas e muito mais rápidas.
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict

import httpx
from django.conf import settings

from .token_manager import token_manager

logger = logging.getLogger(__name__)


class MercadoLivreAPIAsync:
    """Cliente assíncrono para chamadas paralelas à API do Mercado Livre."""

    def __init__(self):
        self.api_base = settings.ML_API_BASE
        self.max_concurrent = 50  # Máximo de requisições simultâneas

    def _get_headers(self, access_token: str) -> dict:
        return {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

    async def get_all_item_ids(self, access_token: str, user_id: int) -> List[str]:
        """
        Busca todos os IDs de produtos do seller de forma paginada.
        """
        item_ids = []
        offset = 0
        limit = 50

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                url = f'{self.api_base}/users/{user_id}/items/search'
                params = {'offset': offset, 'limit': limit}
                headers = self._get_headers(access_token)

                try:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                    results = data.get('results', [])
                    if not results:
                        break

                    item_ids.extend(results)
                    offset += limit

                    logger.info(f'Buscados {len(item_ids)} IDs de produtos...')

                except httpx.HTTPError as e:
                    logger.error(f'Erro ao buscar IDs: {e}')
                    break

        return item_ids

    def calcular_tts(self, start_time_str: str, sold_quantity: int) -> float | None:
        """
        Calcula o Time To Sale (TTS) em horas.
        TTS = tempo_desde_criação / quantidade_vendida
        """
        if not start_time_str or sold_quantity == 0:
            return None

        try:
            data_criacao = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            agora = datetime.now(timezone.utc)

            diferenca = agora - data_criacao
            horas = diferenca.total_seconds() / 3600

            if horas <= 0:
                return None

            tts = horas / sold_quantity
            return round(tts, 2)

        except Exception as e:
            logger.error(f'Erro ao calcular TTS: {e}')
            return None

    def extrair_dados(self, item: dict) -> dict:
        """
        Extrai os dados relevantes do produto no formato do products.py
        """
        atributos = {a['id']: a.get('value_name') for a in item.get('attributes', [])}

        marca = atributos.get('BRAND')
        gtin = atributos.get('GTIN')
        sku = atributos.get('SELLER_SKU')

        primeira_foto = None
        pictures = item.get('pictures', [])
        if pictures:
            primeira_foto = pictures[0].get('secure_url')

        tts = self.calcular_tts(
            item.get('start_time'),
            item.get('sold_quantity', 0)
        )

        return {
            'ID': item.get('id'),
            'título': item.get('title'),
            'preço': item.get('price'),
            'estoque_atual': item.get('available_quantity'),
            'quantidade_vendida': item.get('sold_quantity'),
            'data_de_criacao': item.get('start_time'),
            'permalink': item.get('permalink'),
            'foto': primeira_foto,
            'modo_de_compra': item.get('shipping', {}).get('mode'),
            'tipo_logistico': item.get('shipping', {}).get('logistic_type'),
            'Marca': marca,
            'GTIN': gtin,
            'SKU': sku,
            'TTS_horas': tts,
        }

    async def get_item_detail(
        self,
        client: httpx.AsyncClient,
        item_id: str,
        access_token: str
    ) -> dict:
        """
        Busca os detalhes de um produto específico.
        """
        url = f'{self.api_base}/items/{item_id}'
        headers = self._get_headers(access_token)

        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            item = response.json()
            return self.extrair_dados(item)

        except httpx.HTTPError as e:
            logger.error(f'Erro ao buscar item {item_id}: {e}')
            return None

    async def get_all_my_products_paginated(self, user_id: int = None) -> dict:
        """
        Busca todos os produtos do seller de forma assíncrona.
        Retorna no formato do products.py com TTS ordenado.
        """
        # Pega o token válido do Supabase
        access_token = token_manager.ensure_valid_token(user_id)
        if not access_token:
            raise Exception('Nenhum token válido encontrado.')

        # Busca o user_id se não foi passado
        if not user_id:
            token_data = token_manager.get_token()
            user_id = token_data['user_id']

        logger.info('Iniciando busca de todos os produtos...')

        # 1. Busca todos os IDs
        item_ids = await self.get_all_item_ids(access_token, user_id)
        logger.info(f'Total de {len(item_ids)} produtos encontrados.')

        if not item_ids:
            return {
                'total_produtos': 0,
                'produtos': []
            }

        # 2. Busca detalhes de todos em paralelo (com semáforo para limitar concorrência)
        produtos = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_with_semaphore(client, item_id):
            async with semaphore:
                return await self.get_item_detail(client, item_id, access_token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [fetch_with_semaphore(client, item_id) for item_id in item_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if result and not isinstance(result, Exception):
                    produtos.append(result)

        logger.info(f'{len(produtos)} produtos processados com sucesso.')

        # 3. Ordena por TTS (menor para maior)
        produtos.sort(key=lambda x: (x['TTS_horas'] is None, x['TTS_horas']))

        return {
            'total_produtos': len(produtos),
            'produtos': produtos
        }


# Instância global
ml_api_async = MercadoLivreAPIAsync()
