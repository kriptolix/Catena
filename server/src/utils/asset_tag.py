import sqlite3
from database import create_db_connection
from typing import Optional


def generate_next_asset_tag(prefixo: str = "X") -> str:
    """
    Gera o próximo tombo garantindo que não exista conflito.
    Verifica se o tombo gerado já existe e incrementa até encontrar um disponível.
    
    Args:
        prefixo: Prefixo do tombo (padrão: "XX")
    
    Returns:
        Novo tombo único no formato {prefixo}000001
    """
    conn = create_db_connection()
    try:
        # Buscar todos os números de tombo com o prefixo
        cursor = conn.execute(
            """
            SELECT tombo FROM Equipment 
            WHERE tombo LIKE ?
            """,
            (f"{prefixo}%",)
        )
        tombo_existentes = cursor.fetchall()
        
        # Extrair os números
        numeros = []
        for row in tombo_existentes:
            tombo = row['tombo']
            if tombo.startswith(prefixo) and len(tombo) > len(prefixo):
                try:
                    num_str = tombo[len(prefixo):]
                    numeros.append(int(num_str))
                except ValueError:
                    pass
        
        # Encontrar o menor número disponível (considerando lacunas)
        if not numeros:
            numero = 1
        else:
            numeros.sort()
            # Procurar o primeiro número faltante na sequência
            numero = 1
            for num in numeros:
                if num == numero:
                    numero += 1
                else:
                    break
        
        novo_tombo = f"{prefixo}{numero:06d}"
        return novo_tombo
    
    finally:
        conn.close()


def validar_tombo(asset_tag: str, prefixo: str = "X") -> bool:

    """
    Valida se um tombo está no formato correto.
    
    Args:
        asset_number Tombo a ser validado
        prefixo: Prefixo esperado (padrão: "XX")
    
    Returns:
        True se o tombo for válido, False caso contrário
    """
    if not asset_tag:
        return False
    
    if not asset_tag.startswith(prefixo):
        return False
    
    numero_str = asset_tag[len(prefixo):]
    if len(numero_str) != 6:
        return False
    
    try:
        int(numero_str)
        return True
    except ValueError:
        return False


# Função para uso em ambiente de teste (opcional)
def resetar_sequencia_tombo(prefixo: str = "X", valor_inicial: int = 1) -> bool:
    """
    RESETAR A SEQUÊNCIA DE TOMBOS - CUIDADO!
    Esta função NÃO deve ser usada em produção.
    Apenas para fins de teste.
    
    Args:
        prefixo: Prefixo do tombo
        valor_inicial: Valor inicial da sequência
    
    Returns:
        True se bem sucedido
    """
    import warnings
    warnings.warn("Esta função é apenas para testes! Não use em produção.", UserWarning)
    
    conn = create_db_connection()
    try:
        # Verificar se existem Equipments com o prefixo
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM Equipment WHERE tombo LIKE ?",
            (f"{prefixo}%",)
        )
        count = cursor.fetchone()['count']
        
        if count > 0:
            print(f"ATENÇÃO: Existem {count} Equipments com o prefixo {prefixo}.")
            resposta = input("Tem certeza que deseja resetar a sequência? (s/N): ")
            if resposta.lower() != 's':
                return False
        
        return True
    
    finally:
        conn.close()