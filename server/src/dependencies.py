from fastapi import Depends
from services.auth import get_current_active_user, get_current_admin_user
from typing import Dict, Any

# Como os usuários agora são dicionários, vamos manter a tipagem genérica
# Você pode usar Dict ou criar um tipo específico
UserDict = Dict[str, Any]

def get_current_user_dep(current_user: UserDict = Depends(get_current_active_user)):
    """
    Dependência para obter o usuário atual ativo.
    Retorna um dicionário com os dados do usuário.
    """
    return current_user

def get_current_admin_dep(current_user: UserDict = Depends(get_current_admin_user)):
    """
    Dependência para obter o usuário atual ativo e com permissões de administrador.
    Retorna um dicionário com os dados do usuário.
    """
    return current_user

# Função auxiliar para verificar se o usuário é admin (opcional)
def is_admin_user(current_user: UserDict) -> bool:
    """Verifica se o usuário atual é administrador"""
    return current_user.get('is_admin', False)

# Função auxiliar para obter o username do usuário atual (opcional)
def get_username(current_user: UserDict) -> str:
    """Retorna o username do usuário atual"""
    return current_user.get('username', '')

# Função auxiliar para verificar se o usuário está ativo (opcional)
def is_active_user(current_user: UserDict) -> bool:
    """Verifica se o usuário atual está ativo"""
    return current_user.get('ativo', False)


