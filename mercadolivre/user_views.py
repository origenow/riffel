"""
Views de gerenciamento de usuários conectados ao Mercado Livre.
"""

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .token_manager import token_manager
from .ml_api import ml_api

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

            # Remove o usuário
            success = token_manager.delete_user(user_id)
            
            if success:
                return Response({
                    'message': f'Usuário {user_id} removido com sucesso.',
                    'user_id': user_id
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Falha ao remover usuário.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f'Erro ao remover usuário {user_id}: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
