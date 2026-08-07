import sqlite3
from typing import Dict, Any
from enums import TipoValorControlado
from schemas import ValorControladoCreate
from crud import get_valor_controlado_by_tipo_valor, create_valor_controlado, registrar_auditoria


def normalizar_valor(
    db: sqlite3.Connection, 
    tipo: TipoValorControlado, 
    valor_antigo: str, 
    valor_novo: str, 
    usuario: str
) -> int:
    """
    Substitui todas as ocorrências de valor_antigo pelo valor_novo para um determinado tipo.
    Retorna o número de equipamentos afetados.
    
    Args:
        db: Conexão com o banco de dados
        tipo: Tipo do valor controlado (fabricante, modelo, etc.)
        valor_antigo: Valor antigo a ser substituído
        valor_novo: Novo valor que substituirá o antigo
        usuario: Nome do usuário que está realizando a operação
    
    Returns:
        Número de equipamentos afetados
    """
    # Buscar ou criar o novo valor controlado
    novo_valor_obj = get_valor_controlado_by_tipo_valor(db, tipo, valor_novo)
    if not novo_valor_obj:
        novo_valor_obj = create_valor_controlado(
            db, 
            ValorControladoCreate(tipo=tipo, valor=valor_novo), 
            admin=True
        )

    # Buscar o valor antigo
    antigo_valor_obj = get_valor_controlado_by_tipo_valor(db, tipo, valor_antigo)
    if not antigo_valor_obj:
        return 0  # nada a fazer

    equipamentos_afetados = []
    
    # Atualizar equipamentos que usam o valor antigo
    if tipo == TipoValorControlado.FABRICANTE:
        # Buscar equipamentos com o fabricante antigo
        cursor = db.execute(
            """
            SELECT id, tombo FROM equipamento 
            WHERE fabricante_id = ?
            """,
            (antigo_valor_obj['id'],)
        )
        equipamentos = cursor.fetchall()
        
        # Atualizar cada equipamento
        for eq in equipamentos:
            db.execute(
                """
                UPDATE equipamento 
                SET fabricante_id = ? 
                WHERE id = ?
                """,
                (novo_valor_obj['id'], eq['id'])
            )
            equipamentos_afetados.append(eq['tombo'])
            
    elif tipo == TipoValorControlado.MODELO:
        # Buscar equipamentos com o modelo antigo
        cursor = db.execute(
            """
            SELECT id, tombo FROM equipamento 
            WHERE modelo_id = ?
            """,
            (antigo_valor_obj['id'],)
        )
        equipamentos = cursor.fetchall()
        
        # Atualizar cada equipamento
        for eq in equipamentos:
            db.execute(
                """
                UPDATE equipamento 
                SET modelo_id = ? 
                WHERE id = ?
                """,
                (novo_valor_obj['id'], eq['id'])
            )
            equipamentos_afetados.append(eq['tombo'])
            
    elif tipo == TipoValorControlado.TIPO_MEMORIA:
        # Para memória, atualizar nos inventários (campo memoria)
        cursor = db.execute(
            """
            SELECT id, equipamento_id FROM inventario_hardware 
            WHERE memoria LIKE ?
            """,
            (f"%{valor_antigo}%",)
        )
        inventarios = cursor.fetchall()
        
        for inv in inventarios:
            # Buscar o inventário atual
            cursor_inv = db.execute(
                "SELECT memoria FROM inventario_hardware WHERE id = ?",
                (inv['id'],)
            )
            row = cursor_inv.fetchone()
            if row:
                memoria_atual = row['memoria']
                # Substituir o valor antigo pelo novo
                nova_memoria = memoria_atual.replace(valor_antigo, valor_novo)
                db.execute(
                    """
                    UPDATE inventario_hardware 
                    SET memoria = ? 
                    WHERE id = ?
                    """,
                    (nova_memoria, inv['id'])
                )
                equipamentos_afetados.append(f"inventario_{inv['id']}")
                
    elif tipo == TipoValorControlado.FABRICANTE_DISCO:
        # Para fabricante de disco, atualizar nos inventários (campo armazenamento)
        cursor = db.execute(
            """
            SELECT id, equipamento_id FROM inventario_hardware 
            WHERE armazenamento LIKE ?
            """,
            (f"%{valor_antigo}%",)
        )
        inventarios = cursor.fetchall()
        
        for inv in inventarios:
            # Buscar o inventário atual
            cursor_inv = db.execute(
                "SELECT armazenamento FROM inventario_hardware WHERE id = ?",
                (inv['id'],)
            )
            row = cursor_inv.fetchone()
            if row:
                armazenamento_atual = row['armazenamento']
                # Substituir o valor antigo pelo novo
                novo_armazenamento = armazenamento_atual.replace(valor_antigo, valor_novo)
                db.execute(
                    """
                    UPDATE inventario_hardware 
                    SET armazenamento = ? 
                    WHERE id = ?
                    """,
                    (novo_armazenamento, inv['id'])
                )
                equipamentos_afetados.append(f"inventario_{inv['id']}")
    else:
        # Outros tipos não são diretamente referenciados em equipamentos
        # Registrar que o tipo não é suportado para normalização automática
        registrar_auditoria(
            db, 
            usuario, 
            "normalizacao_nao_suportada",
            f"tipo={tipo}, antigo={valor_antigo}, novo={valor_novo}",
            "Tipo não suportado para normalização automática"
        )
        return 0

    # Commit das alterações
    db.commit()
    
    # Registrar auditoria
    registrar_auditoria(
        db, 
        usuario, 
        "normalizacao", 
        f"tipo={tipo}, antigo={valor_antigo}, novo={valor_novo}", 
        f"Afetou {len(equipamentos_afetados)} equipamentos: {', '.join(equipamentos_afetados[:10])}"
    )
    
    return len(equipamentos_afetados)


def normalizar_valor_batch(
    db: sqlite3.Connection,
    normalizacoes: list[dict],
    usuario: str
) -> dict:
    """
    Executa múltiplas normalizações em lote.
    
    Args:
        db: Conexão com o banco de dados
        normalizacoes: Lista de dicionários com 'tipo', 'valor_antigo', 'valor_novo'
        usuario: Nome do usuário que está realizando a operação
    
    Returns:
        Dicionário com estatísticas da operação
    """
    resultados = {
        'total_afetados': 0,
        'detalhes': [],
        'erros': []
    }
    
    for norm in normalizacoes:
        try:
            tipo = norm.get('tipo')
            valor_antigo = norm.get('valor_antigo')
            valor_novo = norm.get('valor_novo')
            
            if not all([tipo, valor_antigo, valor_novo]):
                resultados['erros'].append({
                    'tipo': tipo,
                    'valor_antigo': valor_antigo,
                    'valor_novo': valor_novo,
                    'erro': 'Dados incompletos'
                })
                continue
            
            # Converter tipo para enum se for string
            if isinstance(tipo, str):
                tipo = TipoValorControlado(tipo)
            
            afetados = normalizar_valor(db, tipo, valor_antigo, valor_novo, usuario)
            resultados['total_afetados'] += afetados
            resultados['detalhes'].append({
                'tipo': tipo.value if hasattr(tipo, 'value') else str(tipo),
                'valor_antigo': valor_antigo,
                'valor_novo': valor_novo,
                'afetados': afetados
            })
            
        except Exception as e:
            resultados['erros'].append({
                'tipo': norm.get('tipo'),
                'valor_antigo': norm.get('valor_antigo'),
                'valor_novo': norm.get('valor_novo'),
                'erro': str(e)
            })
    
    return resultados


def verificar_valores_duplicados(
    db: sqlite3.Connection,
    tipo: TipoValorControlado
) -> list[dict]:
    """
    Verifica se há valores duplicados em valor_controlado para um determinado tipo.
    Retorna lista de valores duplicados.
    """
    cursor = db.execute(
        """
        SELECT valor, COUNT(*) as count
        FROM valor_controlado
        WHERE tipo = ?
        GROUP BY valor
        HAVING COUNT(*) > 1
        """,
        (tipo.value if hasattr(tipo, 'value') else tipo,)
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def merge_valores_controlados(
    db: sqlite3.Connection,
    tipo: TipoValorControlado,
    valor_principal: str,
    valores_a_remover: list[str],
    usuario: str
) -> dict:
    """
    Mescla múltiplos valores controlados em um único valor principal.
    Útil para limpeza de dados duplicados.
    
    Args:
        db: Conexão com o banco de dados
        tipo: Tipo do valor controlado
        valor_principal: Valor que será mantido
        valores_a_remover: Lista de valores que serão mesclados no principal
        usuario: Nome do usuário que está realizando a operação
    
    Returns:
        Dicionário com estatísticas da operação
    """
    resultados = {
        'valores_removidos': [],
        'equipamentos_afetados': 0,
        'erros': []
    }
    
    # Verificar se o valor principal existe
    principal = get_valor_controlado_by_tipo_valor(db, tipo, valor_principal)
    if not principal:
        # Criar o valor principal se não existir
        principal = create_valor_controlado(
            db,
            ValorControladoCreate(tipo=tipo, valor=valor_principal),
            admin=True
        )
    
    for valor in valores_a_remover:
        try:
            # Buscar o valor a ser removido
            valor_obj = get_valor_controlado_by_tipo_valor(db, tipo, valor)
            if not valor_obj:
                resultados['erros'].append({
                    'valor': valor,
                    'erro': 'Valor não encontrado'
                })
                continue
            
            # Atualizar equipamentos que usam este valor
            if tipo == TipoValorControlado.FABRICANTE:
                cursor = db.execute(
                    "UPDATE equipamento SET fabricante_id = ? WHERE fabricante_id = ?",
                    (principal['id'], valor_obj['id'])
                )
                afetados = cursor.rowcount
            elif tipo == TipoValorControlado.MODELO:
                cursor = db.execute(
                    "UPDATE equipamento SET modelo_id = ? WHERE modelo_id = ?",
                    (principal['id'], valor_obj['id'])
                )
                afetados = cursor.rowcount
            else:
                afetados = 0
            
            # Remover o valor controlado
            db.execute(
                "DELETE FROM valor_controlado WHERE id = ?",
                (valor_obj['id'],)
            )
            
            resultados['valores_removidos'].append({
                'valor': valor,
                'equipamentos_afetados': afetados
            })
            resultados['equipamentos_afetados'] += afetados
            
        except Exception as e:
            resultados['erros'].append({
                'valor': valor,
                'erro': str(e)
            })
    
    db.commit()
    
    # Registrar auditoria
    registrar_auditoria(
        db,
        usuario,
        "merge_valores_controlados",
        f"tipo={tipo}, principal={valor_principal}, removidos={valores_a_remover}",
        f"Total de equipamentos afetados: {resultados['equipamentos_afetados']}"
    )
    
    return resultados