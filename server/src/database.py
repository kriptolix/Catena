# database.py
from contextlib import contextmanager
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(BASE_DIR, "data_collector.db")

print(f"Database path: {DATABASE_PATH}")

def get_db_connection():
    """Retorna uma conexão com o banco de dados"""
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# FASTAPI Dependency
def get_db():
    """Dependência para FastAPI"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    from sql import inicializar_banco
    return inicializar_banco()
