import sqlite3

from enums import (TipoHistorico,
    TipoValorControlado, EstadoEquipamento
)
from schemas import (
    EquipamentoCreate, EquipamentoUpdate, ValorControladoCreate,
    DefeitoCreate, InventarioHardwareCreate, HistoricoCreate,
    AnotacaoCreate, UsuarioCreate, UsuarioUpdate
)
from utils.tombo import gerar_proximo_tombo
from server.src.services.auth import get_password_hash
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

# --- ValorControlado ---


def get_valor_controlado_by_tipo_valor(
    db: sqlite3.Connection,
    tipo: str,
    valor: str,
):
    cursor = db.execute(
        """
        SELECT *
        FROM valor_controlado
        WHERE tipo = ? AND valor = ?
        LIMIT 1
        """,
        (tipo, valor),
    )

    return cursor.fetchone()


def create_valor_controlado(
    db: sqlite3.Connection,
    valor: ValorControladoCreate,
    admin: bool = False,
):
    cursor = db.execute(
        """
        INSERT INTO valor_controlado (tipo, valor, criado_por_admin)
        VALUES (?, ?, ?)
        """,
        (valor.tipo, valor.valor, admin),
    )

    db.commit()

    cursor = db.execute(
        "SELECT * FROM valor_controlado WHERE id = ?",
        (cursor.lastrowid,),
    )

    return cursor.fetchone()


def get_or_create_valor_controlado(db: sqlite3.Connection, tipo: TipoValorControlado, valor: str, admin: bool = False):
    existing = get_valor_controlado_by_tipo_valor(db, tipo, valor)
    if existing:
        return existing
    return create_valor_controlado(db, ValorControladoCreate(tipo=tipo, valor=valor), admin)


# --- Equipamento ---


def get_equipamento(db: sqlite3.Connection, tombo: str):
    cursor = db.execute(
        """
        SELECT * FROM equipamento WHERE tombo = ? LIMIT 1
        """,
        (tombo,),
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


def get_equipamento_by_id(db: sqlite3.Connection, id: int):
    cursor = db.execute(
        """
        SELECT * FROM equipamento WHERE id = ? LIMIT 1
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


def get_equipamentos(db: sqlite3.Connection, skip: int = 0, limit: int = 100, filters: dict = None):
    query = "SELECT e.* FROM equipamento e"
    where_clauses = []
    params = []
    joins = []

    if filters:
        if 'tombo' in filters and filters['tombo']:
            where_clauses.append("e.tombo LIKE ?")
            params.append(f"%{filters['tombo']}%")
        
        if 'fabricante' in filters and filters['fabricante']:
            joins.append("JOIN valor_controlado vc_fab ON e.fabricante_id = vc_fab.id")
            where_clauses.append("vc_fab.valor LIKE ?")
            params.append(f"%{filters['fabricante']}%")
        
        if 'modelo' in filters and filters['modelo']:
            joins.append("JOIN valor_controlado vc_mod ON e.modelo_id = vc_mod.id")
            where_clauses.append("vc_mod.valor LIKE ?")
            params.append(f"%{filters['modelo']}%")
        
        if 'localizacao' in filters and filters['localizacao']:
            where_clauses.append("e.localizacao LIKE ?")
            params.append(f"%{filters['localizacao']}%")
        
        if 'estado' in filters and filters['estado']:
            where_clauses.append("e.estado = ?")
            params.append(filters['estado'])
        
        # Garantia: SIM/NAO
        if 'garantia' in filters:
            if filters['garantia'] == 'SIM':
                where_clauses.append("e.inicio_garantia IS NOT NULL")
            elif filters['garantia'] == 'NAO':
                where_clauses.append("e.inicio_garantia IS NULL")
        
        # Defeito: equipamentos com defeitos não resolvidos
        if 'defeito' in filters and filters['defeito']:
            joins.append("JOIN defeito d ON e.id = d.equipamento_id")
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


def create_equipamento(db: sqlite3.Connection, equipamento: EquipamentoCreate, usuario: str):
    # Gerar tombo se não fornecido
    tombo = equipamento.tombo
    if not tombo:
        tombo = gerar_proximo_tombo()
    else:
        # Verificar se já existe
        if get_equipamento(db, tombo):
            raise ValueError("Tombo já existe")

    # Tratar valores controlados (fabricante, modelo)
    fabricante_id = None
    modelo_id = None
    
    if equipamento.fabricante:
        if isinstance(equipamento.fabricante, str):
            fabricante = get_or_create_valor_controlado(
                db, TipoValorControlado.FABRICANTE, equipamento.fabricante, admin=False
            )
            fabricante_id = fabricante['id']
        else:
            fabricante_id = equipamento.fabricante_id
    
    if equipamento.modelo:
        if isinstance(equipamento.modelo, str):
            modelo = get_or_create_valor_controlado(
                db, TipoValorControlado.MODELO, equipamento.modelo, admin=False
            )
            modelo_id = modelo['id']
        else:
            modelo_id = equipamento.modelo_id

    cursor = db.execute(
        """
        INSERT INTO equipamento (
            tombo, uuid, fabricante_id, modelo_id, numero_serie,
            localizacao, estado, inicio_garantia, duracao_garantia
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tombo,
            equipamento.uuid,
            fabricante_id,
            modelo_id,
            equipamento.numero_serie,
            equipamento.localizacao,
            equipamento.estado.value if equipamento.estado else None,
            equipamento.inicio_garantia,
            equipamento.duracao_garantia
        ),
    )
    db.commit()
    
    equip_id = cursor.lastrowid
    
    # Registrar histórico de cadastro
    registrar_historico(
        db, equip_id, usuario,
        TipoHistorico.CADASTRO, None, f"Cadastro com tombo {tombo}"
    )

    return get_equipamento_by_id(db, equip_id)


def update_equipamento(db: sqlite3.Connection, tombo: str, equipamento_update: EquipamentoUpdate, usuario: str):
    db_equip = get_equipamento(db, tombo)
    if not db_equip:
        return None

    # Construir query de update dinâmica
    update_fields = []
    params = []
    changes = {}

    if equipamento_update.uuid is not None and db_equip['uuid'] != equipamento_update.uuid:
        changes['uuid'] = (db_equip['uuid'], equipamento_update.uuid)
        update_fields.append("uuid = ?")
        params.append(equipamento_update.uuid)
    
    if equipamento_update.fabricante_id is not None and db_equip['fabricante_id'] != equipamento_update.fabricante_id:
        # Buscar nome do fabricante para histórico
        cursor = db.execute(
            "SELECT valor FROM valor_controlado WHERE id = ?",
            (db_equip['fabricante_id'],)
        )
        old_fab = cursor.fetchone()
        cursor = db.execute(
            "SELECT valor FROM valor_controlado WHERE id = ?",
            (equipamento_update.fabricante_id,)
        )
        new_fab = cursor.fetchone()
        changes['fabricante'] = (
            old_fab['valor'] if old_fab else None,
            new_fab['valor'] if new_fab else None
        )
        update_fields.append("fabricante_id = ?")
        params.append(equipamento_update.fabricante_id)
    
    if equipamento_update.modelo_id is not None and db_equip['modelo_id'] != equipamento_update.modelo_id:
        cursor = db.execute(
            "SELECT valor FROM valor_controlado WHERE id = ?",
            (db_equip['modelo_id'],)
        )
        old_mod = cursor.fetchone()
        cursor = db.execute(
            "SELECT valor FROM valor_controlado WHERE id = ?",
            (equipamento_update.modelo_id,)
        )
        new_mod = cursor.fetchone()
        changes['modelo'] = (
            old_mod['valor'] if old_mod else None,
            new_mod['valor'] if new_mod else None
        )
        update_fields.append("modelo_id = ?")
        params.append(equipamento_update.modelo_id)
    
    if equipamento_update.numero_serie is not None and db_equip['numero_serie'] != equipamento_update.numero_serie:
        changes['numero_serie'] = (db_equip['numero_serie'], equipamento_update.numero_serie)
        update_fields.append("numero_serie = ?")
        params.append(equipamento_update.numero_serie)
    
    if equipamento_update.localizacao is not None and db_equip['localizacao'] != equipamento_update.localizacao:
        changes['localizacao'] = (db_equip['localizacao'], equipamento_update.localizacao)
        update_fields.append("localizacao = ?")
        params.append(equipamento_update.localizacao)
    
    if equipamento_update.estado is not None and db_equip['estado'] != equipamento_update.estado.value:
        changes['estado'] = (db_equip['estado'], equipamento_update.estado.value)
        update_fields.append("estado = ?")
        params.append(equipamento_update.estado.value)
    
    if equipamento_update.inicio_garantia is not None and db_equip['inicio_garantia'] != equipamento_update.inicio_garantia:
        changes['inicio_garantia'] = (db_equip['inicio_garantia'], equipamento_update.inicio_garantia)
        update_fields.append("inicio_garantia = ?")
        params.append(equipamento_update.inicio_garantia)
    
    if equipamento_update.duracao_garantia is not None and db_equip['duracao_garantia'] != equipamento_update.duracao_garantia:
        changes['duracao_garantia'] = (db_equip['duracao_garantia'], equipamento_update.duracao_garantia)
        update_fields.append("duracao_garantia = ?")
        params.append(equipamento_update.duracao_garantia)

    # Se não houve mudanças, retornar o equipamento atual
    if not update_fields:
        return db_equip

    # Executar update
    params.append(tombo)
    query = f"""
        UPDATE equipamento 
        SET {', '.join(update_fields)}
        WHERE tombo = ?
    """
    db.execute(query, params)
    db.commit()

    # Registrar histórico para cada mudança relevante
    for campo, (old, new) in changes.items():
        tipo = None
        if campo == 'localizacao':
            tipo = TipoHistorico.MUDANCA_LOCALIZACAO
        elif campo == 'estado':
            tipo = TipoHistorico.MUDANCA_ESTADO
        elif campo in ['inicio_garantia', 'duracao_garantia']:
            tipo = TipoHistorico.ALTERACAO_GARANTIA
        elif campo in ['uuid', 'fabricante', 'modelo', 'numero_serie']:
            tipo = TipoHistorico.ALTERACAO_PATRIMONIAL
        if tipo:
            registrar_historico(
                db, db_equip['id'], usuario,
                tipo, str(old), str(new)
            )

    return get_equipamento(db, tombo)


def delete_equipamento(db: sqlite3.Connection, tombo: str, usuario: str):
    db_equip = get_equipamento(db, tombo)
    if not db_equip:
        return False
    
    # Registrar auditoria
    registrar_auditoria(
        db, usuario, "exclusao_equipamento",
        f"Tombo {tombo}", "Equipamento excluído"
    )
    
    db.execute("DELETE FROM equipamento WHERE tombo = ?", (tombo,))
    db.commit()
    return True


# --- Historico ---


def registrar_historico(
    db: sqlite3.Connection,
    equipamento_id: int,
    usuario: str,
    tipo: TipoHistorico,
    valor_anterior: Optional[str],
    valor_novo: Optional[str]
):
    db.execute(
        """
        INSERT INTO historico (
            equipamento_id, usuario, tipo,
            valor_anterior, valor_novo, data_hora
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (equipamento_id, usuario, tipo.value, valor_anterior, valor_novo, datetime.now())
    )
    db.commit()


# --- Defeitos ---


def create_defeito(db: sqlite3.Connection, defeito: DefeitoCreate, usuario: str):
    cursor = db.execute(
        """
        INSERT INTO defeito (
            equipamento_id, componente, descricao, resolvido
        ) VALUES (?, ?, ?, ?)
        """,
        (defeito.equipamento_id, defeito.componente, defeito.descricao, defeito.resolvido or 0)
    )
    db.commit()
    
    defeito_id = cursor.lastrowid
    
    # Registrar histórico
    equip = get_equipamento_by_id(db, defeito.equipamento_id)
    if equip:
        registrar_historico(
            db, equip['id'], usuario,
            TipoHistorico.MUDANCA_ESTADO,
            equip['estado'], "defeito_registrado"
        )
    
    cursor = db.execute(
        "SELECT * FROM defeito WHERE id = ?",
        (defeito_id,)
    )
    return _row_to_dict(cursor.fetchone())


def resolver_defeito(db: sqlite3.Connection, defeito_id: int, usuario: str):
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
    equip = get_equipamento_by_id(db, db_defeito['equipamento_id'])
    if equip:
        registrar_historico(
            db, equip['id'], usuario,
            TipoHistorico.MUDANCA_ESTADO,
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
    equipamento_id: int,
    inventario_data: dict,
    usuario: str
):
    """
    Recebe dados de inventário e cria um novo registro apenas se houve mudança no hardware.
    Caso contrário, atualiza a data_coleta do último.
    """
    # Buscar último inventário
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

    # Definir campos a comparar
    campos = ['cpu', 'memoria', 'armazenamento', 'gpu',
              'placa_mae', 'bios', 'sistema_operacional']
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
                equipamento_id, cpu, memoria, armazenamento, gpu,
                placa_mae, bios, sistema_operacional, json_original, data_coleta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipamento_id,
                inventario_data.get('cpu'),
                inventario_data.get('memoria'),
                inventario_data.get('armazenamento'),
                inventario_data.get('gpu'),
                inventario_data.get('placa_mae'),
                inventario_data.get('bios'),
                inventario_data.get('sistema_operacional'),
                inventario_data.get('json_original'),
                datetime.now()
            )
        )
        db.commit()
        novo_id = cursor.lastrowid
        
        # Registrar histórico de alteração de hardware
        registrar_historico(
            db, equipamento_id, usuario,
            TipoHistorico.ALTERACAO_HARDWARE,
            "Inventário anterior", "Novo inventário"
        )
        
        cursor = db.execute(
            "SELECT * FROM inventario_hardware WHERE id = ?",
            (novo_id,)
        )
        return _row_to_dict(cursor.fetchone())
    else:
        # Atualizar data_coleta do último
        db.execute(
            """
            UPDATE inventario_hardware
            SET data_coleta = ?
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


def create_anotacao(db: sqlite3.Connection, anotacao: AnotacaoCreate):
    cursor = db.execute(
        """
        INSERT INTO anotacao (
            equipamento_id, usuario, texto, data_hora
        ) VALUES (?, ?, ?, ?)
        """,
        (anotacao.equipamento_id, anotacao.usuario, anotacao.texto, datetime.now())
    )
    db.commit()
    
    cursor = db.execute(
        "SELECT * FROM anotacao WHERE id = ?",
        (cursor.lastrowid,)
    )
    return _row_to_dict(cursor.fetchone())


# --- Usuario ---


def get_usuario_by_username(db: sqlite3.Connection, username: str):
    cursor = db.execute(
        "SELECT * FROM usuario WHERE username = ? LIMIT 1",
        (username,)
    )
    return _row_to_dict(cursor.fetchone())


def create_usuario(db: sqlite3.Connection, usuario: UsuarioCreate):
    hashed = get_password_hash(usuario.password)
    cursor = db.execute(
        """
        INSERT INTO usuario (
            username, hashed_password, is_admin, ativo
        ) VALUES (?, ?, ?, ?)
        """,
        (usuario.username, hashed, usuario.is_admin or 0, 1)
    )
    db.commit()
    
    cursor = db.execute(
        "SELECT * FROM usuario WHERE id = ?",
        (cursor.lastrowid,)
    )
    return _row_to_dict(cursor.fetchone())


def update_usuario(db: sqlite3.Connection, username: str, usuario_update: UsuarioUpdate):
    db_user = get_usuario_by_username(db, username)
    if not db_user:
        return None
    
    update_fields = []
    params = []
    
    if usuario_update.password:
        update_fields.append("hashed_password = ?")
        params.append(get_password_hash(usuario_update.password))
    
    if usuario_update.is_admin is not None:
        update_fields.append("is_admin = ?")
        params.append(1 if usuario_update.is_admin else 0)
    
    if usuario_update.ativo is not None:
        update_fields.append("ativo = ?")
        params.append(1 if usuario_update.ativo else 0)
    
    if update_fields:
        params.append(username)
        query = f"""
            UPDATE usuario
            SET {', '.join(update_fields)}
            WHERE username = ?
        """
        db.execute(query, params)
        db.commit()
    
    return get_usuario_by_username(db, username)


# --- Auditoria ---


def registrar_auditoria(
    db: sqlite3.Connection,
    usuario: str,
    operacao: str,
    objeto_alterado: str,
    detalhes: str | None
):
    db.execute(
        """
        INSERT INTO auditoria (
            usuario, operacao, objeto_alterado,
            antes, depois, data_hora
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (usuario, operacao, objeto_alterado, detalhes, detalhes, datetime.now())
    )
    db.commit()