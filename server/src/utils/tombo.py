import sqlite3
from database import get_db_connection
from typing import Optional


def gerar_proximo_tombo(prefixo: str = "XX") -> str:
    """
    Gera o próximo tombo no formato {prefixo}000001, baseado no último número usado.
    
    Args:
        prefixo: Prefixo do tombo (padrão: "XX")
    
    Returns:
        Novo tombo no formato {prefixo}000001
    
    Exemplo:
        >>> gerar_proximo_tombo()
        'XX000001'
        >>> gerar_proximo_tombo("EQ")
        'EQ000001'
    """
    conn = get_db_connection()
    try:
        # Buscar o maior tombo que começa com o prefixo especificado
        cursor = conn.execute(
            """
            SELECT tombo FROM equipamento 
            WHERE tombo LIKE ? 
            ORDER BY tombo DESC 
            LIMIT 1
            """,
            (f"{prefixo}%",)
        )
        resultado = cursor.fetchone()
        
        if resultado:
            # Extrair o número após o prefixo
            tombo_atual = resultado['tombo']
            # Verificar se o tombo tem o formato esperado
            if tombo_atual.startswith(prefixo) and len(tombo_atual) > len(prefixo):
                numero_str = tombo_atual[len(prefixo):]  # ex: '000001'
                try:
                    numero = int(numero_str) + 1
                except ValueError:
                    # Se não for um número válido, começar do 1
                    numero = 1
            else:
                numero = 1
        else:
            numero = 1
        
        novo_tombo = f"{prefixo}{numero:06d}"
        return novo_tombo
    
    finally:
        conn.close()


def gerar_proximo_tombo_com_validacao(prefixo: str = "XX") -> str:
    """
    Gera o próximo tombo garantindo que não exista conflito.
    Verifica se o tombo gerado já existe e incrementa até encontrar um disponível.
    
    Args:
        prefixo: Prefixo do tombo (padrão: "XX")
    
    Returns:
        Novo tombo único no formato {prefixo}000001
    """
    conn = get_db_connection()
    try:
        # Buscar todos os números de tombo com o prefixo
        cursor = conn.execute(
            """
            SELECT tombo FROM equipamento 
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


def validar_tombo(tombo: str, prefixo: str = "XX") -> bool:
    """
    Valida se um tombo está no formato correto.
    
    Args:
        tombo: Tombo a ser validado
        prefixo: Prefixo esperado (padrão: "XX")
    
    Returns:
        True se o tombo for válido, False caso contrário
    """
    if not tombo:
        return False
    
    if not tombo.startswith(prefixo):
        return False
    
    numero_str = tombo[len(prefixo):]
    if len(numero_str) != 6:
        return False
    
    try:
        int(numero_str)
        return True
    except ValueError:
        return False


def gerar_proximo_tombo_com_prefixo_dinamico(prefixo: str = "XX", tamanho_numero: int = 6) -> str:
    """
    Gera o próximo tombo com prefixo e tamanho de número personalizáveis.
    
    Args:
        prefixo: Prefixo do tombo (padrão: "XX")
        tamanho_numero: Quantidade de dígitos para o número (padrão: 6)
    
    Returns:
        Novo tombo no formato {prefixo}{numero:0{tamanho_numero}d}
    """
    conn = get_db_connection()
    try:
        # Buscar o maior tombo que começa com o prefixo
        cursor = conn.execute(
            """
            SELECT tombo FROM equipamento 
            WHERE tombo LIKE ? 
            ORDER BY tombo DESC 
            LIMIT 1
            """,
            (f"{prefixo}%",)
        )
        resultado = cursor.fetchone()
        
        if resultado:
            tombo_atual = resultado['tombo']
            if tombo_atual.startswith(prefixo) and len(tombo_atual) > len(prefixo):
                numero_str = tombo_atual[len(prefixo):]
                try:
                    numero = int(numero_str) + 1
                except ValueError:
                    numero = 1
            else:
                numero = 1
        else:
            numero = 1
        
        # Formatar o número com zeros à esquerda
        formato = f"{{:0{tamanho_numero}d}}"
        novo_tombo = f"{prefixo}{formato.format(numero)}"
        return novo_tombo
    
    finally:
        conn.close()


def obter_proximo_tombo_disponivel(prefixo: str = "XX") -> str:
    """
    Obtém o próximo tombo disponível considerando tombos existentes.
    Útil quando há tombos com formatação irregular.
    
    Args:
        prefixo: Prefixo do tombo (padrão: "XX")
    
    Returns:
        Próximo tombo disponível
    """
    conn = get_db_connection()
    try:
        # Buscar todos os tombos que começam com o prefixo
        cursor = conn.execute(
            """
            SELECT tombo FROM equipamento 
            WHERE tombo LIKE ?
            """,
            (f"{prefixo}%",)
        )
        tombo_existentes = cursor.fetchall()
        
        if not tombo_existentes:
            return f"{prefixo}000001"
        
        # Extrair números e encontrar o máximo
        max_numero = 0
        for row in tombo_existentes:
            tombo = row['tombo']
            if tombo.startswith(prefixo):
                try:
                    num_str = tombo[len(prefixo):]
                    # Tentar extrair apenas números
                    import re
                    numeros = re.findall(r'\d+', num_str)
                    if numeros:
                        numero = int(numeros[0])
                        if numero > max_numero:
                            max_numero = numero
                except (ValueError, IndexError):
                    pass
        
        novo_numero = max_numero + 1
        return f"{prefixo}{novo_numero:06d}"
    
    finally:
        conn.close()


# Função para uso em ambiente de teste (opcional)
def resetar_sequencia_tombo(prefixo: str = "XX", valor_inicial: int = 1) -> bool:
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
    
    conn = get_db_connection()
    try:
        # Verificar se existem equipamentos com o prefixo
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM equipamento WHERE tombo LIKE ?",
            (f"{prefixo}%",)
        )
        count = cursor.fetchone()['count']
        
        if count > 0:
            print(f"ATENÇÃO: Existem {count} equipamentos com o prefixo {prefixo}.")
            resposta = input("Tem certeza que deseja resetar a sequência? (s/N): ")
            if resposta.lower() != 's':
                return False
        
        return True
    
    finally:
        conn.close()