import sqlite3
import json
from datetime import datetime
from utils.to_dict import _row_to_dict
from cruds.history import log_history
from enums import HistoryType

def processar_inventario(
    db: sqlite3.Connection,
    equipment_id: int,
    inventory_data: dict,
    user: str
):
    """
    Recebe dados de inventário e cria um novo registro apenas se houve mudança no hardware.
    Caso contrário, atualiza a collection_date do último.
    """
    # Buscar último inventário
    cursor = db.execute(
        """
        SELECT * FROM inventory
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
            new_val = inventory_data.get(campo)
            if old_val != new_val:
                mudou = True
                break
    else:
        mudou = True  # não existe inventário anterior

    if mudou:
        # Criar novo registro
        cursor = db.execute(
            """
            INSERT INTO inventory (
                equipment_id, cpu, memoria, armazenamento, gpu,
                motherboard, bios, system, json_original, collection_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipment_id,
                json.dumps(inventory_data.get("cpu"), ensure_ascii=False),
                json.dumps(inventory_data.get("memoria"), ensure_ascii=False),
                json.dumps(inventory_data.get(
                    "armazenamento"), ensure_ascii=False),
                json.dumps(inventory_data.get("gpu"), ensure_ascii=False),
                json.dumps(inventory_data.get(
                    "motherboard"), ensure_ascii=False),
                json.dumps(inventory_data.get("bios"), ensure_ascii=False),
                json.dumps(inventory_data.get(
                    "system"), ensure_ascii=False),
                json.dumps(inventory_data.get(
                    "json_original"), ensure_ascii=False),
                datetime.now()
            )
        )
        db.commit()
        novo_id = cursor.lastrowid

        # Registrar histórico de alteração de hardware
        log_history(
            db, equipment_id, user,
            HistoryType.COMPONENT_CHANGED,
            "Inventário anterior", "Novo inventário"
        )

        cursor = db.execute(
            "SELECT * FROM inventory WHERE id = ?",
            (novo_id,)
        )
        return _row_to_dict(cursor.fetchone())
    else:
        # Atualizar collection_date do último
        db.execute(
            """
            UPDATE inventory
            SET collection_date = ?
            WHERE id = ?
            """,
            (datetime.now(), ultimo['id'])
        )
        db.commit()

        cursor = db.execute(
            "SELECT * FROM inventory WHERE id = ?",
            (ultimo['id'],)
        )
        return _row_to_dict(cursor.fetchone())