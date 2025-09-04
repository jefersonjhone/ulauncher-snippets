import logging
import os
import sqlite3
from typing import List, Dict, Optional

_LOGGER_ = logging.getLogger(__name__)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
db_name = "snippets.db"


class DataBase:
    """Abstraction of the database using sqlite with snippet support"""

    SEARCH_LIMIT_MIN = 2
    SEARCH_LIMIT_DEFAULT = 8
    SEARCH_LIMIT_MAX = 50

    def __init__(self, db_path="DEFAULT"):
        self.db = db_name if db_path == "DEFAULT" else db_path

        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS DB_VERSION (VERSION INTEGER NOT NULL)"
            )

            version = conn.execute("SELECT VERSION FROM DB_VERSION").fetchone()
            _LOGGER_.debug(f"Current DB version: {version}")

            if version is None:
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS SNIPPETS (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        NAME TEXT NOT NULL UNIQUE,
                        CONTENT TEXT NOT NULL,
                        TYPE TEXT NOT NULL,
                        CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        LAST_USED TIMESTAMP NULL,
                        USAGE_COUNT INTEGER DEFAULT 0
                    );"""
                )
                conn.execute("INSERT INTO DB_VERSION VALUES (1)")
                version = (1,)

            if version[0] != 1:
                _LOGGER_.error(f"Unexpected database version: {version[0]}")

    def execute_statement(self, statement, params=()):
        """Executes query and returns cursor"""
        with sqlite3.connect(self.db) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(statement, params)
            conn.commit()
            return cur

    def add_snippet(self, name: str, content: str, type_: str) -> bool:
        try:
            self.execute_statement(
                """INSERT OR REPLACE INTO SNIPPETS 
                   (NAME, CONTENT, TYPE, CREATED_AT) 
                   VALUES (?, ?, ?, datetime('now'))""",
                (name, content, type_),
            )
            return True
        except sqlite3.Error as e:
            _LOGGER_.error(f"Error adding snippet: {e}")
            return False

    def get_snippet(self, name: str, default=None) -> Optional[Dict]:
        try:
            row = self.execute_statement(
                "SELECT * FROM SNIPPETS WHERE NAME = ?", (name,)
            ).fetchone()
            return dict(row) if row else default
        except sqlite3.Error as e:
            _LOGGER_.error(f"Error getting snippet: {e}")
            return None

    def list_snippets(self, search_query: str = None, page=1, page_size=SEARCH_LIMIT_DEFAULT) -> List[Dict]:
        try:
            offset = (page - 1) * page_size
            if search_query:
                
                cur = self.execute_statement(
                    """
                    SELECT *
                    FROM SNIPPETS
                    WHERE NAME LIKE ? OR TYPE LIKE ?
                    ORDER BY
                        CASE WHEN NAME LIKE ? THEN 0 ELSE 1 END,
                        LAST_USED DESC,
                        USAGE_COUNT DESC
                    LIMIT ? OFFSET ?    
                    """,
                    (f"%{search_query}%", f"%{search_query}%", f"{search_query}%", page_size, offset),
                )

            else:
                cur = self.execute_statement(
                    "SELECT * FROM SNIPPETS ORDER BY LAST_USED DESC, USAGE_COUNT DESC LIMIT ? OFFSET ?", (page_size, offset)
                )
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            _LOGGER_.error(f"Error listing snippets: {e}")
            return []

    def remove_snippet(self, name: str) -> bool:
        try:
            self.execute_statement("DELETE FROM SNIPPETS WHERE NAME = ?", (name,))
            return True
        except sqlite3.Error as e:
            _LOGGER_.error(f"Error removing snippet: {e}")
            return False

    def update_snippet_usage(self, name: str) -> bool:
        try:
            self.execute_statement(
                """UPDATE SNIPPETS 
                   SET LAST_USED = datetime('now'), 
                       USAGE_COUNT = USAGE_COUNT + 1 
                   WHERE NAME = ?""",
                (name,),
            )
            return True
        except sqlite3.Error as e:
            _LOGGER_.error(f"Error updating usage: {e}")
            return False

    def search_snippets(
        self, query: str, limit: int = SEARCH_LIMIT_DEFAULT
    ) -> List[Dict]:
        """Search snippets with limit"""
        try:
            if len(query) < self.SEARCH_LIMIT_MIN:
                return []

            limit = min(limit, self.SEARCH_LIMIT_MAX)
            cur = self.execute_statement(
                "SELECT * FROM SNIPPETS WHERE NAME LIKE ? "
                "ORDER BY USAGE_COUNT DESC LIMIT ?",
                (f"%{query}%", limit),
            )
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            _LOGGER_.error(f"Error searching snippets: {e}")
            return []
