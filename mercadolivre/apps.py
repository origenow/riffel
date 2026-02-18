import logging
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class MercadolivreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mercadolivre'

    def ready(self):
        """
        Quando a aplicação inicia, verifica se o token precisa de refresh
        e faz automaticamente em background.
        """
        import os
        # Evita executar duas vezes (Django reloader)
        if os.environ.get('RUN_MAIN') != 'true':
            return

        thread = threading.Thread(target=self._startup_token_check, daemon=True)
        thread.start()

    def _startup_token_check(self):
        """Verifica e faz refresh do token ao iniciar a aplicação."""
        import time
        # Pequeno delay para garantir que tudo carregou
        time.sleep(2)

        try:
            from .token_manager import token_manager

            logger.info('=' * 50)
            logger.info('Verificando tokens do Mercado Livre no startup...')

            token_data = token_manager.get_token()

            if token_data:
                logger.info(
                    f'Token encontrado para user_id={token_data["user_id"]}. '
                    f'Expira em: {token_data["expires_at"]}'
                )
                logger.info('Token válido e pronto para uso!')
            else:
                logger.warning(
                    'Nenhum token encontrado no banco. '
                    'Salve um token inicial usando o comando seed_token.'
                )

            logger.info('=' * 50)

        except RuntimeError as e:
            logger.warning(f'Supabase nao configurado - pulando verificacao de token: {e}')
        except Exception as e:
            logger.error(f'Erro ao verificar token no startup: {e}')
