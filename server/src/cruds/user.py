import sqlite3
from schemas.user import UserCreate, UserUpdate
from services.auth import get_password_hash
from utils.to_dict import _row_to_dict

def get_user_by_username(db: sqlite3.Connection, username: str):
    cursor = db.execute(
        "SELECT * FROM user WHERE username = ? LIMIT 1",
        (username,)
    )
    return _row_to_dict(cursor.fetchone())


def create_user(db: sqlite3.Connection, user: UserCreate):
    hashed = get_password_hash(user.hashed_password)
    cursor = db.execute(
        """
        INSERT INTO user (
            username, hashed_password, is_admin, ativo
        ) VALUES (?, ?, ?, ?)
        """,
        (user.username, hashed, user.is_admin or 0, 1)
    )
    db.commit()

    cursor = db.execute(
        "SELECT * FROM user WHERE id = ?",
        (cursor.lastrowid,)
    )
    return _row_to_dict(cursor.fetchone())


def update_user(db: sqlite3.Connection, username: str, user_update: UserUpdate):
    db_user = get_user_by_username(db, username)
    if not db_user:
        return None

    update_fields = []
    params = []

    if user_update.hashed_password:
        update_fields.append("hashed_password = ?")
        params.append(get_password_hash(user_update.hashed_password))

    if user_update.is_admin is not None:
        update_fields.append("is_admin = ?")
        params.append(1 if user_update.is_admin else 0)

    if user_update.active is not None:
        update_fields.append("ativo = ?")
        params.append(1 if user_update.active else 0)

    if update_fields:
        params.append(username)
        query = f"""
            UPDATE user
            SET {', '.join(update_fields)}
            WHERE username = ?
        """
        db.execute(query, params)
        db.commit()

    return get_user_by_username(db, username)