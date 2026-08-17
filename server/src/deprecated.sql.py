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
    CREATE TABLE IF NOT EXISTS Equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tombo TEXT UNIQUE NOT NULL,
        uuid TEXT,
        manufacturer TEXT,
        model TEXT,
        serial_number TEXT,
        location TEXT,
        status TEXT,
        warranty_start DATE,
        warranty_period INTEGER
    )
""")
    
    # Criar tabela historico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            user TEXT NOT NULL,
            tipo TEXT NOT NULL,
            previous_value TEXT,
            next_value TEXT,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES Equipment(id) ON DELETE CASCADE
        )
    """)
    
    # Criar tabela defeito
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defeito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            componente TEXT,
            descricao TEXT NOT NULL,
            resolvido INTEGER DEFAULT 0,
            data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES Equipment(id) ON DELETE CASCADE
        )
    """)
    
    # Criar tabela inventario_hardware
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario_hardware (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            cpu TEXT,
            memoria TEXT,
            armazenamento TEXT,
            gpu TEXT,
            motherboard TEXT,
            bios TEXT,
            system TEXT,
            json_original TEXT,
            collection_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES Equipment(id) ON DELETE CASCADE
        )
    """)
    
    # Criar tabela annotation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annotation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            user TEXT NOT NULL,
            texto TEXT NOT NULL,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES Equipment(id) ON DELETE CASCADE
        )
    """)
    
    # Criar tabela user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
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
            user TEXT NOT NULL,
            operacao TEXT NOT NULL,
            objeto_alterado TEXT,
            antes TEXT,
            depois TEXT,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Criar índices para melhor performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_Equipment_tombo ON Equipment(tombo)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_Equipment_status ON Equipment(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historico_Equipment ON historico(equipment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defeito_Equipment ON defeito(equipment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventario_Equipment ON inventario_hardware(equipment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_annotation_Equipment ON annotation(equipment_id)")
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