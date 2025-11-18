import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "english.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_key = ON")
    return conn