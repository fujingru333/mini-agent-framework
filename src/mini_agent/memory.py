"""记忆存储：会话消息的存取抽象与实现（SQLite / PostgreSQL）。"""

import abc
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2


class Storage(abc.ABC):
    """存储抽象（"口子"）：Agent 只依赖这个接口，不关心具体数据库。

    将来接 PostgreSQL / Redis：写一个新类实现同样三个方法，
    传给 Agent 即可，Agent 和框架其他代码一行都不用改。
    """

    @abc.abstractmethod
    def save_message(self, session_id: str, message: dict[str, Any]) -> None:
        """把一条消息写入指定会话。"""

    @abc.abstractmethod
    def load_messages(self, session_id: str) -> list[dict[str, Any]]:
        """按时间顺序读出指定会话的全部消息。"""

    @abc.abstractmethod
    def clear_session(self, session_id: str) -> None:
        """清空指定会话的历史。"""


class SQLiteStorage(Storage):
    """基于 SQLite 的会话存储实现（开发/单机场景，零依赖）。"""

    def __init__(self, db_path: str | Path = "agent_memory.db"):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id   TEXT NOT NULL,
                message_json TEXT NOT NULL,   -- 整条消息的 JSON，无损保真
                created_at   TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)"
        )

    def save_message(self, session_id: str, message: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO messages (session_id, message_json, created_at) VALUES (?, ?, ?)",
            (
                session_id,
                json.dumps(message, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def load_messages(self, session_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT message_json FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def clear_session(self, session_id: str) -> None:
        self.conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.conn.commit()


class PostgreSQLStorage(Storage):
    """基于 PostgreSQL 的会话存储实现。

    与 SQLiteStorage 实现相同的 Storage 接口，切换后端时 Agent 代码零改动。
    与 SQLite 的两个关键差异（否则直接崩）：
    - 占位符用 %s 而不是 ?
    - 自增主键用 SERIAL PRIMARY KEY（SQLite 的 INTEGER PRIMARY KEY 在 PG 中不会自增）
    """

    def __init__(
            self,
            host: str = "localhost",
            port: int = 5433,
            user: str = "postgres",
            password: str = "postgres",
            dbname: str = "agent_db",
    ):
        self.conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        )
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id           SERIAL PRIMARY KEY,
                    session_id   TEXT NOT NULL,
                    message_json TEXT NOT NULL,
                    created_at   TIMESTAMPTZ NOT NULL
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)"
            )
        self.conn.commit()

    def save_message(self, session_id: str, message: dict[str, Any]) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (session_id, message_json, created_at) VALUES (%s, %s, %s)",
                (
                    session_id,
                    json.dumps(message, ensure_ascii=False),
                    datetime.now(timezone.utc),
                ),
            )
        self.conn.commit()

    def load_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT message_json FROM messages WHERE session_id = %s ORDER BY id",
                (session_id,),
            )
            rows = cur.fetchall()
        return [json.loads(row[0]) for row in rows]

    def clear_session(self, session_id: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
        self.conn.commit()
