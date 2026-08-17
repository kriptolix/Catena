def _row_to_dict(row):
    """Converte uma linha SQLite para dicionário com nomes de colunas"""
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def _fetch_all_as_dict(cursor):
    """Converte todas as linhas do cursor para lista de dicionários"""
    rows = cursor.fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]