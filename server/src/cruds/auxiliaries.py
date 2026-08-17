import sqlite3
from datetime import datetime

from schemas.accessories import AnnotationCreate, DefectCreate
from equipment import get_equipment_by_id
from history import log_history
from utils.to_dict import _row_to_dict
from enums import HistoryType

def create_annotation(db: sqlite3.Connection, annotation: AnnotationCreate):
    cursor = db.execute(
        """
        INSERT INTO annotation (
            equipment_id, user, texto, data_hora
        ) VALUES (?, ?, ?, ?)
        """,
        (annotation.equipment_id, annotation.user, annotation.text, datetime.now())
    )
    db.commit()

    cursor = db.execute(
        "SELECT * FROM annotation WHERE id = ?",
        (cursor.lastrowid,)
    )
    return _row_to_dict(cursor.fetchone())

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
        log_history(
            db, equip['id'], user,
            HistoryType.STATUS_CHANGED,
            equip['status'], "defeito_registrado"
        )

    cursor = db.execute(
        "SELECT * FROM defeito WHERE id = ?",
        (defeito_id,)
    )
    return _row_to_dict(cursor.fetchone())