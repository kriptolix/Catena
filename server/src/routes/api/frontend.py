from fastapi import APIRouter, Depends, HTTPException, Query, Request
import sqlite3
from typing import Optional, List
from database import get_db_connection
from schemas import (
    Equipment, EquipmentCreate, EquipmentUpdate, 
    DefeitoCreate, Defeito, AnnotationCreate, Annotation, 
    InventarioHardware, Historico
)
from crud import (
    get_Equipment, get_Equipments, create_Equipment, 
    update_Equipment, delete_Equipment,
    create_defeito, resolver_defeito, create_annotation
)
from services.auth import get_current_active_user, get_current_admin_user
from enums import statusEquipment
from typing import Dict, Any

# Type alias para usuário
UserDict = Dict[str, Any]

router = APIRouter(prefix="/api/v1/Equipments", tags=["Equipments"])

@router.get("/", response_model=List[Equipment])
async def list_Equipments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    asset_number Optional[str] = None,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[statusEquipment] = None,
    garantia: Optional[str] = None,  # 'SIM' ou 'NAO'
    defeito: Optional[bool] = False,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: Optional[UserDict] = Depends(get_current_active_user)
):
    """
    Lista Equipments com filtros opcionais.
    Qualquer usuário autenticado pode visualizar.
    """
    filters = {}
    if asset_number
        filters['tombo'] = tombo
    if manufacturer:
        filters['manufacturer'] = manufacturer
    if model:
        filters['model'] = model
    if location:
        filters['location'] = location
    if status:
        filters['status'] = status.value if hasattr(status, 'value') else status
    if garantia:
        filters['garantia'] = garantia
    if defeito:
        filters['defeito'] = defeito
    
    Equipments = get_Equipments(db, skip, limit, filters)
    return Equipments


@router.get("/{tombo}", response_model=Equipment)
async def get_Equipment_detail(
    asset_number str, 
    db: sqlite3.Connection = Depends(get_db_connection), 
    current_user: Optional[UserDict] = Depends(get_current_active_user)
):
    """Obtém detalhes de um Equipment específico"""
    equip = get_Equipment(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipment não encontrado")
    return equip


@router.post("/", response_model=Equipment)
async def create_new_Equipment(
    Equipment: EquipmentCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Cria um novo Equipment"""
    try:
        return create_Equipment(db, Equipment, current_user['username'])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tombo}", response_model=Equipment)
async def update_existing_Equipment(
    asset_number str,
    Equipment_update: EquipmentUpdate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Atualiza um Equipment existente"""
    equip = update_Equipment(db, tombo, Equipment_update, current_user['username'])
    if not equip:
        raise HTTPException(status_code=404, detail="Equipment não encontrado")
    return equip


@router.delete("/{tombo}")
async def delete_existing_Equipment(
    asset_number str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)  # apenas admin
):
    """Remove um Equipment (apenas administradores)"""
    success = delete_Equipment(db, tombo, current_user['username'])
    if not success:
        raise HTTPException(status_code=404, detail="Equipment não encontrado")
    return {"detail": "Equipment removido"}


# --- Defeitos ---
@router.post("/{tombo}/defeitos", response_model=Defeito)
async def add_defeito(
    asset_number str,
    defeito: DefeitoCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Adiciona um defeito a um Equipment"""
    equip = get_Equipment(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipment não encontrado")
    
    # Atribuir o equipment_id ao defeito
    defeito.equipment_id = equip['id']
    return create_defeito(db, defeito, current_user['username'])


@router.patch("/defeitos/{defeito_id}/resolver", response_model=Defeito)
async def resolve_defeito(
    defeito_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Marca um defeito como resolvido"""
    defeito = resolver_defeito(db, defeito_id, current_user['username'])
    if not defeito:
        raise HTTPException(status_code=404, detail="Defeito não encontrado")
    return defeito


# --- Anotações ---
@router.post("/{tombo}/anotacoes", response_model=Annotation)
async def add_annotation(
    asset_number str,
    annotation: AnnotationCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Adiciona uma anotação a um Equipment"""
    equip = get_Equipment(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipment não encontrado")
    
    annotation.equipment_id = equip['id']
    annotation.user = current_user['username']
    return create_annotation(db, annotation)


# --- Histórico ---
@router.get("/{tombo}/historico", response_model=List[Historico])
async def get_historico(
    asset_number str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: Optional[UserDict] = Depends(get_current_active_user)
):
    """Obtém o histórico de alterações de um Equipment"""
    equip = get_Equipment(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipment não encontrado")
    
    cursor = db.execute(
        """
        SELECT * FROM historico
        WHERE equipment_id = ?
        ORDER BY data_hora DESC
        """,
        (equip['id'],)
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


# --- Inventários ---
@router.get("/{tombo}/inventarios", response_model=List[InventarioHardware])
async def get_inventarios(
    asset_number str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: Optional[UserDict] = Depends(get_current_active_user)
):
    """Obtém o histórico de inventários de hardware de um Equipment"""
    equip = get_Equipment(db, tombo)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipment não encontrado")
    
    cursor = db.execute(
        """
        SELECT * FROM inventario_hardware
        WHERE equipment_id = ?
        ORDER BY collection_date DESC
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

@frontend_router.get("/Equipments/{tombo}", response_class=HTMLResponse)
async def Equipment_detail(request: Request, asset_number str):
    return templates.TemplateResponse(
        request,
        "Equipment.html", 
        {"tombo": tombo}
    )

@frontend_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@frontend_router.get("/adicionar", response_class=HTMLResponse)
async def adicionar_Equipment(request: Request):
    return templates.TemplateResponse(
        request,
        "adicionar_Equipment.html", 
        {}
    )