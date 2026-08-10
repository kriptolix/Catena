novas tabelas

CREATE TABLE inventario_processador (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario_id INTEGER NOT NULL,
    fabricante TEXT,
    modelo TEXT,
    nucleos INTEGER,
    threads INTEGER,
    clock_maximo_mhz INTEGER,

    FOREIGN KEY (inventario_id)
        REFERENCES inventario(id)
);

CREATE TABLE inventario_memoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario_id INTEGER NOT NULL,
    fabricante TEXT,
    capacidade_gb REAL,
    velocidade_mhz INTEGER,
    tipo TEXT,
    part_number TEXT,
    numero_serie TEXT,
    slot TEXT,

    FOREIGN KEY (inventario_id)
        REFERENCES inventario(id)
);

CREATE TABLE inventario_disco (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario_id INTEGER NOT NULL,
    modelo TEXT,
    fabricante TEXT,
    interface TEXT,
    tamanho_gb REAL,
    numero_serie TEXT,
    tipo TEXT,

    FOREIGN KEY (inventario_id)
        REFERENCES inventario(id)
);

CREATE TABLE inventario_gpu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario_id INTEGER NOT NULL,
    modelo TEXT,
    memoria_gb REAL,

    FOREIGN KEY (inventario_id)
        REFERENCES inventario(id)
);

CREATE TABLE inventario_placa_mae (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario_id INTEGER NOT NULL,
    fabricante TEXT,
    modelo TEXT,
    numero_serie TEXT,

    FOREIGN KEY (inventario_id)
        REFERENCES inventario(id)
);

CREATE TABLE inventario_bios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario_id INTEGER NOT NULL,
    fabricante TEXT,
    versao TEXT,
    data TEXT,

    FOREIGN KEY (inventario_id)
        REFERENCES inventario(id)
);

CREATE TABLE inventario_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario_id INTEGER NOT NULL,
    nome TEXT,
    versao TEXT,
    arquitetura TEXT,

    FOREIGN KEY (inventario_id)
        REFERENCES inventario(id)
);

CREATE TABLE inventario_rede (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario_id INTEGER NOT NULL,
    modelo TEXT,
    mac TEXT,
    velocidade_mbps INTEGER,

    FOREIGN KEY (inventario_id)
        REFERENCES inventario(id)
);

CREATE TABLE inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipamento_id INTEGER NOT NULL,
    processador_id INTEGER,
    placa_mae_id INTEGER,
    bios_id INTEGER,
    sistema_id INTEGER,
    fingerprint TEXT NOT NULL,
    data_coleta DATETIME NOT NULL,

    FOREIGN KEY (equipamento_id) REFERENCES equipamento(id),
    FOREIGN KEY (processador_id) REFERENCES processador(id),
    FOREIGN KEY (placa_mae_id) REFERENCES placa_mae(id),
    FOREIGN KEY (bios_id) REFERENCES bios(id),
    FOREIGN KEY (sistema_id) REFERENCES sistema(id)
);

CREATE TABLE inventario_memoria (
    inventario_id INTEGER NOT NULL,
    memoria_id INTEGER NOT NULL,

    PRIMARY KEY (inventario_id, memoria_id),

    FOREIGN KEY (inventario_id) REFERENCES inventario(id),
    FOREIGN KEY (memoria_id) REFERENCES memoria(id)
);

CREATE TABLE inventario_rede (
    inventario_id INTEGER NOT NULL,
    memoria_id INTEGER NOT NULL,

    PRIMARY KEY (inventario_id, rede_id),

    FOREIGN KEY (inventario_id) REFERENCES inventario(id),
    FOREIGN KEY (rede_id) REFERENCES rede(id)
);

CREATE TABLE inventario_disco (
    inventario_id INTEGER NOT NULL,
    memoria_id INTEGER NOT NULL,

    PRIMARY KEY (inventario_id, disco_id),

    FOREIGN KEY (inventario_id) REFERENCES inventario(id),
    FOREIGN KEY (disco_id) REFERENCES disco(id)
);