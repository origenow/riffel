"""
Management command para salvar o token inicial do Mercado Livre no Supabase.
Uso: python manage.py seed_token
"""

from django.core.management.base import BaseCommand

from mercadolivre.token_manager import token_manager


class Command(BaseCommand):
    help = 'Salva o token inicial do Mercado Livre no Supabase'

    def handle(self, *args, **options):
        self.stdout.write('Salvando token inicial do Mercado Livre...')

        # Token fornecido pelo usuário
        token_data = {
            'access_token': 'APP_USR-4943523961409438-021212-e3b4aa7caa6d2948a46b50c0aa096e95-533863251',
            'token_type': 'Bearer',
            'expires_in': 21600,
            'scope': 'offline_access read urn:global:admin:info:/read-only urn:global:admin:oauth:/read-only urn:ml:all:comunication:/read-write urn:ml:all:publish-sync:/read-write urn:ml:mktp:ads:/read-write urn:ml:mktp:comunication:/read-write urn:ml:mktp:invoices:/read-write urn:ml:mktp:offers:/read-write urn:ml:mktp:orders-shipments:/read-write urn:ml:mktp:publish-sync:/read-write urn:ml:vis:comunication:/read-write urn:ml:vis:publish-sync:/read-write write',
            'user_id': 533863251,
            'refresh_token': 'TG-698e0062ce29160001e14f59-533863251',
        }

        try:
            saved = token_manager.save_token(token_data)
            self.stdout.write(self.style.SUCCESS(
                f'Token salvo com sucesso! user_id={saved.get("user_id", token_data["user_id"])}'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'Expira em: {saved.get("expires_at", "N/A")}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao salvar token: {e}'))
