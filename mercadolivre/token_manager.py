"""
Gerenciador de tokens do Mercado Livre.
Responsável por salvar, consultar e fazer refresh automático dos tokens.
"""

import logging
from datetime import datetime, timezone, timedelta

import requests
from django.conf import settings

from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

TABLE_NAME = 'mercadolivre_tokens'


class TokenManager:
    """Gerencia tokens de acesso do Mercado Livre no Supabase."""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.app_id = settings.ML_APP_ID
        self.secret_key = settings.ML_SECRET_KEY
        self.redirect_uri = settings.ML_REDIRECT_URI
        self.api_base = settings.ML_API_BASE

    def get_token(self, user_id: int = None) -> dict | None:
        """
        Busca o token do banco. Se user_id não for passado, retorna o primeiro.
        Se o token estiver expirado ou próximo de expirar, faz refresh automaticamente.
        """
        try:
            query = self.supabase.table(TABLE_NAME).select('*')

            if user_id:
                query = query.eq('user_id', user_id)

            result = query.order('updated_at', desc=True).limit(1).execute()

            if not result.data:
                logger.warning('Nenhum token encontrado no banco.')
                return None

            token_data = result.data[0]

            # Verifica se precisa de refresh (expira em menos de 30 minutos)
            expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            time_remaining = expires_at - now

            if time_remaining < timedelta(minutes=30):
                logger.info(
                    f'Token expira em {time_remaining}. Fazendo refresh automático...'
                )
                token_data = self.refresh_token(token_data)

            return token_data

        except Exception as e:
            logger.error(f'Erro ao buscar token: {e}')
            return None

    def save_token(self, token_response: dict) -> dict:
        """
        Salva ou atualiza o token no Supabase.
        Calcula o expires_at baseado no expires_in.
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=token_response.get('expires_in', 21600))

        data = {
            'user_id': token_response['user_id'],
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'token_type': token_response.get('token_type', 'Bearer'),
            'expires_in': token_response.get('expires_in', 21600),
            'expires_at': expires_at.isoformat(),
            'scope': token_response.get('scope', ''),
            'updated_at': now.isoformat(),
        }

        try:
            # Tenta atualizar se já existe
            existing = (
                self.supabase.table(TABLE_NAME)
                .select('id')
                .eq('user_id', token_response['user_id'])
                .execute()
            )

            if existing.data:
                result = (
                    self.supabase.table(TABLE_NAME)
                    .update(data)
                    .eq('user_id', token_response['user_id'])
                    .execute()
                )
                logger.info(f'Token atualizado para user_id={token_response["user_id"]}')
            else:
                data['created_at'] = now.isoformat()
                result = (
                    self.supabase.table(TABLE_NAME)
                    .insert(data)
                    .execute()
                )
                logger.info(f'Token inserido para user_id={token_response["user_id"]}')

            return result.data[0] if result.data else data

        except Exception as e:
            logger.error(f'Erro ao salvar token: {e}')
            raise

    def refresh_token(self, token_data: dict) -> dict:
        """
        Faz o refresh do token usando o refresh_token armazenado.
        """
        logger.info(f'Iniciando refresh do token para user_id={token_data["user_id"]}...')

        url = f'{self.api_base}/oauth/token'
        payload = {
            'grant_type': 'refresh_token',
            'client_id': self.app_id,
            'client_secret': self.secret_key,
            'refresh_token': token_data['refresh_token'],
        }
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
        }

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=30)
            response.raise_for_status()
            new_token = response.json()

            logger.info(f'Refresh realizado com sucesso! Novo token obtido.')

            # Salva o novo token no banco
            saved = self.save_token(new_token)
            return saved

        except requests.exceptions.RequestException as e:
            logger.error(f'Erro ao fazer refresh do token: {e}')
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f'Response: {e.response.text}')
            raise

    def exchange_code(self, code: str) -> dict:
        """
        Troca o authorization_code por um token de acesso.
        Usado na primeira autenticação.
        """
        url = f'{self.api_base}/oauth/token'
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.secret_key,
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
        }

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            # Salva no banco
            saved = self.save_token(token_data)
            return saved

        except requests.exceptions.RequestException as e:
            logger.error(f'Erro ao trocar code por token: {e}')
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f'Response: {e.response.text}')
            raise

    def ensure_valid_token(self, user_id: int = None) -> str | None:
        """
        Garante que temos um token válido e retorna o access_token.
        Faz refresh se necessário.
        """
        token_data = self.get_token(user_id)
        if token_data:
            return token_data['access_token']
        return None


# Instância global
token_manager = TokenManager()
