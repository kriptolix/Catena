import os
from database import DATABASE_PATH, create_db_connection, get_db_connection
from services.auth import create_initial_admin


def create_tables():
    """Cria todas as tabelas do banco de dados se elas não existirem"""

    conn = create_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS location (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE        
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_tag TEXT UNIQUE NOT NULL,
        uuid TEXT,
        manufacturer TEXT,
        model TEXT,
        serial_number TEXT,
        location_id INTEGER,
        status TEXT,
        warranty_start_date DATE,
        warranty_period INTEGER,
        active INTEGER NOT NULL DEFAULT 1,

        FOREIGN KEY (location_id) REFERENCES location(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        manufacturer TEXT,
        model TEXT,
        cores INTEGER,
        threads INTEGER,
        clock_mhz INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        manufacturer TEXT,
        capacity_gb REAL,
        clock_mhz INTEGER,
        type TEXT,
        part_number TEXT,
        serial_number TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS disc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        manufacturer TEXT,
        interface TEXT,
        capacity_gb REAL,
        serial_number TEXT,
        type TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gpu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        manufacturer TEXT,
        model TEXT,
        memory_gb REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS motherboard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        serial_number TEXT,
        manufacturer TEXT,
        bios_version TEXT,
        bios_date TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        version TEXT,
        architecture TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS network (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        mac TEXT,
        speed_mbps INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        processor_id INTEGER,
        motherboard_id INTEGER,
        system_id INTEGER,
        gpu_id INTEGER,
        fingerprint TEXT NOT NULL,
        collection_date DATETIME NOT NULL,

        FOREIGN KEY (equipment_id) REFERENCES equipment(id),
        FOREIGN KEY (processor_id) REFERENCES processor(id),
        FOREIGN KEY (motherboard_id) REFERENCES motherboard(id),
        FOREIGN KEY (system_id) REFERENCES system(id),
        FOREIGN KEY (gpu_id) REFERENCES gpu(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_memory (
        inventory_id INTEGER NOT NULL,
        memory_id INTEGER NOT NULL,
        slot TEXT,

        PRIMARY KEY (inventory_id, memory_id),

        FOREIGN KEY (inventory_id) REFERENCES inventory(id),
        FOREIGN KEY (memory_id) REFERENCES memory(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_network (
        inventory_id INTEGER NOT NULL,
        network_id INTEGER NOT NULL,

        PRIMARY KEY (inventory_id, network_id),

        FOREIGN KEY (inventory_id) REFERENCES inventory(id),
        FOREIGN KEY (network_id) REFERENCES network(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_disc (
        inventory_id INTEGER NOT NULL,
        disc_id INTEGER NOT NULL,

        PRIMARY KEY (inventory_id, disc_id),

        FOREIGN KEY (inventory_id) REFERENCES inventory(id),
        FOREIGN KEY (disc_id) REFERENCES disc(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        user TEXT NOT NULL,
        type TEXT NOT NULL,
        previous_value TEXT,
        next_value TEXT,
        datetime DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS prevent_history_update
        BEFORE UPDATE ON history
        BEGIN
            SELECT RAISE(ABORT, 'History records cannot be modified');
        END
        ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS prevent_history_delete
        BEFORE DELETE ON history
        BEGIN
            SELECT RAISE(ABORT, 'History records cannot be deleted');
        END
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            previous_value TEXT,
            next_value TEXT,
            datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS defect (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        component TEXT,
        description TEXT NOT NULL,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS annotation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        user TEXT NOT NULL,
        text TEXT NOT NULL,
        datetime DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        fullname TEXT NOT NULL,
        hashed_password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        creation_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Criar índices para melhor performance
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_inventory_equipment_id
    ON inventory(equipment_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_inventory_processor_id
    ON inventory(processor_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_inventory_motherboard_id
    ON inventory(motherboard_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_inventory_system_id
    ON inventory(system_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_inventory_gpu_id
    ON inventory(gpu_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_inventory_memory_memory_id
    ON inventory_memory(memory_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_inventory_network_network_id
    ON inventory_network(network_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_inventory_disc_disc_id
    ON inventory_disc(disc_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_history_equipment_id
    ON history(equipment_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_defect_equipment_id
    ON defect(equipment_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_annotation_equipment_id
    ON annotation(equipment_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_equipment_status
    ON equipment(status)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_inventory_fingerprint
    ON inventory(fingerprint)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_history_datetime
    ON history(datetime)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_defect_date
    ON defect(date)
    ''')

    conn.commit()
    conn.close()


print("Tabelas criadas/verificadas com sucesso!")


def database_exists():
    """Verifica se o arquivo do banco de dados existe"""
    return os.path.exists(DATABASE_PATH)


def initialize_database():
    """Inicializa o banco de dados: cria se não existir, ou conecta se existir"""
    if database_exists():
        print(f"Conectando ao banco de dados existente: {DATABASE_PATH}")
    else:
        print(
            f"Banco de dados não encontrado. Criando novo banco em: {DATABASE_PATH}")
        # O próprio sqlite3 cria o arquivo ao conectar, mas vamos garantir que o diretório existe
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    # Criar/verificar tabelas
    create_tables()
    conn = create_db_connection()
    create_initial_admin(conn)

    return get_db_connection()
