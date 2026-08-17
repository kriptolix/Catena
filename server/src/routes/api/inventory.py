from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3

from database import get_db_connection
from schemas.equipment import EquipmentCreate, EquipmentUpdate
from schemas.reception import InventoryReceived
from cruds.equipment import (
    get_equipment, get_equipment_by_id, create_Equipment, 
    update_Equipment
)
from cruds.inventory import processar_inventario
from services.auth import get_current_active_user
from utils.asset_tag import generate_next_asset_tag
from typing import Optional, List, Dict, Any
from enums import StatusEquipment

UserDict = Dict[str, Any]

router = APIRouter(prefix="/api/v1", tags=["inventario"])

@router.post("/inventario", response_model=dict)
async def receber_inventario(
    payload: InventoryReceived,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    # ============================================================
    # 1. Dados básicos
    # ============================================================

    uuid = payload.identification.uuid if payload.identification else None

    manufacturer = (
        payload.equipment.manufacturer
        if payload.equipment
        else None
    )

    model = (
        payload.equipment.model
        if payload.equipment
        else None
    )

    serial_number = (
        payload.equipment.serial_number
        if payload.equipment
        else None
    )

    # Valores "N/A" não devem ser tratados como dados reais
    if uuid == "N/A":
        uuid = None

    if serial_number == "N/A":
        serial_number = None

    asset_tag = payload.asset_tag.strip() if payload.asset_tag else None

    # ============================================================
    # 2. Procurar Equipment existente
    # ============================================================

    equip = None

    if asset_tag:
        equip = get_equipment(db, asset_tag)

    if not equip and uuid:
        cursor = db.execute(
            """
            SELECT *
            FROM Equipment
            WHERE uuid = ?
            LIMIT 1
            """,
            (uuid,)
        )

        row = cursor.fetchone()

        if row:
            equip = dict(row)    

    # ============================================================
    # 4. Criar Equipment
    # ============================================================

    if not equip:

        novo_asset_tag = (
            asset_tag
            if asset_tag
            else generate_next_asset_tag()
        )

        equip_data = EquipmentCreate(
            asset_tag=novo_asset_tag,
            uuid=uuid,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            location=payload.location,
            status=StatusEquipment.FUNCIONAL,
            warranty_start_date=None,
            warranty_period=None
        )

        equip = create_Equipment(
            db,
            equip_data,
            current_user["username"]
        )

    # ============================================================
    # 5. Atualizar Equipment existente
    # ============================================================

    else:

        update_data = {}

        if uuid and equip.get("uuid") != uuid:
            update_data["uuid"] = uuid

        if (
            manufacturer
            and equip.get("manufacturer_id") != manufacturer
        ):
            update_data["manufacturer_id"] = manufacturer

        if (
            model
            and equip.get("model_id") != model
        ):
            update_data["model_id"] = model

        if (
            serial_number
            and equip.get("serial_number") != serial_number
        ):
            update_data["serial_number"] = serial_number

        if (
            payload.location
            and equip.get("location") != payload.location
        ):
            update_data["location"] = payload.location

        if update_data:

            equip_update = EquipmentUpdate(
                **update_data
            )

            equip = update_Equipment(
                db,
                equip["asset_tag"],
                equip_update,
                current_user["username"]
            )

    # ============================================================
    # 6. Montar inventário de hardware
    # ============================================================

    inventario_data = {
        "cpu": (
            payload.processor.model_dump()
            if payload.processor
            else None
        ),

        "memoria": (
            payload.memory.model_dump()
            if payload.memory
            else None
        ),

        "armazenamento": [
            disco.model_dump()
            for disco in payload.disks
        ],

        "gpu": [
            video.model_dump()
            for video in payload.gpu
        ],

        "motherboard": (
            payload.motherboard.model_dump()
            if payload.motherboard
            else None
        ),

        "bios": (
            payload.bios.model_dump()
            if payload.bios
            else None
        ),

        "system": (
            payload.system.model_dump()
            if payload.system
            else None
        ),

        "json_original": payload.model_dump()
    }

    # ============================================================
    # 7. Salvar inventário
    # ============================================================

    equip_id = equip.get("id") if equip else None

    if equip_id:
        processar_inventario(
            db,
            equip_id,
            inventario_data,
            current_user["username"]
        )

    # ============================================================
    # 8. Retornar Equipment atualizado
    # ============================================================

    if equip and equip.get("asset_tag"):

        equip_atualizado = get_equipment(
            db,
            equip["asset_tag"]
        )

        if equip_atualizado:
            return dict(equip_atualizado)

    return dict(equip) if equip else {}

@router.get("/inventario/ultimo/{equipment_id}")
async def obter_ultimo_inventario(
    equipment_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Retorna o último inventário de hardware de um Equipment"""
    cursor = db.execute(
        """
        SELECT * FROM inventario_hardware
        WHERE equipment_id = ?
        ORDER BY collection_date DESC
        LIMIT 1
        """,
        (equipment_id,)
    )
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum inventário encontrado para este Equipment"
        )
    
    return dict(row)


@router.get("/inventario/historico/{equipment_id}")
async def obter_historico_inventario(
    equipment_id: int,
    limit: int = 10,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Retorna o histórico de inventários de um Equipment"""
    cursor = db.execute(
        """
        SELECT * FROM inventario_hardware
        WHERE equipment_id = ?
        ORDER BY collection_date DESC
        LIMIT ?
        """,
        (equipment_id, limit)
    )
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@router.post("/inventario/forcar/{equipment_id}")
async def forcar_inventario(
    equipment_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Força a criação de um novo registro de inventário para um Equipment"""
    # Verificar se Equipment existe
    equip = get_equipment_by_id(db, equipment_id)
    if not equip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment não encontrado"
        )
    
    # Buscar último inventário para usar como base
    cursor = db.execute(
        """
        SELECT * FROM inventario_hardware
        WHERE equipment_id = ?
        ORDER BY collection_date DESC
        LIMIT 1
        """,
        (equipment_id,)
    )
    ultimo = cursor.fetchone()
    
    if not ultimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment não possui inventário anterior"
        )
    
    # Criar novo inventário com os mesmos dados
    inventario_data = {
        'cpu': ultimo['cpu'],
        'memoria': ultimo['memoria'],
        'armazenamento': ultimo['armazenamento'],
        'gpu': ultimo['gpu'],
        'motherboard': ultimo['motherboard'],
        'bios': ultimo['bios'],
        'system': ultimo['system'],
        'json_original': ultimo['json_original']
    }
    
    # Forçar criação de novo registro (muda a collection_date)
    novo_inventario = processar_inventario(
        db, 
        equipment_id, 
        inventario_data, 
        current_user['username']
    )
    
    return {
        "message": "Novo registro de inventário criado com sucesso",
        "inventario": dict(novo_inventario) if novo_inventario else None
    }