from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3

from database import get_db
from schemas import InventarioRecebido, EquipamentoCreate, Equipamento, EquipamentoUpdate
from crud import (
    get_equipamento, get_equipamento_by_id, create_equipamento, 
    processar_inventario, update_equipamento
)
from server.src.services.auth import get_current_active_user
from utils.tombo import gerar_proximo_tombo
from typing import Optional, List, Dict, Any

UserDict = Dict[str, Any]

router = APIRouter(prefix="/api/v1", tags=["inventario"])

@router.post("/inventario", response_model=dict)
async def receber_inventario(
    payload: InventarioRecebido,
    db: sqlite3.Connection = Depends(get_db),
    current_user: UserDict = Depends(get_current_active_user)
):
    # Verificar se equipamento já existe pelo tombo ou uuid
    equip = None
    if payload.tombo:
        equip = get_equipamento(db, payload.tombo)
    
    if not equip and payload.uuid:
        # Buscar equipamento por UUID
        cursor = db.execute(
            "SELECT * FROM equipamento WHERE uuid = ? LIMIT 1",
            (payload.uuid,)
        )
        row = cursor.fetchone()
        if row:
            equip = dict(row)

    # Se não existe, criar novo
    if not equip:
        # Gerar tombo se não fornecido
        tombo = payload.tombo if payload.tombo else gerar_proximo_tombo()
        
        # Preparar dados para criação
        equip_data = EquipamentoCreate(
            tombo=tombo,
            uuid=payload.uuid,
            fabricante=payload.fabricante,  # será tratado como string
            modelo=payload.modelo,
            numero_serie=payload.numero_serie,
            localizacao=payload.localizacao,
            estado=payload.estado,
            inicio_garantia=payload.inicio_garantia,
            duracao_garantia=payload.duracao_garantia
        )
        equip = create_equipamento(db, equip_data, current_user['username'])
    else:
        # Atualizar campos básicos se fornecidos
        update_data = {}
        
        if payload.localizacao and equip['localizacao'] != payload.localizacao:
            update_data['localizacao'] = payload.localizacao
        
        if payload.estado and equip['estado'] != payload.estado:
            update_data['estado'] = payload.estado
        
        if payload.inicio_garantia and equip['inicio_garantia'] != payload.inicio_garantia:
            update_data['inicio_garantia'] = payload.inicio_garantia
        
        if payload.duracao_garantia and equip['duracao_garantia'] != payload.duracao_garantia:
            update_data['duracao_garantia'] = payload.duracao_garantia
        
        if update_data:
            equip_update = EquipamentoUpdate(**update_data)
            equip = update_equipamento(db, equip['tombo'], equip_update, current_user['username'])

    # Processar inventário de hardware
    inventario_data = {
        'cpu': payload.cpu,
        'memoria': payload.memoria,
        'armazenamento': payload.armazenamento,
        'gpu': payload.gpu,
        'placa_mae': payload.placa_mae,
        'bios': payload.bios,
        'sistema_operacional': payload.sistema_operacional,
        'json_original': payload.json_original
    }
    
    # Obter o ID do equipamento (pode ser dict ou None)
    equip_id = equip['id'] if equip else None
    if equip_id:
        processar_inventario(db, equip_id, inventario_data, current_user['username'])

    # Buscar equipamento atualizado para retornar
    if equip and equip.get('tombo'):
        equip_atualizado = get_equipamento(db, equip['tombo'])
        if equip_atualizado:
            return dict(equip_atualizado)
    
    # Se não encontrar, retornar o que temos
    return dict(equip) if equip else None


@router.get("/inventario/ultimo/{equipamento_id}")
async def obter_ultimo_inventario(
    equipamento_id: int,
    db: sqlite3.Connection = Depends(get_db),
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
    db: sqlite3.Connection = Depends(get_db),
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
    db: sqlite3.Connection = Depends(get_db),
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