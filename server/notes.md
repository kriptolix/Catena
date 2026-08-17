novas tabelas



CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_number TEXT UNIQUE NOT NULL,
    uuid TEXT,
    manufacturer TEXT,
    model TEXT,
    serial_number TEXT,
    localition TEXT,
    status TEXT,
    warranty_start_date DATE,
    warranty_period INTEGER
);

CREATE TABLE processor ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    manufacturer TEXT, 
    model TEXT, 
    cores INTEGER, 
    threads INTEGER, 
    clock_mhz INTEGER,
);

CREATE TABLE memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,    
    manufacturer TEXT,
    capacity_gb REAL,
    clock_mhz INTEGER,
    type TEXT,
    part_number TEXT,
    serial_number TEXT,     
);

CREATE TABLE disc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,    
    model TEXT,
    manufacturer TEXT,
    interface TEXT,
    capacity_gb REAL,
    serial_number TEXT,
    type TEXT,    
);

CREATE TABLE gpu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT,    
    model TEXT,
    memory_gb REAL,   
);

CREATE TABLE motherboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,    
    model TEXT,
    serial_number TEXT,
    manufacturer TEXT,
    bios_version TEXT,
    bios_data TEXT,     
);

CREATE TABLE system (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    name TEXT,
    version TEXT,
    architecture TEXT,
);

CREATE TABLE network (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    model TEXT,
    mac TEXT,
    speed_mbps INTEGER,
);

CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    processor_id INTEGER,
    motherboard_id INTEGER,    
    system_id INTEGER,
    fingerprint TEXT NOT NULL,
    collection_date DATETIME NOT NULL,

    FOREIGN KEY (equipment_id) REFERENCES Equipment(id),
    FOREIGN KEY (processor_id) REFERENCES processor(id),
    FOREIGN KEY (motherboard_id) REFERENCES motherboard(id),
    FOREIGN KEY (system_id) REFERENCES system(id)
);

CREATE TABLE inventory_memory (
    inventory_id INTEGER NOT NULL,
    memory_id INTEGER NOT NULL,
    slot TEXT, 

    PRIMARY KEY (inventory_id, memory_id),

    FOREIGN KEY (inventory_id) REFERENCES inventory(id),
    FOREIGN KEY (memory_id) REFERENCES memory(id)
);

CREATE TABLE inventory_network (
    inventory_id INTEGER NOT NULL,
    memory_id INTEGER NOT NULL,

    PRIMARY KEY (inventory_id, network_id),

    FOREIGN KEY (inventory_id) REFERENCES inventory(id),
    FOREIGN KEY (network_id) REFERENCES network(id)
);

CREATE TABLE inventory_disc (
    inventory_id INTEGER NOT NULL,
    memory_id INTEGER NOT NULL,

    PRIMARY KEY (inventory_id, disc_id),

    FOREIGN KEY (inventory_id) REFERENCES inventory(id),
    FOREIGN KEY (disc_id) REFERENCES disc(id)
);

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

CREATE TABLE IF NOT EXISTS defect (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    component TEXT,
    description TEXT NOT NULL,    
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES Equipment(id) ON DELETE CASCADE
)

CREATE TABLE IF NOT EXISTS annotation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    user TEXT NOT NULL,
    text TEXT NOT NULL,
    datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
)

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    fullname TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP
)