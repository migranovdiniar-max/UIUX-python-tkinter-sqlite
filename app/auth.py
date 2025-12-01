import os
from datetime import datetime
import sqlite3
from typing import Optional
from dotenv import load_dotenv
from argon2 import PasswordHasher
from app.db import get_connection

# Загружаем .env
load_dotenv()

# Хэширование
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1, hash_len=32, salt_len=16)

# Админ-токен из .env
ADMIN_TOKEN = os.getenv("ADMIN_SECRET_TOKEN")
if not ADMIN_TOKEN:
    raise RuntimeError("ADMIN_SECRET_TOKEN не задан в .env")
ADMIN_TOKEN_HASH = ph.hash(ADMIN_TOKEN)

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except:
        return False

def validate_admin_token(input_token: str) -> bool:
    """Проверяет, совпадает ли введённый токен с хранимым"""
    if not input_token:
        return False
    try:
        return ph.verify(ADMIN_TOKEN_HASH, input_token)
    except:
        return False

def authenticate(email: str, password: str) -> Optional[dict]:
    """Аутентификация пользователя"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, name, email, role, current_level, start_date, target_level, hashed_password
        FROM users WHERE email = ?
    """, (email,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None
    if not verify_password(password, row["hashed_password"]):
        return None

    return {k: row[k] for k in row.keys() if k != "hashed_password"}

def register_user(
    name: str,
    email: str,
    password: str,
    role: str,
    current_level: str = None,
    target_level: str = None,
    admin_token: str = None
) -> bool:
    """Регистрация пользователя с проверкой токена для админов"""
    if role not in ("admin", "student"):
        return False

    admin_token_hash = None
    if role == "admin":
        if not validate_admin_token(admin_token):
            return False
        admin_token_hash = ADMIN_TOKEN_HASH

    try:
        hashed_password = hash_password(password)
        conn = get_connection()
        cur = conn.cursor()

        if role == "student":
            start_date = datetime.now().strftime("%Y-%m-%d")
            cur.execute("""
                INSERT INTO users (name, email, role, hashed_password, current_level, target_level, start_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, email, role, hashed_password, current_level, target_level, start_date))
        else:
            cur.execute("""
                INSERT INTO users (name, email, role, hashed_password, admin_token_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, role, hashed_password, admin_token_hash))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print("Ошибка регистрации:", e)
        return False
    finally:
        conn.close()
