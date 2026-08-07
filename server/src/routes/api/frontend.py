from fastapi import APIRouter, Depends, HTTPException, Query, Request
import sqlite3
from typing import Optional, List
from database import get_db
from schemas import (
    Equipamento, EquipamentoCreate, EquipamentoUpdate, 
    DefeitoCreate, Defeito, AnotacaoCreate, Anotacao, 
    InventarioHardware, Historico
)
from crud import (
    get_equipamento, get_equipamentos, create_equipamento, 
    update_equipamento, delete_equipamento,
    create_defeito, resolver_defeito, create_anotacao
)
from server.src.services.auth import get_current_active_user, get_current_admin_user
from enums import EstadoEquipamento
from typing import Dict, Any

# Type alias para usuário
UserDict = Dict[str, Any]

router = APIRouter(prefix="/api/v1/equipamentos", tags=["equipamentos"])

@router.get("/", response_model=List[Equipamento])
async def list_equipamentos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tombo: Optional[str] = None,
    fabricante: Optional[str] = None,
    modelo: Optional[str] = None,
    localizacao: Optional[str] = None,
    estado: Optional[EstadoEquipamento] = None,
    garantia: Optional[str] = None,  # 'SIM' ou 'NAO'
    defeito: Optional[bool] = False,
    db: sqlite3.Connection = Depends(get_db),
    current_user: Optional[UserDict] = Depends(get_current_active_user)
):
    """
    Lista equipamentos com filtros opcionais.
    Qualquer usuário autenticado pode visualizar.
    """
    filters = {}
    if tombo:
        filters['tombo'] = tombo
    if fabricante:
        filters['fabricante'] = fabricante
    if modelo:
        filters['modelo'] = modelo
    if localizacao:
        filters['localizacao'] = localizacao
    if estado:
        filters['estado'] = estado.value if hasattr(estado, 'value') else estado
    if garantia:
        filters['garantia'] = garantia
    if defeito:
        filters['defeito'] = defeito
    
    equipamentos = get_equipamentos(db, skip, limit, filters)
    return equipamentos


@router.get("/{tombo}", response_model=Equipamento)
async def get_equipamento_detail(
    tombo: str, 
    db: sqlite3.Connection = Depends(get_db), 
    current_user: Optional[UserDict] = Depends(get_current_active_user)
):
    """Obtém detalhes de um equipamento específico"""
    equip = get_equipamento(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    return equip


@router.post("/", response_model=Equipamento)
async def create_new_equipamento(
    equipamento: EquipamentoCreate,
    db: sqlite3.Connection = Depends(get_db),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Cria um novo equipamento"""
    try:
        return create_equipamento(db, equipamento, current_user['username'])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tombo}", response_model=Equipamento)
async def update_existing_equipamento(
    tombo: str,
    equipamento_update: EquipamentoUpdate,
    db: sqlite3.Connection = Depends(get_db),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Atualiza um equipamento existente"""
    equip = update_equipamento(db, tombo, equipamento_update, current_user['username'])
    if not equip:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    return equip


@router.delete("/{tombo}")
async def delete_existing_equipamento(
    tombo: str,
    db: sqlite3.Connection = Depends(get_db),
    current_user: UserDict = Depends(get_current_admin_user)  # apenas admin
):
    """Remove um equipamento (apenas administradores)"""
    success = delete_equipamento(db, tombo, current_user['username'])
    if not success:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    return {"detail": "Equipamento removido"}


# --- Defeitos ---
@router.post("/{tombo}/defeitos", response_model=Defeito)
async def add_defeito(
    tombo: str,
    defeito: DefeitoCreate,
    db: sqlite3.Connection = Depends(get_db),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Adiciona um defeito a um equipamento"""
    equip = get_equipamento(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    
    # Atribuir o equipamento_id ao defeito
    defeito.equipamento_id = equip['id']
    return create_defeito(db, defeito, current_user['username'])


@router.patch("/defeitos/{defeito_id}/resolver", response_model=Defeito)
async def resolve_defeito(
    defeito_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Marca um defeito como resolvido"""
    defeito = resolver_defeito(db, defeito_id, current_user['username'])
    if not defeito:
        raise HTTPException(status_code=404, detail="Defeito não encontrado")
    return defeito


# --- Anotações ---
@router.post("/{tombo}/anotacoes", response_model=Anotacao)
async def add_anotacao(
    tombo: str,
    anotacao: AnotacaoCreate,
    db: sqlite3.Connection = Depends(get_db),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Adiciona uma anotação a um equipamento"""
    equip = get_equipamento(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    
    anotacao.equipamento_id = equip['id']
    anotacao.usuario = current_user['username']
    return create_anotacao(db, anotacao)


# --- Histórico ---
@router.get("/{tombo}/historico", response_model=List[Historico])
async def get_historico(
    tombo: str,
    db: sqlite3.Connection = Depends(get_db),
    current_user: Optional[UserDict] = Depends(get_current_active_user)
):
    """Obtém o histórico de alterações de um equipamento"""
    equip = get_equipamento(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    
    cursor = db.execute(
        """
        SELECT * FROM historico
        WHERE equipamento_id = ?
        ORDER BY data_hora DESC
        """,
        (equip['id'],)
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


# --- Inventários ---
@router.get("/{tombo}/inventarios", response_model=List[InventarioHardware])
async def get_inventarios(
    tombo: str,
    db: sqlite3.Connection = Depends(get_db),
    current_user: Optional[UserDict] = Depends(get_current_active_user)
):
    """Obtém o histórico de inventários de hardware de um equipamento"""
    equip = get_equipamento(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    
    cursor = db.execute(
        """
        SELECT * FROM inventario_hardware
        WHERE equipamento_id = ?
        ORDER BY data_coleta DESC
        """,
        (equip['id'],)
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


# --- Frontend ---
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from templates.templates import templates

# Criar um router separado para frontend
frontend_router = APIRouter(tags=["frontend"])


@frontend_router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

@frontend_router.get("/equipamentos/{tombo}", response_class=HTMLResponse)
async def equipamento_detail(request: Request, tombo: str):
    return templates.TemplateResponse(
        request,
        "equipamento.html", 
        {"tombo": tombo}
    )

@frontend_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@frontend_router.get("/adicionar", response_class=HTMLResponse)
async def adicionar_equipamento(request: Request):
    return templates.TemplateResponse(
        request,
        "adicionar_equipamento.html", 
        {}
    )