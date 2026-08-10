import os
from database import DATABASE_PATH, create_db_connection, get_db_connection
from services.auth import create_initial_admin

def criar_tabelas():
    """Cria todas as tabelas do banco de dados se elas não existirem"""
    
    conn = create_db_connection()
    cursor = conn.cursor()
    
    # Criar tabela valor_controlado
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS valor_controlado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor TEXT NOT NULL,
            criado_por_admin INTEGER DEFAULT 0,
            UNIQUE(tipo, valor)
        )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipamento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tombo TEXT UNIQUE NOT NULL,
        uuid TEXT,
        fabricante TEXT,
        modelo TEXT,
        numero_serie TEXT,
        localizacao TEXT,
        estado TEXT,
        inicio_garantia DATE,
        duracao_garantia INTEGER
    )
""")
    
    # Criar tabela historico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento_id INTEGER NOT NULL,
            usuario TEXT NOT NULL,
            tipo TEXT NOT NULL,
            valor_anterior TEXT,
            valor_novo TEXT,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipamento_id) REFERENCES equipamento(id) ON DELETE CASCADE
        )
    """)
    
    # Criar tabela defeito
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defeito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento_id INTEGER NOT NULL,
            componente TEXT,
            descricao TEXT NOT NULL,
            resolvido INTEGER DEFAULT 0,
            data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipamento_id) REFERENCES equipamento(id) ON DELETE CASCADE
        )
    """)
    
    # Criar tabela inventario_hardware
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario_hardware (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento_id INTEGER NOT NULL,
            cpu TEXT,
            memoria TEXT,
            armazenamento TEXT,
            gpu TEXT,
            placa_mae TEXT,
            bios TEXT,
            sistema_operacional TEXT,
            json_original TEXT,
            data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipamento_id) REFERENCES equipamento(id) ON DELETE CASCADE
        )
    """)
    
    # Criar tabela anotacao
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anotacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento_id INTEGER NOT NULL,
            usuario TEXT NOT NULL,
            texto TEXT NOT NULL,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipamento_id) REFERENCES equipamento(id) ON DELETE CASCADE
        )
    """)
    
    # Criar tabela usuario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Criar tabela auditoria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            operacao TEXT NOT NULL,
            objeto_alterado TEXT,
            antes TEXT,
            depois TEXT,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Criar índices para melhor performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipamento_tombo ON equipamento(tombo)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipamento_estado ON equipamento(estado)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historico_equipamento ON historico(equipamento_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defeito_equipamento ON defeito(equipamento_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventario_equipamento ON inventario_hardware(equipamento_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_anotacao_equipamento ON anotacao(equipamento_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_valor_controlado_tipo ON valor_controlado(tipo)")
    
    conn.commit()
    conn.close()
    
    print("Tabelas criadas/verificadas com sucesso!")


def banco_existe():
    """Verifica se o arquivo do banco de dados existe"""
    return os.path.exists(DATABASE_PATH)

def inicializar_banco():
    """Inicializa o banco de dados: cria se não existir, ou conecta se existir"""
    if banco_existe():
        print(f"Conectando ao banco de dados existente: {DATABASE_PATH}")
    else:
        print(f"Banco de dados não encontrado. Criando novo banco em: {DATABASE_PATH}")
        # O próprio sqlite3 cria o arquivo ao conectar, mas vamos garantir que o diretório existe
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Criar/verificar tabelas
    criar_tabelas()
    conn = create_db_connection()
    create_initial_admin(conn)
    
    return get_db_connection()