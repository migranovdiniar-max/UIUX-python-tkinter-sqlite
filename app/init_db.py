from pathlib import Path
from app.db import get_connection
import sqlite3

SQL_FILE = Path(__file__).resolve().parent / "db" / "init_sqlite.sql"

def init_db():
    conn = get_connection()
    sql = SQL_FILE.read_text(encoding="utf-8")
    conn.executescript(sql)

    cur = conn.cursor()

    cur.execute("INSERT OR IGNORE INTO users (name, email, role) VALUES (?, ?, ?)",
                ("Admin User", "admin@example.com", "admin"))
    cur.execute("INSERT OR IGNORE INTO users (name, email, role) VALUES (?, ?, ?)",
                ("Student User", "student@example.com", "student"))
    conn.commit()
    conn.close()

    print("DB initialized at", Path(get_connection().__self__.database) if hasattr(get_connection(), 'database') else "english.db")

if __name__ == "__main__":
    init_db()