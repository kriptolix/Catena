from fastapi import APIRouter, Depends, HTTPException, Query
import sqlite3
from typing import Optional, List, Dict, Any
from database import get_db_connection
from schemas import ValorControlado, ValorControladoCreate
from crud import get_valor_controlado_by_tipo_valor, create_valor_controlado
from services.auth import get_current_admin_user
from enums import TipoValorControlado
from utils.normalizacao import normalizar_valor, verificar_valores_duplicados, merge_valores_controlados

# Type alias para usuário
UserDict = Dict[str, Any]

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/normalizar")
async def normalizar(
    tipo: TipoValorControlado,
    valor_antigo: str,
    valor_novo: str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Normaliza um valor controlado: substitui todas as ocorrências de valor_antigo por valor_novo.
    Apenas administradores podem executar esta operação.
    """
    if valor_antigo == valor_novo:
        raise HTTPException(
            status_code=400, 
            detail="Valores iguais. Não é possível normalizar um valor para ele mesmo."
        )
    
    try:
        count = normalizar_valor(db, tipo, valor_antigo, valor_novo, current_user['username'])
        return {
            "detail": f"Normalização concluída: {count} equipamentos afetados",
            "tipo": tipo.value if hasattr(tipo, 'value') else str(tipo),
            "valor_antigo": valor_antigo,
            "valor_novo": valor_novo,
            "afetados": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao normalizar: {str(e)}"
        )


@router.post("/normalizar/batch")
async def normalizar_batch(
    normalizacoes: List[dict],
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Executa múltiplas normalizações em lote.
    Apenas administradores podem executar esta operação.
    
    Exemplo de payload:
    [
        {"tipo": "fabricante", "valor_antigo": "HP Inc.", "valor_novo": "HP"},
        {"tipo": "modelo", "valor_antigo": "Latitude 5480", "valor_novo": "Latitude 5480 Pro"}
    ]
    """
    from utils.normalizacao import normalizar_valor_batch
    
    if not normalizacoes:
        raise HTTPException(
            status_code=400,
            detail="Lista de normalizações vazia"
        )
    
    try:
        resultados = normalizar_valor_batch(db, normalizacoes, current_user['username'])
        
        if resultados['erros']:
            return {
                "detail": "Normalização em lote concluída com erros",
                "resultados": resultados
            }
        
        return {
            "detail": f"Normalização em lote concluída: {resultados['total_afetados']} equipamentos afetados",
            "resultados": resultados
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar normalização em lote: {str(e)}"
        )


@router.get("/valores_controlados", response_model=List[ValorControlado])
async def list_valores_controlados(
    tipo: Optional[TipoValorControlado] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Lista todos os valores controlados com filtros opcionais.
    Apenas administradores podem visualizar.
    """
    query = """
        SELECT id, tipo, valor, criado_por_admin
        FROM valor_controlado
        WHERE 1=1
    """
    params = []
    
    if tipo:
        query += " AND tipo = ?"
        params.append(tipo.value if hasattr(tipo, 'value') else tipo)
    
    if search:
        query += " AND valor LIKE ?"
        params.append(f"%{search}%")
    
    query += " ORDER BY tipo, valor LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/valores_controlados/tipos")
async def list_tipos_valores_controlados(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Lista todos os tipos de valores controlados disponíveis.
    Apenas administradores podem visualizar.
    """
    cursor = db.execute(
        """
        SELECT DISTINCT tipo, COUNT(*) as total
        FROM valor_controlado
        GROUP BY tipo
        ORDER BY tipo
        """
    )
    rows = cursor.fetchall()
    
    return [
        {
            "tipo": row['tipo'],
            "total": row['total'],
            "label": row['tipo'].replace('_', ' ').title()
        }
        for row in rows
    ]


@router.get("/valores_controlados/{valor_id}", response_model=ValorControlado)
async def get_valor_controlado(
    valor_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Obtém um valor controlado específico pelo ID.
    Apenas administradores podem visualizar.
    """
    cursor = db.execute(
        """
        SELECT id, tipo, valor, criado_por_admin
        FROM valor_controlado
        WHERE id = ?
        """,
        (valor_id,)
    )
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Valor controlado não encontrado"
        )
    
    return dict(row)


@router.post("/valores_controlados", response_model=ValorControlado)
async def create_valor_controlado_endpoint(
    valor: ValorControladoCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Cria um novo valor controlado.
    Apenas administradores podem criar.
    """
    # Verificar se o valor já existe
    existing = get_valor_controlado_by_tipo_valor(db, valor.tipo, valor.valor)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Valor '{valor.valor}' já existe para o tipo '{valor.tipo}'"
        )
    
    try:
        novo_valor = create_valor_controlado(db, valor, admin=True)
        return novo_valor
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar valor controlado: {str(e)}"
        )


@router.delete("/valores_controlados/{valor_id}")
async def delete_valor_controlado(
    valor_id: int,
    force: bool = Query(False, description="Forçar exclusão mesmo se estiver em uso"),
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Remove um valor controlado.
    Apenas administradores podem remover.
    
    Args:
        valor_id: ID do valor controlado
        force: Se True, força a exclusão mesmo se o valor estiver em uso
    """
    # Buscar o valor
    cursor = db.execute(
        "SELECT id, tipo, valor FROM valor_controlado WHERE id = ?",
        (valor_id,)
    )
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Valor controlado não encontrado"
        )
    
    valor = dict(row)
    
    # Verificar se o valor está em uso
    cursor = db.execute(
        """
        SELECT COUNT(*) as count
        FROM equipamento
        WHERE fabricante_id = ? OR modelo_id = ?
        """,
        (valor_id, valor_id)
    )
    em_uso = cursor.fetchone()['count'] > 0
    
    if em_uso and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Valor está em uso em {cursor.fetchone()['count']} equipamentos. Use force=True para forçar a exclusão."
        )
    
    # Se force=True, remover as referências primeiro
    if em_uso and force:
        # Remover referências nos equipamentos
        db.execute(
            "UPDATE equipamento SET fabricante_id = NULL WHERE fabricante_id = ?",
            (valor_id,)
        )
        db.execute(
            "UPDATE equipamento SET modelo_id = NULL WHERE modelo_id = ?",
            (valor_id,)
        )
    
    # Remover o valor
    db.execute(
        "DELETE FROM valor_controlado WHERE id = ?",
        (valor_id,)
    )
    db.commit()
    
    # Registrar auditoria
    from crud import registrar_auditoria
    registrar_auditoria(
        db,
        current_user['username'],
        "exclusao_valor_controlado",
        f"ID: {valor_id}, Tipo: {valor['tipo']}, Valor: {valor['valor']}",
        f"Forçado: {force}, Em uso: {em_uso}"
    )
    
    return {
        "detail": f"Valor controlado '{valor['valor']}' removido com sucesso",
        "id": valor_id,
        "tipo": valor['tipo'],
        "valor": valor['valor']
    }


@router.get("/valores_controlados/duplicados")
async def verificar_duplicados(
    tipo: Optional[TipoValorControlado] = None,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Verifica valores duplicados no sistema.
    Apenas administradores podem visualizar.
    """
    if tipo:
        duplicados = verificar_valores_duplicados(db, tipo)
    else:
        # Verificar para todos os tipos
        duplicados = {}
        for tipo_enum in TipoValorControlado:
            duplicados[tipo_enum.value] = verificar_valores_duplicados(db, tipo_enum)
    
    return {
        "duplicados": duplicados,
        "total_encontrados": sum(len(v) for v in duplicados.values()) if isinstance(duplicados, dict) else len(duplicados)
    }


@router.post("/valores_controlados/merge")
async def mesclar_valores_controlados(
    tipo: TipoValorControlado,
    valor_principal: str,
    valores_a_remover: List[str],
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Mescla múltiplos valores controlados em um único valor principal.
    Útil para limpeza de dados duplicados.
    Apenas administradores podem executar esta operação.
    """
    if not valores_a_remover:
        raise HTTPException(
            status_code=400,
            detail="Lista de valores a remover vazia"
        )
    
    if valor_principal in valores_a_remover:
        raise HTTPException(
            status_code=400,
            detail="O valor principal não pode estar na lista de valores a remover"
        )
    
    try:
        resultado = merge_valores_controlados(
            db,
            tipo,
            valor_principal,
            valores_a_remover,
            current_user['username']
        )
        
        if resultado['erros']:
            return {
                "detail": "Mesclagem concluída com erros",
                "resultado": resultado
            }
        
        return {
            "detail": f"Mesclagem concluída: {resultado['equipamentos_afetados']} equipamentos afetados",
            "resultado": resultado
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao mesclar valores: {str(e)}"
        )


@router.get("/stats/valores_controlados")
async def stats_valores_controlados(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: UserDict = Depends(get_current_admin_user)
):
    """
    Estatísticas sobre valores controlados.
    Apenas administradores podem visualizar.
    """
    cursor = db.execute(
        """
        SELECT 
            tipo,
            COUNT(*) as total,
            COUNT(CASE WHEN criado_por_admin = 1 THEN 1 END) as criados_por_admin,
            COUNT(CASE WHEN criado_por_admin = 0 THEN 1 END) as criados_por_coletor
        FROM valor_controlado
        GROUP BY tipo
        ORDER BY tipo
        """
    )
    rows = cursor.fetchall()
    
    return {
        "estatisticas": [dict(row) for row in rows],
        "total_geral": sum(row['total'] for row in rows)
    }
