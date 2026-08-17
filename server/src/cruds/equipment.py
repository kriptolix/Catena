import sqlite3
from utils.to_dict import _fetch_all_as_dict
from utils.asset_tag import generate_next_asset_tag
from cruds.history import log_history
from enums import HistoryType
from schemas.equipment import EquipmentCreate, EquipmentUpdate


def get_equipment(db: sqlite3.Connection, asset_tag: str):

    cursor = db.execute(
        """
        SELECT * FROM Equipment WHERE asset_tag = ? LIMIT 1
        """,
        (asset_tag,),
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

def get_equipments(db: sqlite3.Connection, skip: int = 0, limit: int = 100, filters: dict | None = None):
    query = "SELECT e.* FROM equipment e"
    where_clauses = []
    params = []
    joins = []

    if filters:
        if 'asset_tag' in filters and filters['asset_tag']:
            where_clauses.append("e.asset_tag LIKE ?")
            params.append(f"%{filters['asset_tag']}%")

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
    # Gerar asset_tag se não fornecido
    asset_tag = Equipment.asset_tag
    if not asset_tag:
        asset_tag = generate_next_asset_tag()
    else:
        # Verificar se já existe
        if get_equipment(db, asset_tag):
            raise ValueError("asset_tag já existe")

    # Tratar valores controlados (manufacturer, model)
    manufacturer = None
    model = None
    
    manufacturer = Equipment.manufacturer    
    model = Equipment.model

    cursor = db.execute(
        """
        INSERT INTO Equipment (
            asset_tag, uuid, manufacturer, model, serial_number,
            location, status, warranty_start_date, warranty_period
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asset_tag,
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
    log_history(
        db, equip, user,
        HistoryType.CREATED, None, f"Cadastro com asset_tag {asset_tag}"
    )

    return get_equipment_by_id(db, equip)


def update_Equipment(db: sqlite3.Connection, asset_tag: str, Equipment_update: EquipmentUpdate, user: str):
    db_equip = get_equipment(db, asset_tag)
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
    params.append(asset_tag)
    query = f"""
        UPDATE Equipment 
        SET {', '.join(update_fields)}
        WHERE asset_tag = ?
    """
    db.execute(query, params)
    db.commit()

    # Registrar histórico para cada mudança relevante
    for campo, (old, new) in changes.items():
        tipo = None
        if campo == 'location':
            tipo = HistoryType.LOCATION_CHANGED
        elif campo == 'status':
            tipo = HistoryType.STATUS_CHANGED        
        
        if type:
            log_history(
                db, db_equip['id'], user,
                tipo, str(old), str(new)
            )

    return get_equipment(db, asset_tag)


def delete_Equipment(db: sqlite3.Connection, asset_tag: str, user: str):
    db_equip = get_equipment(db, asset_tag)
    if not db_equip:
        return False    

    db.execute("UPDATE equipment SET active = 0 WHERE id = ?", (asset_tag,))
    db.commit()
    return True