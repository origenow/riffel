"""
Views de autenticação OAuth2 do Mercado Livre.
"""

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .token_manager import token_manager
from .ml_api import ml_api

logger = logging.getLogger(__name__)


class AuthLoginView(APIView):
    """
    GET /auth/login
    Redireciona o usuário para a página de autorização do Mercado Livre.
    """

    def get(self, request):
        auth_url = 'https://auth.mercadolivre.com.br/authorization'
        params = {
            'response_type': 'code',
            'client_id': settings.ML_APP_ID,
            'redirect_uri': settings.ML_REDIRECT_URI,
        }
        
        authorization_url = f'{auth_url}?{urlencode(params)}'
        logger.info(f'Redirecionando para autorização ML: {authorization_url}')
        
        return redirect(authorization_url)


class AuthCallbackView(APIView):
    """
    GET /auth/callback?code=TG-xxxxx
    Recebe o código de autorização do Mercado Livre,
    troca por token e salva no Supabase junto com dados do usuário.
    """

    def get(self, request):
        code = request.query_params.get('code')
        error = request.query_params.get('error')

        if error:
            logger.error(f'Erro na autorização ML: {error}')
            return Response(
                {'error': f'Autorização negada: {error}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not code:
            return Response(
                {'error': 'Código de autorização não fornecido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. Trocar código por token
            logger.info('Trocando código por token...')
            token_data = token_manager.exchange_code(code)
            user_id = token_data['user_id']
            
            # 2. Buscar dados do usuário no ML
            logger.info(f'Buscando dados do usuário {user_id}...')
            user_info = ml_api.get_me(user_id)
            
            # 3. Atualizar token com dados do usuário
            logger.info('Salvando dados do usuário no Supabase...')
            token_manager.update_user_info(user_id, user_info)
            
            # 4. Redirecionar para o frontend
            logger.info(f'Autenticação bem-sucedida para user_id={user_id}. Redirecionando...')
            redirect_url = f'https://riffel.origenow.com.br/?auth=success&user_id={user_id}&nickname={user_info.get("nickname", "")}&first_name={user_info.get("first_name", "")}'
            return redirect(redirect_url)

        except Exception as e:
            logger.error(f'Erro no callback OAuth2: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
