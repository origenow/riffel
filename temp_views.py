"""
Views da API do Mercado Livre.
"""

import logging
from datetime import datetime, timedelta

import requests as http_requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .ml_api import ml_api
from .ml_api_async import ml_api_async
from .token_manager import token_manager
from .products_sync import get_cached_products, get_sync_status, run_sync
from .orders_sync import (
    get_cached_orders, get_orders_sync_status, run_orders_sync,
)

logger = logging.getLogger(__name__)


def formatar_cnpj(cnpj: str) -> str:
    """Formata string de CNPJ para XX.XXX.XXX/XXXX-XX"""
    if not cnpj or len(cnpj) != 14:
        return cnpj
    return f"{cnpj[0:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"


class MeView(APIView):
    """
    GET /users/{user_id}/me
    Retorna os dados da conta do Mercado Livre do usu├írio autenticado.
    Faz refresh autom├ítico do token se necess├írio.
    """

    def get(self, request, user_id):
        try:
            # Verifica se o usu├írio existe
            token_data = token_manager.get_token(user_id)
            if not token_data:
                return Response(
                    {'error': f'Usu├írio {user_id} n├úo encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            user_data = ml_api.get_me(user_id)
            
            # Extrai e formata apenas os dados solicitados
            cnpj_numero = user_data.get('identification', {}).get('number', '')
            address_data = user_data.get('address', {})
            seller_rep = user_data.get('seller_reputation', {})
            status_data = user_data.get('status', {})
            company_data = user_data.get('company', {})
            thumbnail_data = user_data.get('thumbnail', {})
            
            # Pega o telefone do registration_identifiers
            telefone = ''
            reg_identifiers = user_data.get('registration_identifiers', [])
            if reg_identifiers:
                for identifier in reg_identifiers:
                    if identifier.get('registration_type') == 'phone_identifier':
                        telefone = identifier.get('user_identifier', '')
                        break
            
            response_data = {
                'id': user_data.get('id'),
                'nickname': user_data.get('nickname'),
                'data_de_registro': user_data.get('registration_date'),
                'primeiro_nome': user_data.get('first_name'),
                'email': user_data.get('email'),
                'cnpj': formatar_cnpj(cnpj_numero),
                'endereco': address_data.get('address'),
                'cidade': address_data.get('city'),
                'estado': address_data.get('state'),
                'cep': address_data.get('zip_code'),
                'permalink_perfil': user_data.get('permalink'),
                'nivel_reputacao': seller_rep.get('level_id'),
                'nivel_mercado_lider': seller_rep.get('power_seller_status'),
                'mercadoenvios': status_data.get('mercadoenvios'),
                'nome_marca': company_data.get('brand_name'),
                'foto_perfil': thumbnail_data.get('picture_url'),
                'numero_telefone': telefone,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'Erro na rota /me: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TokenStatusView(APIView):
    """
    GET /users/{user_id}/token/status
    Retorna o status do token armazenado (sem expor o token em si).
    """

    def get(self, request, user_id):
        try:
            token_data = token_manager.get_token(user_id)
            if not token_data:
                return Response(
                    {'error': f'Usu├írio {user_id} n├úo encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({
                'user_id': token_data['user_id'],
                'token_type': token_data['token_type'],
                'expires_at': token_data['expires_at'],
                'scope': token_data['scope'],
                'updated_at': token_data['updated_at'],
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Erro ao verificar status do token: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefreshTokenView(APIView):
    """
    POST /users/{user_id}/token/refresh
    For├ºa um refresh do token manualmente.
    """

    def post(self, request, user_id):
        try:
            token_data = token_manager.get_token(user_id)
            if not token_data:
                return Response(
                    {'error': f'Usu├írio {user_id} n├úo encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            new_token = token_manager.refresh_token(token_data)
            return Response({
                'message': 'Token atualizado com sucesso!',
                'user_id': new_token['user_id'],
                'expires_at': new_token['expires_at'],
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Erro ao fazer refresh: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MyProductsView(APIView):
    """
    GET /users/{user_id}/myproducts
    Retorna os produtos do cache Supabase (atualizado a cada 1h em background).
    Muito mais leve ÔÇö zero chamadas ao ML API nesta rota.
    """

    def get(self, request, user_id):
        try:
            # Verifica se o usu├írio existe
            token_data = token_manager.get_token(user_id)
            if not token_data:
                return Response(
                    {'error': f'Usu├írio {user_id} n├úo encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            logger.info(f'Buscando produtos do cache Supabase para user_id={user_id}...')

            result = get_cached_products(user_id)

            # Se o cache est├í vazio, faz um sync imediato
            if result['total_produtos'] == 0:
                logger.info(f'Cache vazio ÔÇö executando sync imediato para user_id={user_id}...')
                run_sync(user_id)
                result = get_cached_products(user_id)

            # Adiciona info do ultimo sync
            sync_info = get_sync_status()
            result['ultimo_sync'] = sync_info.get('last_sync_at') if sync_info else None
            result['sync_status'] = sync_info.get('status') if sync_info else None

            logger.info(f'Retornando {result["total_produtos"]} produtos do cache.')

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Erro ao buscar produtos: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SyncProductsView(APIView):
    """
    POST /users/{user_id}/myproducts/sync
    Forca uma sincronizacao imediata dos produtos (ML -> Supabase).
    """

    def post(self, request, user_id):
        try:
            # Verifica se o usu├írio existe
            token_data = token_manager.get_token(user_id)
            if not token_data:
                return Response(
                    {'error': f'Usu├írio {user_id} n├úo encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            logger.info(f'Sync manual de produtos solicitado para user_id={user_id}...')
            run_sync(user_id)
            sync_info = get_sync_status()
            return Response({
                'message': 'Sincronizacao concluida!',
                'total_items': sync_info.get('total_items', 0),
                'last_sync_at': sync_info.get('last_sync_at'),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'Erro no sync manual: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MyOrdersView(APIView):
    """
    GET /users/{user_id}/myorders
    Retorna os pedidos do cache Supabase (atualizado a cada 1h em background).
    Formato identico ao meli_vendas_detalhadas.json.
    """

    def get(self, request, user_id):
        try:
            # Verifica se o usu├írio existe
            token_data = token_manager.get_token(user_id)
            if not token_data:
                return Response(
                    {'error': f'Usu├írio {user_id} n├úo encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            logger.info(f'Buscando pedidos do cache Supabase para user_id={user_id}...')

            result = get_cached_orders(user_id)

            # Se o cache est├í vazio, faz um sync imediato
            if not result.get('vendas_detalhadas'):
                logger.info(f'Cache de pedidos vazio ÔÇö executando sync imediato para user_id={user_id}...')
                run_orders_sync(user_id)
                result = get_cached_orders(user_id)

            # Adiciona info do ultimo sync
            sync_info = get_orders_sync_status()
            result['ultimo_sync'] = sync_info.get('last_sync_at') if sync_info else None
            result['sync_status'] = sync_info.get('status') if sync_info else None

            logger.info(f'Retornando {result["total_linhas"]} linhas do cache.')

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Erro ao buscar pedidos: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SyncOrdersView(APIView):
    """
    POST /users/{user_id}/myorders/sync
    Forca uma sincronizacao imediata dos pedidos (ML -> Supabase).
    """

    def post(self, request, user_id):
        try:
            # Verifica se o usu├írio existe
            token_data = token_manager.get_token(user_id)
            if not token_data:
                return Response(
                    {'error': f'Usu├írio {user_id} n├úo encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            logger.info(f'Sync manual de pedidos solicitado para user_id={user_id}...')
            run_orders_sync(user_id)
            sync_info = get_orders_sync_status()
            return Response({
                'message': 'Sincronizacao de pedidos concluida!',
                'total_items': sync_info.get('total_items', 0),
                'last_sync_at': sync_info.get('last_sync_at'),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'Erro no sync manual de pedidos: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DebugEnvView(APIView):
    """
    GET /debug/env
    Mostra quais variaveis de ambiente estao configuradas (sem expor valores).
    Util para diagnosticar problemas no deploy.
    """

    def get(self, request):
        import os
        from django.conf import settings as s

        checks = {
            'SUPABASE_URL': bool(s.SUPABASE_URL),
            'SUPABASE_KEY': bool(s.SUPABASE_KEY),
            'ML_APP_ID': bool(s.ML_APP_ID),
            'ML_SECRET_KEY': bool(s.ML_SECRET_KEY),
            'ML_REDIRECT_URI': bool(s.ML_REDIRECT_URI),
            'DEBUG': s.DEBUG,
        }

        # Testa conexao Supabase
        supabase_ok = False
        supabase_error = None
        token_found = False
        try:
            from .supabase_client import get_supabase_client
            sb = get_supabase_client()
            supabase_ok = True
            result = sb.table('mercadolivre_tokens').select('user_id').limit(1).execute()
            token_found = bool(result.data)
        except Exception as e:
            supabase_error = str(e)

        return Response({
            'env_vars_configuradas': checks,
            'supabase_conectado': supabase_ok,
            'supabase_erro': supabase_error,
            'token_no_banco': token_found,
        })


class ProductAdsView(APIView):
    """
    GET /users/{user_id}/productads?period=30
    Retorna metricas de Product Ads do Mercado Livre.
    Periodos permitidos: 7, 15, 30, 60, 90 (padrao: 30).

    Resposta:
    {
        "period_days": 30,
        "dashboard": {
            "investment": ...,
            "revenue": ...,
            "sales": ...,
            "impressions": ...,
            "clicks": ...,
            "roas": ...
        },
        "campaigns": [...]
    }
    """

    ALLOWED_PERIODS = [7, 15, 30, 60, 90]

    def get(self, request, user_id):
        try:
            # Verifica se o usu├írio existe
            token_data = token_manager.get_token(user_id)
            if not token_data:
                return Response(
                    {'error': f'Usu├írio {user_id} n├úo encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Periodo via query param (?period=30)
            period_days = int(request.query_params.get('period', 30))
            if period_days not in self.ALLOWED_PERIODS:
                return Response(
                    {'error': f'Periodo invalido. Use: {self.ALLOWED_PERIODS}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Token do Supabase
            access_token = token_manager.ensure_valid_token(user_id)
            if not access_token:
                return Response(
                    {'error': 'Nenhum token valido encontrado.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            api_base = settings.ML_API_BASE

            # ========== 1. Buscar advertiser ==========
            headers_v1 = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Api-Version': '1',
            }

            resp_adv = http_requests.get(
                f'{api_base}/advertising/advertisers',
                headers=headers_v1,
                params={'product_id': 'PADS'},
                timeout=30,
            )
            resp_adv.raise_for_status()
            adv_data = resp_adv.json()

            advertisers = adv_data.get('advertisers', [])
            if not advertisers:
                return Response(
                    {'error': 'Nenhum advertiser encontrado.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            advertiser_id = advertisers[0]['advertiser_id']
            site_id = advertisers[0]['site_id']

            # ========== 2. Buscar campanhas + metricas ==========
            headers_v2 = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'api-version': '2',
            }

            date_to = datetime.today()
            date_from = date_to - timedelta(days=period_days)

            metrics = (
                'clicks,prints,cost,units_quantity,'
                'direct_amount,indirect_amount,total_amount,roas'
            )

            resp_campaigns = http_requests.get(
                f'{api_base}/advertising/{site_id}/advertisers/'
                f'{advertiser_id}/product_ads/campaigns/search',
                headers=headers_v2,
                params={
                    'limit': 50,
                    'offset': 0,
                    'date_from': date_from.strftime('%Y-%m-%d'),
                    'date_to': date_to.strftime('%Y-%m-%d'),
                    'metrics': metrics,
                },
                timeout=30,
            )
            resp_campaigns.raise_for_status()
            campaigns = resp_campaigns.json().get('results', [])

            # ========== 3. Gerar resumo dashboard ==========
            summary = {
                'investment': 0,
                'revenue': 0,
                'sales': 0,
                'impressions': 0,
                'clicks': 0,
            }

            for c in campaigns:
                m = c.get('metrics', {})
                summary['investment'] += m.get('cost', 0)
                summary['revenue'] += m.get('total_amount', 0)
                summary['sales'] += m.get('units_quantity', 0)
                summary['impressions'] += m.get('prints', 0)
                summary['clicks'] += m.get('clicks', 0)

            summary['roas'] = (
                round(summary['revenue'] / summary['investment'], 2)
                if summary['investment'] > 0 else 0
            )

            # Arredondar valores monetarios
            summary['investment'] = round(summary['investment'], 2)
            summary['revenue'] = round(summary['revenue'], 2)

            result = {
                'period_days': period_days,
                'dashboard': summary,
                'campaigns': campaigns,
            }

            return Response(result, status=status.HTTP_200_OK)

        except http_requests.exceptions.RequestException as e:
            logger.error(f'Erro na API do Mercado Livre (Product Ads): {e}')
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_detail = e.response.text
            return Response(
                {'error': error_detail},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            logger.error(f'Erro na rota /productads: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CampaignAdsView(APIView):
    """
    GET /users/{user_id}/productads/campaigns/{campaign_identifier}/ads
    Retorna os an├║ncios pertencentes a uma campanha, aceitando o ID ou o Nome da campanha.
    """

    def get(self, request, user_id, campaign_identifier):
        try:
            # Verifica se o usu├írio existe e pega o token
            token_data = token_manager.get_token(user_id)
            if not token_data:
                return Response(
                    {'error': f'Usu├írio {user_id} n├úo encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            access_token = token_manager.ensure_valid_token(user_id)
            if not access_token:
                return Response(
                    {'error': 'Nenhum token valido encontrado.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            api_base = settings.ML_API_BASE

            # ========== 1. Buscar advertiser ==========
            headers_v1 = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Api-Version': '1',
            }

            resp_adv = http_requests.get(
                f'{api_base}/advertising/advertisers',
                headers=headers_v1,
                params={'product_id': 'PADS'},
                timeout=30,
            )
            resp_adv.raise_for_status()
            adv_data = resp_adv.json()
            advertisers = adv_data.get('advertisers', [])
            if not advertisers:
                return Response(
                    {'error': 'Nenhum advertiser encontrado.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            advertiser_id = advertisers[0]['advertiser_id']
            site_id = advertisers[0]['site_id']

            headers_v2 = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'api-version': '2',
            }

            # ========== 2. Resolver `campaign_identifier` ==========
            resolved_campaign_id = campaign_identifier

            # Se for string (n├úo cont├®m s├│ d├¡gitos), busca as campanhas para achar o id do nome
            if not str(campaign_identifier).isdigit():
                resp_campaigns = http_requests.get(
                    f'{api_base}/advertising/{site_id}/advertisers/'
                    f'{advertiser_id}/product_ads/campaigns/search',
                    headers=headers_v2,
                    params={'limit': 100, 'offset': 0},
                    timeout=30,
                )
                resp_campaigns.raise_for_status()
                campaigns = resp_campaigns.json().get('results', [])
                
                campaign_match = next((c for c in campaigns if c.get('name', '').lower() == str(campaign_identifier).lower()), None)
                if not campaign_match:
                    return Response(
                        {'error': f'Campanha n├úo encontrada com o nome: {campaign_identifier}. Verifique se ├® exatamente o mesmo nome.'},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                resolved_campaign_id = campaign_match['id']

            # ========== 3. Buscar os an├║ncios da campanha ==========
            # A API do Mercado Livre exige date_from e date_to quando metrics est├úo sendo solicitadas.
            period_days = int(request.query_params.get('period', 30))
            date_to_dt = datetime.today()
            date_from_dt = date_to_dt - timedelta(days=period_days)
            
            metrics_ads = (
                'clicks,prints,cost,units_quantity,'
                'direct_amount,indirect_amount,total_amount,roas'
            )
            resp_ads = http_requests.get(
                f'{api_base}/advertising/{site_id}/advertisers/'
                f'{advertiser_id}/product_ads/ads/search',
                headers=headers_v2,
                params={
                    'filters[campaign_id]': resolved_campaign_id,
                    'metrics': metrics_ads,
                    'date_from': date_from_dt.strftime('%Y-%m-%d'),
                    'date_to': date_to_dt.strftime('%Y-%m-%d'),
                    'limit': 100,
                    'offset': 0
                },
                timeout=30,
            )
            resp_ads.raise_for_status()

            ads_data = resp_ads.json()
            ads_results = ads_data.get('results', [])

            # ========== 4. Enriquecer an├║ncios com imagens dos produtos ==========
            item_ids = list({ad['item_id'] for ad in ads_results if ad.get('item_id')})

            item_data_map = {}
            if item_ids:
                try:
                    from .supabase_client import get_supabase_client
                    sb = get_supabase_client()
                    
                    # Buscar produtos cacheados em lotes para evitar payload gigante na query
                    chunk_size = 100
                    for i in range(0, len(item_ids), chunk_size):
                        chunk = item_ids[i:i + chunk_size]
                        resp = sb.table('mercadolivre_products') \
                                 .select('item_id, titulo, preco, foto, permalink') \
                                 .eq('user_id', user_id) \
                                 .in_('item_id', chunk) \
                                 .execute()
                        
                        if resp.data:
                            for row in resp.data:
                                item_data_map[row['item_id']] = {
                                    'image': row.get('foto') or '',
                                    'price': float(row.get('preco')) if row.get('preco') is not None else None,
                                    'original_price': None, # Cach├¬ atual n├úo possui pre├ºo original
                                    'title': row.get('titulo') or '',
                                    'permalink': row.get('permalink') or '',
                                }
                except Exception as db_err:
                    logger.warning(f"Erro ao buscar itens no banco para a campanha, fallback vazio: {db_err}")

            # Enriquece cada an├║ncio com imagem e pre├ºo correto do item
            for ad in ads_results:
                item_data = item_data_map.get(ad.get('item_id'), {})
                
                # Tratar fallback do pr├│prio objeto ad do Ads API (tem thumbnail, price, title)
                ad['image'] = item_data.get('image') or ad.get('thumbnail', '')
                ad['price'] = item_data.get('price') or ad.get('price')
                ad['original_price'] = item_data.get('original_price')
                
                # Garante que o titulo e o permalink do DB sobrescrevam se existirem
                if item_data.get('title'):
                    ad['title'] = item_data.get('title')
                if item_data.get('permalink'):
                    ad['permalink'] = item_data.get('permalink')

            return Response({
                'requested_campaign': campaign_identifier,
                'resolved_campaign_id': resolved_campaign_id,
                'total': ads_data.get('paging', {}).get('total', 0),
                'results': ads_results
            }, status=status.HTTP_200_OK)

        except http_requests.exceptions.RequestException as e:
            logger.error(f'Erro na API do Mercado Livre (Ads list): {e}')
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_detail = e.response.text
            return Response(
                {'error': error_detail},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            logger.error(f'Erro na rota de ads da ampanha: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

