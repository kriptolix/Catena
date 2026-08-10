from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3

from database import get_db_connection
from schemas import InventarioRecebido, EquipamentoCreate, Equipamento, EquipamentoUpdate
from crud import (
    get_equipamento, get_equipamento_by_id, create_equipamento, 
    processar_inventario, update_equipamento
)
from services.auth import get_current_active_user
from utils.tombo import gerar_proximo_tombo
from typing import Optional, List, Dict, Any
from enums import EstadoEquipamento

UserDict = Dict[str, Any]

router = APIRouter(prefix="/api/v1", tags=["inventario"])

@router.post("/inventario", response_model=dict)
async def receber_inventario(
    payload: InventarioRecebido,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    # ============================================================
    # 1. Dados básicos
    # ============================================================

    uuid = payload.identificacao.uuid if payload.identificacao else None

    fabricante = (
        payload.equipamento.fabricante
        if payload.equipamento
        else None
    )

    modelo = (
        payload.equipamento.modelo
        if payload.equipamento
        else None
    )

    numero_serie = (
        payload.equipamento.numeroSerie
        if payload.equipamento
        else None
    )

    # Valores "N/A" não devem ser tratados como dados reais
    if uuid == "N/A":
        uuid = None

    if numero_serie == "N/A":
        numero_serie = None

    tombo = payload.tombo.strip() if payload.tombo else None

    # ============================================================
    # 2. Procurar equipamento existente
    # ============================================================

    equip = None

    if tombo:
        equip = get_equipamento(db, tombo)

    if not equip and uuid:
        cursor = db.execute(
            """
            SELECT *
            FROM equipamento
            WHERE uuid = ?
            LIMIT 1
            """,
            (uuid,)
        )

        row = cursor.fetchone()

        if row:
            equip = dict(row)    

    # ============================================================
    # 4. Criar equipamento
    # ============================================================

    if not equip:

        novo_tombo = (
            tombo
            if tombo
            else gerar_proximo_tombo()
        )

        equip_data = EquipamentoCreate(
            tombo=novo_tombo,
            uuid=uuid,
            fabricante=fabricante,
            modelo=modelo,
            numero_serie=numero_serie,
            localizacao=payload.localizacao,
            estado=EstadoEquipamento.FUNCIONAL,
            inicio_garantia=None,
            duracao_garantia=None
        )

        equip = create_equipamento(
            db,
            equip_data,
            current_user["username"]
        )

    # ============================================================
    # 5. Atualizar equipamento existente
    # ============================================================

    else:

        update_data = {}

        if uuid and equip.get("uuid") != uuid:
            update_data["uuid"] = uuid

        if (
            fabricante
            and equip.get("fabricante_id") != fabricante
        ):
            update_data["fabricante_id"] = fabricante

        if (
            modelo
            and equip.get("modelo_id") != modelo
        ):
            update_data["modelo_id"] = modelo

        if (
            numero_serie
            and equip.get("numero_serie") != numero_serie
        ):
            update_data["numero_serie"] = numero_serie

        if (
            payload.localizacao
            and equip.get("localizacao") != payload.localizacao
        ):
            update_data["localizacao"] = payload.localizacao

        if update_data:

            equip_update = EquipamentoUpdate(
                **update_data
            )

            equip = update_equipamento(
                db,
                equip["tombo"],
                equip_update,
                current_user["username"]
            )

    # ============================================================
    # 6. Montar inventário de hardware
    # ============================================================

    inventario_data = {
        "cpu": (
            payload.processador.model_dump()
            if payload.processador
            else None
        ),

        "memoria": (
            payload.memoria.model_dump()
            if payload.memoria
            else None
        ),

        "armazenamento": [
            disco.model_dump()
            for disco in payload.discos
        ],

        "gpu": [
            video.model_dump()
            for video in payload.video
        ],

        "placa_mae": (
            payload.placaMae.model_dump()
            if payload.placaMae
            else None
        ),

        "bios": (
            payload.bios.model_dump()
            if payload.bios
            else None
        ),

        "sistema_operacional": (
            payload.sistema.model_dump()
            if payload.sistema
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
    # 8. Retornar equipamento atualizado
    # ============================================================

    if equip and equip.get("tombo"):

        equip_atualizado = get_equipamento(
            db,
            equip["tombo"]
        )

        if equip_atualizado:
            return dict(equip_atualizado)

    return dict(equip) if equip else {}

@router.get("/inventario/ultimo/{equipamento_id}")
async def obter_ultimo_inventario(
    equipamento_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Retorna o último inventário de hardware de um equipamento"""
    cursor = db.execute(
        """
        SELECT * FROM inventario_hardware
        WHERE equipamento_id = ?
        ORDER BY data_coleta DESC
        LIMIT 1
        """,
        (equipamento_id,)
    )
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum inventário encontrado para este equipamento"
        )
    
    return dict(row)


@router.get("/inventario/historico/{equipamento_id}")
async def obter_historico_inventario(
    equipamento_id: int,
    limit: int = 10,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Retorna o histórico de inventários de um equipamento"""
    cursor = db.execute(
        """
        SELECT * FROM inventario_hardware
        WHERE equipamento_id = ?
        ORDER BY data_coleta DESC
        LIMIT ?
        """,
        (equipamento_id, limit)
    )
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@router.post("/inventario/forcar/{equipamento_id}")
async def forcar_inventario(
    equipamento_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_active_user)
):
    """Força a criação de um novo registro de inventário para um equipamento"""
    # Verificar se equipamento existe
    equip = get_equipamento_by_id(db, equipamento_id)
    if not equip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipamento não encontrado"
        )
    
    # Buscar último inventário para usar como base
    cursor = db.execute(
        """
        SELECT * FROM inventario_hardware
        WHERE equipamento_id = ?
        ORDER BY data_coleta DESC
        LIMIT 1
        """,
        (equipamento_id,)
    )
    ultimo = cursor.fetchone()
    
    if not ultimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipamento não possui inventário anterior"
        )
    
    # Criar novo inventário com os mesmos dados
    inventario_data = {
        'cpu': ultimo['cpu'],
        'memoria': ultimo['memoria'],
        'armazenamento': ultimo['armazenamento'],
        'gpu': ultimo['gpu'],
        'placa_mae': ultimo['placa_mae'],
        'bios': ultimo['bios'],
        'sistema_operacional': ultimo['sistema_operacional'],
        'json_original': ultimo['json_original']
    }
    
    # Forçar criação de novo registro (muda a data_coleta)
    novo_inventario = processar_inventario(
        db, 
        equipamento_id, 
        inventario_data, 
        current_user['username']
    )
    
    return {
        "message": "Novo registro de inventário criado com sucesso",
        "inventario": dict(novo_inventario) if novo_inventario else None
    }