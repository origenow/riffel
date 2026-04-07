"""
Views de autenticacao OAuth2 do Mercado Livre.
"""

import base64
import json
import logging
import threading
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView

from .ml_api import ml_api
from .orders_sync import run_orders_sync
from .products_sync import run_sync
from .token_manager import token_manager

logger = logging.getLogger(__name__)
DEFAULT_FRONTEND_URL = "https://riffel.origenow.com.br"


def encode_state(payload: dict) -> str:
    raw = json.dumps(payload).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_state(state: str | None) -> dict:
    if not state:
        return {}

    try:
        padded = state + "=" * (-len(state) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode()).decode()
        payload = json.loads(decoded)
        return payload if isinstance(payload, dict) else {}
    except Exception as exc:
        logger.warning(f"Falha ao decodificar state OAuth: {exc}")
        return {}


def build_frontend_redirect(path: str, params: dict | None = None, frontend_base: str | None = None) -> str:
    configured_frontend = getattr(settings, "FRONTEND_URL", DEFAULT_FRONTEND_URL)
    base = (frontend_base or configured_frontend).rstrip("/")
    clean_path = f"/{path.lstrip('/')}" if path else ""
    query = urlencode({key: value for key, value in (params or {}).items() if value not in (None, "")})
    return f"{base}{clean_path}{f'?{query}' if query else ''}"


class AuthLoginView(APIView):
    """
    GET /auth/login
    Redireciona o usuario para a pagina de autorizacao do Mercado Livre.
    """

    def get(self, request):
        auth_url = "https://auth.mercadolivre.com.br/authorization"
        configured_frontend = getattr(settings, "FRONTEND_URL", DEFAULT_FRONTEND_URL)
        redirect_to = request.query_params.get("redirect_to") or configured_frontend
        state = encode_state({"redirect_to": redirect_to})
        params = {
            "response_type": "code",
            "client_id": settings.ML_APP_ID,
            "redirect_uri": settings.ML_REDIRECT_URI,
            "state": state,
            "scope": "offline_access read write",
        }

        authorization_url = f"{auth_url}?{urlencode(params)}"
        logger.info(f"Redirecionando para autorizacao ML: {authorization_url}")

        return redirect(authorization_url)


class AuthCallbackView(APIView):
    """
    GET /auth/callback?code=TG-xxxxx
    Recebe o codigo de autorizacao do Mercado Livre,
    troca por token e salva no Supabase junto com dados do usuario.
    """

    def get(self, request):
        code = request.query_params.get("code")
        error = request.query_params.get("error")
        state_data = decode_state(request.query_params.get("state"))
        configured_frontend = getattr(settings, "FRONTEND_URL", DEFAULT_FRONTEND_URL)
        frontend_base = state_data.get("redirect_to") or configured_frontend

        if error:
            logger.error(f"Erro na autorizacao ML: {error}")
            return redirect(
                build_frontend_redirect(
                    "/erro-autorizacao",
                    {"error": error},
                    frontend_base,
                )
            )

        if not code:
            return redirect(
                build_frontend_redirect(
                    "/erro-autorizacao",
                    {"error": "codigo_nao_fornecido"},
                    frontend_base,
                )
            )

        try:
            logger.info("Trocando codigo por token...")
            token_data = token_manager.exchange_code(code)
            user_id = token_data["user_id"]

            logger.info(f"Buscando dados do usuario {user_id}...")
            user_info = ml_api.get_me(user_id)

            logger.info("Salvando dados do usuario no Supabase...")
            token_manager.update_user_info(user_id, user_info)

            def sync_user_data():
                try:
                    logger.info(f"[BACKGROUND] Iniciando sync de produtos para user_id={user_id}...")
                    run_sync(user_id)
                    logger.info(f"[BACKGROUND] Sync de produtos concluido para user_id={user_id}.")
                except Exception as exc:
                    logger.error(f"[BACKGROUND] Erro no sync de produtos para user_id={user_id}: {exc}")

                try:
                    logger.info(f"[BACKGROUND] Iniciando sync de pedidos para user_id={user_id}...")
                    run_orders_sync(user_id)
                    logger.info(f"[BACKGROUND] Sync de pedidos concluido para user_id={user_id}.")
                except Exception as exc:
                    logger.error(f"[BACKGROUND] Erro no sync de pedidos para user_id={user_id}: {exc}")

            sync_thread = threading.Thread(target=sync_user_data, daemon=True, name=f"sync-user-{user_id}")
            sync_thread.start()
            logger.info(f"Sync em background iniciado para user_id={user_id}.")

            logger.info(f"Autenticacao bem-sucedida para user_id={user_id}. Redirecionando...")
            return redirect(
                build_frontend_redirect(
                    "/",
                    {
                        "auth": "success",
                        "user_id": user_id,
                        "nickname": user_info.get("nickname", ""),
                        "first_name": user_info.get("first_name", ""),
                    },
                    frontend_base,
                )
            )

        except Exception as exc:
            logger.error(f"Erro no callback OAuth2: {exc}")
            return redirect(
                build_frontend_redirect(
                    "/erro-autorizacao",
                    {"error": "oauth_callback_failed"},
                    frontend_base,
                )
            )
