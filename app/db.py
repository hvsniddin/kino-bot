import sqlite3
from typing import List, NamedTuple, Optional, Tuple

from app.config import DB_PATH


class Channel(NamedTuple):
    invite_link: str
    chat_id: int


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
    channel_info = conn.execute("PRAGMA table_info(channels)").fetchall()
    channel_columns = [row[1] for row in channel_info]
    desired_columns = ["invite_link", "chat_id"]
    if not channel_info:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                invite_link TEXT PRIMARY KEY,
                chat_id INTEGER NOT NULL UNIQUE
            );
            """
        )
    elif channel_columns != desired_columns:
        conn.execute("ALTER TABLE channels RENAME TO channels_old")
        conn.execute("CREATE TABLE channels (invite_link TEXT PRIMARY KEY, chat_id INTEGER NOT NULL UNIQUE)")
        try:
            existing_cols = {row[1] for row in channel_info}
            if existing_cols == {"invite_link", "chat_id"}:
                conn.execute("INSERT OR IGNORE INTO channels (invite_link, chat_id) SELECT invite_link, chat_id FROM channels_old")
            elif "invite_link" in existing_cols:
                conn.execute("INSERT OR IGNORE INTO channels (invite_link) SELECT invite_link FROM channels_old")
        except sqlite3.OperationalError:
            pass
        conn.execute("DROP TABLE channels_old")
    # Join requests
    jr_info = conn.execute("PRAGMA table_info(join_requests)").fetchall()
    if not jr_info:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS join_requests (
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                requested_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                PRIMARY KEY (user_id, chat_id)
            );
            """
        )
    conn.commit()
    return conn


_conn = _get_connection()


# Movies

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


# Channels

def add_channel(invite_link: str, chat_id: int) -> bool:
    try:
        _conn.execute("INSERT INTO channels (invite_link, chat_id) VALUES (?, ?)", (invite_link, chat_id))
        _conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def update_channel_invite(old_invite_link: str, new_invite_link: str) -> bool:
    cur = _conn.execute("UPDATE channels SET invite_link = ? WHERE invite_link = ?", (new_invite_link, old_invite_link))
    _conn.commit()
    return cur.rowcount > 0


def get_channel(invite_link: str) -> Optional[Channel]:
    row = _conn.execute("SELECT invite_link, chat_id FROM channels WHERE invite_link = ?", (invite_link,)).fetchone()
    return Channel(*row) if row else None


def get_channel_by_chat_id(chat_id: int) -> Optional[Channel]:
    row = _conn.execute("SELECT invite_link, chat_id FROM channels WHERE chat_id = ?", (chat_id,)).fetchone()
    return Channel(*row) if row else None


def list_channels() -> List[Channel]:
    rows = _conn.execute("SELECT invite_link, chat_id FROM channels ORDER BY rowid").fetchall()
    return [Channel(*row) for row in rows]


def remove_channel(invite_link: str) -> bool:
    cur = _conn.execute("DELETE FROM channels WHERE invite_link = ?", (invite_link,))
    _conn.commit()
    return cur.rowcount > 0


# Join Requests

def upsert_join_request(user_id: int, chat_id: int, status: str = "pending") -> None:
    _conn.execute(
        """
        INSERT INTO join_requests (user_id, chat_id, status) VALUES (?, ?, ?)
        ON CONFLICT(user_id, chat_id) DO UPDATE SET status=excluded.status, requested_at=strftime('%s','now')
        """,
        (user_id, chat_id, status),
    )
    _conn.commit()


def has_pending_join_request(user_id: int, chat_id: int) -> bool:
    row = _conn.execute(
        "SELECT 1 FROM join_requests WHERE user_id = ? AND chat_id = ? AND status = 'pending'",
        (user_id, chat_id),
    ).fetchone()
    return bool(row)


def remove_join_request(user_id: int, chat_id: int) -> None:
    _conn.execute("DELETE FROM join_requests WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    _conn.commit()
