import sqlite3
import json

from enums import (TipoHistorico,
                   TipoValorControlado, StatusEquipment
                   )
from schemas.equipment import EquipmentCreate, EquipmentUpdate
from schemas.accessories import DefectCreate, AnnotationCreate
from schemas.user import userCreate, userUpdate

from server.src.utils.asset_tag import gerar_proximo_tombo
from services.auth import get_password_hash
from datetime import datetime
from typing import Optional, List, Dict, Any
import json


# --- Equipment ---


def get_equipment(db: sqlite3.Connection, asset_number: str):

    cursor = db.execute(
        """
        SELECT * FROM Equipment WHERE asset_number = ? LIMIT 1
        """,
        (asset_number,),
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


def get_equipment_by_id(db: sqlite3.Connection, id: int):
    cursor = db.execute(
        """
        SELECT * FROM Equipment WHERE id = ? LIMIT 1
        """,
        (id,),
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


def _row_to_dict(row):
    """Converte uma linha SQLite para dicionário com nomes de colunas"""
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def _fetch_all_as_dict(cursor):
    """Converte todas as linhas do cursor para lista de dicionários"""
    rows = cursor.fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]


def get_equipments(db: sqlite3.Connection, skip: int = 0, limit: int = 100, filters: dict | None = None):
    query = "SELECT e.* FROM equipment e"
    where_clauses = []
    params = []
    joins = []

    if filters:
        if 'asset_number' in filters and filters['asset_number']:
            where_clauses.append("e.asset_number LIKE ?")
            params.append(f"%{filters['asset_number']}%")

        if 'manufacturer' in filters and filters['manufacturer']:
            joins.append(
                "JOIN valor_controlado vc_fab ON e.manufacturer = vc_fab.id")
            where_clauses.append("vc_fab.valor LIKE ?")
            params.append(f"%{filters['manufacturer']}%")

        if 'model' in filters and filters['model']:
            joins.append(
                "JOIN valor_controlado vc_mod ON e.model = vc_mod.id")
            where_clauses.append("vc_mod.valor LIKE ?")
            params.append(f"%{filters['model']}%")

        if 'location' in filters and filters['location']:
            where_clauses.append("e.location LIKE ?")
            params.append(f"%{filters['location']}%")

        if 'status' in filters and filters['status']:
            where_clauses.append("e.status = ?")
            params.append(filters['status'])

        # Garantia: SIM/NAO
        if 'garantia' in filters:
            if filters['garantia'] == 'SIM':
                where_clauses.append("e.warranty_start_date IS NOT NULL")
            elif filters['garantia'] == 'NAO':
                where_clauses.append("e.warranty_start_date IS NULL")

        # Defeito: Equipments com defeitos não resolvidos
        if 'defeito' in filters and filters['defeito']:
            joins.append("JOIN defeito d ON e.id = d.equipment_id")
            where_clauses.append("d.resolvido = 0")

    # Montar query completa
    full_query = query
    if joins:
        full_query += " " + " ".join(joins)
    if where_clauses:
        full_query += " WHERE " + " AND ".join(where_clauses)

    full_query += " ORDER BY e.id LIMIT ? OFFSET ?"
    params.extend([limit, skip])

    cursor = db.execute(full_query, params)
    return _fetch_all_as_dict(cursor)


def create_Equipment(db: sqlite3.Connection, Equipment: EquipmentCreate, user: str):
    # Gerar asset_number se não fornecido
    asset_number = Equipment.asset_number
    if not asset_number:
        asset_number = gerar_proximo_tombo()
    else:
        # Verificar se já existe
        if get_equipment(db, asset_number):
            raise ValueError("asset_number já existe")

    # Tratar valores controlados (manufacturer, model)
    manufacturer = None
    model = None
    
    manufacturer = Equipment.manufacturer    
    model = Equipment.model

    cursor = db.execute(
        """
        INSERT INTO Equipment (
            asset_number, uuid, manufacturer, model, serial_number,
            location, status, warranty_start_date, warranty_period
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asset_number,
            Equipment.uuid,
            manufacturer,
            model,
            Equipment.serial_number,
            Equipment.location,
            Equipment.status.value if Equipment.status else None,
            Equipment.warranty_start_date,
            Equipment.warranty_period
        ),
    )
    db.commit()

    equip = cursor.lastrowid

    # Registrar histórico de cadastro
    registrar_historico(
        db, equip, user,
        TipoHistorico.CADASTRO, None, f"Cadastro com asset_number {asset_number}"
    )

    return get_equipment_by_id(db, equip)


def update_Equipment(db: sqlite3.Connection, asset_number: str, Equipment_update: EquipmentUpdate, user: str):
    db_equip = get_equipment(db, asset_number)
    if not db_equip:
        return None

    # Construir query de update dinâmica
    update_fields = []
    params = []
    changes = {}

    if Equipment_update.uuid is not None and db_equip['uuid'] != Equipment_update.uuid:
        changes['uuid'] = (db_equip['uuid'], Equipment_update.uuid)
        update_fields.append("uuid = ?")
        params.append(Equipment_update.uuid)

    if Equipment_update.manufacturer is not None and db_equip['manufacturer'] != Equipment_update.manufacturer:
        # Buscar nome do manufacturer para histórico
        cursor = db.execute(
            "SELECT valor FROM valor_controlado WHERE id = ?",
            (db_equip['manufacturer'],)
        )
        old_fab = cursor.fetchone()
        cursor = db.execute(
            "SELECT valor FROM valor_controlado WHERE id = ?",
            (Equipment_update.manufacturer,)
        )
        new_fab = cursor.fetchone()
        changes['manufacturer'] = (
            old_fab['valor'] if old_fab else None,
            new_fab['valor'] if new_fab else None
        )
        update_fields.append("manufacturer = ?")
        params.append(Equipment_update.manufacturer)

    if Equipment_update.model is not None and db_equip['model'] != Equipment_update.model:
        cursor = db.execute(
            "SELECT valor FROM valor_controlado WHERE id = ?",
            (db_equip['model'],)
        )
        old_mod = cursor.fetchone()
        cursor = db.execute(
            "SELECT valor FROM valor_controlado WHERE id = ?",
            (Equipment_update.model,)
        )
        new_mod = cursor.fetchone()
        changes['model'] = (
            old_mod['valor'] if old_mod else None,
            new_mod['valor'] if new_mod else None
        )
        update_fields.append("model = ?")
        params.append(Equipment_update.model)

    if Equipment_update.serial_number is not None and db_equip['serial_number'] != Equipment_update.serial_number:
        changes['serial_number'] = (
            db_equip['serial_number'], Equipment_update.serial_number)
        update_fields.append("serial_number = ?")
        params.append(Equipment_update.serial_number)

    if Equipment_update.location is not None and db_equip['location'] != Equipment_update.location:
        changes['location'] = (
            db_equip['location'], Equipment_update.location)
        update_fields.append("location = ?")
        params.append(Equipment_update.location)

    if Equipment_update.status is not None and db_equip['status'] != Equipment_update.status.value:
        changes['status'] = (db_equip['status'],
                             Equipment_update.status.value)
        update_fields.append("status = ?")
        params.append(Equipment_update.status.value)

    if Equipment_update.warranty_start_date is not None and db_equip['warranty_start_date'] != Equipment_update.warranty_start_date:
        changes['warranty_start_date'] = (
            db_equip['warranty_start_date'], Equipment_update.warranty_start_date)
        update_fields.append("warranty_start_date = ?")
        params.append(Equipment_update.warranty_start_date)

    if Equipment_update.warranty_period is not None and db_equip['warranty_period'] != Equipment_update.warranty_period:
        changes['warranty_period'] = (
            db_equip['warranty_period'], Equipment_update.warranty_period)
        update_fields.append("warranty_period = ?")
        params.append(Equipment_update.warranty_period)

    # Se não houve mudanças, retornar o Equipment atual
    if not update_fields:
        return db_equip

    # Executar update
    params.append(asset_number)
    query = f"""
        UPDATE Equipment 
        SET {', '.join(update_fields)}
        WHERE asset_number = ?
    """
    db.execute(query, params)
    db.commit()

    # Registrar histórico para cada mudança relevante
    for campo, (old, new) in changes.items():
        tipo = None
        if campo == 'location':
            tipo = TipoHistorico.MODIFICATION_location
        elif campo == 'status':
            tipo = TipoHistorico.MODIFICATION_status        
        
        if type:
            registrar_historico(
                db, db_equip['id'], user,
                tipo, str(old), str(new)
            )

    return get_equipment(db, asset_number)


def delete_Equipment(db: sqlite3.Connection, asset_number: str, user: str):
    db_equip = get_equipment(db, asset_number)
    if not db_equip:
        return False

    # Registrar auditoria
    registrar_auditoria(
        db, user, "exclusao_Equipment",
        f"asset_number {asset_number}", "Equipment excluído"
    )

    db.execute("DELETE FROM Equipment WHERE asset_number = ?", (asset_number,))
    db.commit()
    return True


# --- Historico ---


def registrar_historico(
    db: sqlite3.Connection,
    equipment_id: int,
    user: str,
    type: TipoHistorico,
    previous_value: Optional[str],
    next_value: Optional[str]
):
    db.execute(
        """
        INSERT INTO historico (
            equipment_id, user, tipo,
            previous_value, next_value, data_hora
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (equipment_id, user, type.value,
         previous_value, next_value, datetime.now())
    )
    db.commit()


# --- Defeitos ---


def create_defeito(db: sqlite3.Connection, defeito: DefectCreate, user: str):
    cursor = db.execute(
        """
        INSERT INTO defeito (
            equipment_id, componente, descricao, resolvido
        ) VALUES (?, ?, ?, ?)
        """,
        (defeito.equipment_id, defeito.componente,
         defeito.descricao, defeito.resolvido or 0)
    )
    db.commit()

    defeito_id = cursor.lastrowid

    # Registrar histórico
    equip = get_equipment_by_id(db, defeito.equipment_id)
    if equip:
        registrar_historico(
            db, equip['id'], user,
            TipoHistorico.MODIFICATION_status,
            equip['status'], "defeito_registrado"
        )

    cursor = db.execute(
        "SELECT * FROM defeito WHERE id = ?",
        (defeito_id,)
    )
    return _row_to_dict(cursor.fetchone())


def resolver_defeito(db: sqlite3.Connection, defeito_id: int, user: str):
    cursor = db.execute(
        "SELECT * FROM defeito WHERE id = ? LIMIT 1",
        (defeito_id,)
    )
    db_defeito = cursor.fetchone()

    if not db_defeito:
        return None

    db.execute(
        "UPDATE defeito SET resolvido = 1 WHERE id = ?",
        (defeito_id,)
    )
    db.commit()

    # Registrar histórico
    equip = get_equipment_by_id(db, db_defeito['equipment_id'])
    if equip:
        registrar_historico(
            db, equip['id'], user,
            TipoHistorico.MODIFICATION_status,
            "defeituoso", "defeito_resolvido"
        )

    cursor = db.execute(
        "SELECT * FROM defeito WHERE id = ?",
        (defeito_id,)
    )
    return _row_to_dict(cursor.fetchone())


# --- InventarioHardware ---


def processar_inventario(
    db: sqlite3.Connection,
    equipment_id: int,
    inventario_date: dict,
    user: str
):
    """
    Recebe dados de inventário e cria um novo registro apenas se houve mudança no hardware.
    Caso contrário, atualiza a collection_date do último.
    """
    # Buscar último inventário
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

    # Definir campos a comparar
    campos = ['cpu', 'memoria', 'armazenamento', 'gpu',
              'motherboard', 'bios', 'system']
    mudou = False

    if ultimo:
        for campo in campos:
            old_val = ultimo[campo]
            new_val = inventario_data.get(campo)
            if old_val != new_val:
                mudou = True
                break
    else:
        mudou = True  # não existe inventário anterior

    if mudou:
        # Criar novo registro
        cursor = db.execute(
            """
            INSERT INTO inventario_hardware (
                equipment_id, cpu, memoria, armazenamento, gpu,
                motherboard, bios, system, json_original, collection_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipment_id,
                json.dumps(inventario_data.get("cpu"), ensure_ascii=False),
                json.dumps(inventario_data.get("memoria"), ensure_ascii=False),
                json.dumps(inventario_data.get(
                    "armazenamento"), ensure_ascii=False),
                json.dumps(inventario_data.get("gpu"), ensure_ascii=False),
                json.dumps(inventario_data.get(
                    "motherboard"), ensure_ascii=False),
                json.dumps(inventario_data.get("bios"), ensure_ascii=False),
                json.dumps(inventario_data.get(
                    "system"), ensure_ascii=False),
                json.dumps(inventario_data.get(
                    "json_original"), ensure_ascii=False),
                datetime.now()
            )
        )
        db.commit()
        novo_id = cursor.lastrowid

        # Registrar histórico de alteração de hardware
        registrar_historico(
            db, equipment_id, user,
            TipoHistorico.ALTERACAO_HARDWARE,
            "Inventário anterior", "Novo inventário"
        )

        cursor = db.execute(
            "SELECT * FROM inventario_hardware WHERE id = ?",
            (novo_id,)
        )
        return _row_to_dict(cursor.fetchone())
    else:
        # Atualizar collection_date do último
        db.execute(
            """
            UPDATE inventario_hardware
            SET collection_date = ?
            WHERE id = ?
            """,
            (datetime.now(), ultimo['id'])
        )
        db.commit()

        cursor = db.execute(
            "SELECT * FROM inventario_hardware WHERE id = ?",
            (ultimo['id'],)
        )
        return _row_to_dict(cursor.fetchone())


# --- Anotacoes ---


def create_annotation(db: sqlite3.Connection, annotation: AnnotationCreate):
    cursor = db.execute(
        """
        INSERT INTO annotation (
            equipment_id, user, texto, data_hora
        ) VALUES (?, ?, ?, ?)
        """,
        (annotation.equipment_id, annotation.user, annotation.texto, datetime.now())
    )
    db.commit()

    cursor = db.execute(
        "SELECT * FROM annotation WHERE id = ?",
        (cursor.lastrowid,)
    )
    return _row_to_dict(cursor.fetchone())


# --- user ---


def get_user_by_username(db: sqlite3.Connection, username: str):
    cursor = db.execute(
        "SELECT * FROM user WHERE username = ? LIMIT 1",
        (username,)
    )
    return _row_to_dict(cursor.fetchone())


def create_user(db: sqlite3.Connection, user: userCreate):
    hashed = get_password_hash(user.password)
    cursor = db.execute(
        """
        INSERT INTO user (
            username, hashed_password, is_admin, ativo
        ) VALUES (?, ?, ?, ?)
        """,
        (user.username, hashed, user.is_admin or 0, 1)
    )
    db.commit()

    cursor = db.execute(
        "SELECT * FROM user WHERE id = ?",
        (cursor.lastrowid,)
    )
    return _row_to_dict(cursor.fetchone())


def update_user(db: sqlite3.Connection, username: str, user_update: userUpdate):
    db_user = get_user_by_username(db, username)
    if not db_user:
        return None

    update_fields = []
    params = []

    if user_update.password:
        update_fields.append("hashed_password = ?")
        params.append(get_password_hash(user_update.password))

    if user_update.is_admin is not None:
        update_fields.append("is_admin = ?")
        params.append(1 if user_update.is_admin else 0)

    if user_update.ativo is not None:
        update_fields.append("ativo = ?")
        params.append(1 if user_update.ativo else 0)

    if update_fields:
        params.append(username)
        query = f"""
            UPDATE user
            SET {', '.join(update_fields)}
            WHERE username = ?
        """
        db.execute(query, params)
        db.commit()

    return get_user_by_username(db, username)


# --- Auditoria ---


def registrar_auditoria(
    db: sqlite3.Connection,
    user: str,
    operacao: str,
    objeto_alterado: str,
    detalhes: str | None
):
    db.execute(
        """
        INSERT INTO auditoria (
            user, operacao, objeto_alterado,
            antes, depois, data_hora
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user, operacao, objeto_alterado, detalhes, detalhes, datetime.now())
    )
    db.commit()
