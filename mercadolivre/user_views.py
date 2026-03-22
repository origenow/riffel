"""
Views de gerenciamento de usuários conectados ao Mercado Livre.
"""

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .token_manager import token_manager
from .ml_api import ml_api
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class UsersListView(APIView):
    """
    GET /users
    Lista todos os usuários conectados com suas informações.
    """

    def get(self, request):
        try:
            users = token_manager.get_all_users()
            
            return Response({
                'total': len(users),
                'users': users
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Erro ao listar usuários: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserDetailView(APIView):
    """
    GET /users/{user_id}
    Retorna detalhes de um usuário específico.
    """

    def get(self, request, user_id):
        try:
            token_data = token_manager.get_token(user_id)
            
            if not token_data:
                return Response(
                    {'error': f'Usuário {user_id} não encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({
                'user_id': token_data.get('user_id'),
                'nickname': token_data.get('nickname'),
                'first_name': token_data.get('first_name'),
                'token_type': token_data.get('token_type'),
                'expires_at': token_data.get('expires_at'),
                'scope': token_data.get('scope'),
                'updated_at': token_data.get('updated_at'),
                'last_updated_me': token_data.get('last_updated_me'),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Erro ao buscar usuário {user_id}: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserDeleteView(APIView):
    """
    DELETE /users/{user_id}
    Remove a conexão de um usuário.
    """

    def delete(self, request, user_id):
        try:
            # Verifica se o usuário existe
            token_data = token_manager.get_token(user_id)
            
            if not token_data:
                return Response(
                    {'error': f'Usuário {user_id} não encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            sb = get_supabase_client()
            
            # 1. Deletar produtos do usuário
            logger.info(f'Deletando produtos do user_id={user_id}...')
            products_result = sb.table('mercadolivre_products').delete().eq('user_id', user_id).execute()
            products_deleted = len(products_result.data) if products_result.data else 0
            logger.info(f'{products_deleted} produtos deletados.')
            
            # 2. Deletar pedidos do usuário
            logger.info(f'Deletando pedidos do user_id={user_id}...')
            orders_result = sb.table('mercadolivre_orders').delete().eq('user_id', user_id).execute()
            orders_deleted = len(orders_result.data) if orders_result.data else 0
            logger.info(f'{orders_deleted} pedidos deletados.')
            
            # 3. Deletar resumo de pedidos do usuário
            logger.info(f'Deletando resumo de pedidos do user_id={user_id}...')
            summary_result = sb.table('mercadolivre_orders_summary').delete().eq('user_id', user_id).execute()
            summary_deleted = len(summary_result.data) if summary_result.data else 0
            logger.info(f'{summary_deleted} resumos deletados.')
            
            # 4. Deletar token do usuário
            logger.info(f'Deletando token do user_id={user_id}...')
            success = token_manager.delete_user(user_id)
            
            if success:
                return Response({
                    'message': f'Usuário {user_id} e todos os seus dados removidos com sucesso.',
                    'user_id': user_id,
                    'deleted': {
                        'products': products_deleted,
                        'orders': orders_deleted,
                        'summary': summary_deleted,
                        'token': True
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Falha ao remover token do usuário.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f'Erro ao remover usuário {user_id}: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
