from services.auth import get_current_active_user
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import sqlite3
from database import get_db_connection
from schemas import Usuario, UsuarioCreate, UsuarioUpdate, Token
from crud import get_usuario_by_username, create_usuario, update_usuario
from services.auth import get_current_admin_user, authenticate_user, create_access_token, get_current_active_user
from typing import Dict, Any

# Type alias para usuário
UserDict = Dict[str, Any]

router = APIRouter(prefix="/api/v1", tags=["usuarios"])


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    """Endpoint de login que retorna um token JWT"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": user['username']})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/usuarios", response_model=Usuario)
async def create_new_user(
    usuario: UsuarioCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Cria um novo usuário (apenas administradores).
    """
    # Verificar se já existe
    if get_usuario_by_username(db, usuario.username):
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    return create_usuario(db, usuario)


@router.get("/usuarios", response_model=list[Usuario])
async def list_users(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Lista todos os usuários (apenas administradores).
    """
    cursor = db.execute(
        """
        SELECT id, username, is_admin, ativo, data_criacao
        FROM usuario
        ORDER BY username
        """
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@router.get("/usuarios/{username}", response_model=Usuario)
async def get_user(
    username: str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Obtém detalhes de um usuário específico (apenas administradores).
    """
    user = get_usuario_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Não retornar o hash da senha
    user_safe = {k: v for k, v in user.items() if k != 'hashed_password'}
    return user_safe


@router.put("/usuarios/{username}", response_model=Usuario)
async def update_user(
    username: str,
    usuario_update: UsuarioUpdate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Atualiza um usuário (apenas administradores).
    """
    user = update_usuario(db, username, usuario_update)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Não retornar o hash da senha
    user_safe = {k: v for k, v in user.items() if k != 'hashed_password'}
    return user_safe


@router.delete("/usuarios/{username}")
async def delete_user(
    username: str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Remove um usuário (apenas administradores).
    Não permite deletar o próprio usuário.
    """
    # Verificar se o usuário existe
    user = get_usuario_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Não permitir deletar o próprio usuário
    if username == current_user['username']:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own user"
        )

    # Deletar o usuário
    db.execute(
        "DELETE FROM usuario WHERE username = ?",
        (username,)
    )
    db.commit()

    return {"detail": f"User '{username}' deleted successfully"}


@router.post("/usuarios/me/change-password")
async def change_my_password(
    old_password: str,
    new_password: str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """
    Permite que um usuário mude sua própria senha.
    """
    from services.auth import verify_password, get_password_hash

    # Verificar senha atual
    user = get_usuario_by_username(db, current_user['username'])
    if not user or not verify_password(old_password, user['hashed_password']):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    # Atualizar senha
    new_hashed = get_password_hash(new_password)
    db.execute(
        "UPDATE usuario SET hashed_password = ? WHERE username = ?",
        (new_hashed, current_user['username'])
    )
    db.commit()

    return {"detail": "Password updated successfully"}


@router.get("/usuarios/me", response_model=Usuario)
async def get_my_profile(
    current_user: UserDict = Depends(get_current_active_user)
):
    """
    Obtém o perfil do usuário autenticado.
    """
    # Não retornar o hash da senha
    user_safe = {k: v for k, v in current_user.items() if k !=
                 'hashed_password'}
    return user_safe


@router.put("/usuarios/me", response_model=Usuario)
async def update_my_profile(
    usuario_update: UsuarioUpdate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """
    Permite que um usuário atualize seu próprio perfil.
    (Apenas campos permitidos: is_admin não pode ser alterado pelo próprio usuário)
    """
    # Remover campos que o usuário não pode alterar em si mesmo
    update_data = usuario_update.dict(exclude_unset=True)

    # Usuário comum não pode alterar is_admin
    if 'is_admin' in update_data and not current_user.get('is_admin', False):
        del update_data['is_admin']

    # Se não houver campos para atualizar
    if not update_data:
        return get_my_profile(current_user)

    # Criar objeto de atualização
    from schemas import UsuarioUpdate
    user_update = UsuarioUpdate(**update_data)

    # Atualizar usuário
    user = update_usuario(db, current_user['username'], user_update)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Não retornar o hash da senha
    user_safe = {k: v for k, v in user.items() if k != 'hashed_password'}
    return user_safe



