"""
Cliente Supabase singleton para reutilização em toda a aplicação.
"""

from supabase import create_client, Client
from django.conf import settings


_supabase_client: Client = None


def get_supabase_client() -> Client:
    """Retorna uma instância singleton do cliente Supabase."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
    return _supabase_client
