import sqlite3
from typing import Optional
from enums import HistoryType, AuditAction

def log_history(
    db: sqlite3.Connection,
    equipment_id: int,
    user: str,
    type: HistoryType,
    field: Optional[str] = None,
    previous_value: Optional[str] = None,
    next_value: Optional[str] = None,
):
    db.execute(
        """
        INSERT INTO history (
            equipment_id,
            user,
            type,
            field,
            previous_value,
            next_value
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            equipment_id,
            user,
            type.value,
            field,
            previous_value,
            next_value,
        )
    )
    db.commit()


def log_audit( db: sqlite3.Connection, 
              user: str, 
              action: AuditAction, 
              entity_type: Optional[str] = None, 
              entity_id: Optional[int] = None, 
              previous_value: Optional[str] = None, 
              next_value: Optional[str] = None, ): 

    db.execute( """ 
    INSERT INTO audit_log ( 
        user, 
        action, 
        entity_type, 
        entity_id, 
        previous_value, 
        next_value ) 
        VALUES (?, ?, ?, ?, ?, ?) """, 
        ( user, action.value, entity_type, entity_id, previous_value, next_value, ) 
    ) 

    db.commit()