import sqlite3
from typing import Optional, Tuple

from app.config import DB_PATH


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            storage_message_id INTEGER,
            name TEXT,
            description TEXT
        );
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(movies)").fetchall()}
    if "storage_message_id" not in columns:
        conn.execute("ALTER TABLE movies ADD COLUMN storage_message_id INTEGER")
    if "name" not in columns:
        conn.execute("ALTER TABLE movies ADD COLUMN name TEXT")
    if "description" not in columns:
        conn.execute("ALTER TABLE movies ADD COLUMN description TEXT")
    conn.commit()
    return conn


_conn = _get_connection()


def save_movie(code: str, file_id: str, storage_message_id: Optional[int], name: str, description: str) -> bool:
    try:
        _conn.execute(
            "INSERT INTO movies (code, file_id, storage_message_id, name, description) VALUES (?, ?, ?, ?, ?)",
            (code, file_id, storage_message_id, name, description),
        )
        _conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_movie_record(code: str) -> Optional[Tuple[str, str, Optional[int], Optional[str], Optional[str]]]:
    return _conn.execute(
        "SELECT code, file_id, storage_message_id, name, description FROM movies WHERE code = ?",
        (code,),
    ).fetchone()


def remove_movie(code: str) -> bool:
    cur = _conn.execute("DELETE FROM movies WHERE code = ?", (code,))
    _conn.commit()
    return cur.rowcount > 0
