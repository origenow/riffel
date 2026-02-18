"""
Cliente para a API do Mercado Livre.
"""

import logging

import requests
from django.conf import settings

from .token_manager import token_manager

logger = logging.getLogger(__name__)


class MercadoLivreAPI:
    """Faz chamadas à API do Mercado Livre com token gerenciado automaticamente."""

    def __init__(self):
        self.api_base = settings.ML_API_BASE

    def _get_headers(self, access_token: str) -> dict:
        return {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

    def get_me(self, user_id: int = None) -> dict:
        """
        Retorna os dados da conta do usuário autenticado.
        GET https://api.mercadolibre.com/users/me
        """
        access_token = token_manager.ensure_valid_token(user_id)
        if not access_token:
            raise Exception('Nenhum token válido encontrado. Faça a autenticação primeiro.')

        url = f'{self.api_base}/users/me'
        headers = self._get_headers(access_token)

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f'Erro ao buscar /users/me: {e}')
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f'Response: {e.response.text}')
            raise


# Instância global
ml_api = MercadoLivreAPI()
