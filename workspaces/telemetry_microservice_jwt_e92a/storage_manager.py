"""SQLite Transactional Persistence Layer."""
import sqlite3
from typing import List, Dict, Any

class StorageManager:
    def __init__(self, db_path: str = "autonomous_system.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def insert_record(self, record_id: str, name: str, domain: str = "", status: str = "active") -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO records (id, name, domain, status)
                VALUES (?, ?, ?, ?)
            """, (record_id, name, domain, status))
            conn.commit()
        return True

    def get_all_records(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, domain, status FROM records")
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "domain": r[2], "status": r[3]} for r in rows]
