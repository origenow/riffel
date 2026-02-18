"""
Cliente Supabase singleton para reutilização em toda a aplicação.
Inicialização lazy para não falhar durante build (collectstatic/migrate).
"""

import logging

from supabase import create_client, Client
from django.conf import settings

logger = logging.getLogger(__name__)

_supabase_client: Client = None


def get_supabase_client() -> Client:
    """Retorna uma instância singleton do cliente Supabase."""
    global _supabase_client
    if _supabase_client is None:
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_KEY
        if not url or not key:
            raise RuntimeError(
                'SUPABASE_URL e SUPABASE_KEY devem estar configurados nas variaveis de ambiente.'
            )
        _supabase_client = create_client(url, key)
        logger.info('Cliente Supabase inicializado.')
    return _supabase_client
