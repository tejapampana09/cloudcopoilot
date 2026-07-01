import os
import sqlite3
import json
import collections.abc

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cloudpilot.db")

def init_db():
    """Initializes SQLite database tables if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            task_id TEXT PRIMARY KEY,
            data TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            generation_id TEXT PRIMARY KEY,
            data TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

class PersistentDict(dict):
    """A dictionary wrapper that hooks mutating operations and triggers a database write-back."""
    def __init__(self, key, db_dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._key = key
        self._db_dict = db_dict
        
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._db_dict.write_back(self._key, self)
        
    def __delitem__(self, key):
        super().__delitem__(key)
        self._db_dict.write_back(self._key, self)
        
    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._db_dict.write_back(self._key, self)
        
    def pop(self, *args, **kwargs):
        val = super().pop(*args, **kwargs)
        self._db_dict.write_back(self._key, self)
        return val
        
    def clear(self):
        super().clear()
        self._db_dict.write_back(self._key, self)

class SqliteDict(collections.abc.MutableMapping):
    """A dictionary-like interface mapping read/write operations to SQLite tables."""
    def __init__(self, table_name, key_column):
        self.table_name = table_name
        self.key_column = key_column
        
    def _connect(self):
        return sqlite3.connect(DB_PATH)
        
    def write_back(self, key, val_dict):
        """Serializes and writes/updates data to SQLite."""
        conn = self._connect()
        cursor = conn.cursor()
        data_str = json.dumps(val_dict)
        status = val_dict.get("status", "pending")
        cursor.execute(
            f"INSERT OR REPLACE INTO {self.table_name} ({self.key_column}, data, status) VALUES (?, ?, ?)",
            (key, data_str, status)
        )
        conn.commit()
        conn.close()
        
    def __getitem__(self, key):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT data FROM {self.table_name} WHERE {self.key_column} = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise KeyError(key)
        # Return a proxy dict so nested updates trigger database changes
        return PersistentDict(key, self, json.loads(row[0]))
        
    def __setitem__(self, key, value):
        self.write_back(key, value)
        
    def __delitem__(self, key):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.table_name} WHERE {self.key_column} = ?", (key,))
        conn.commit()
        conn.close()
        
    def __iter__(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {self.key_column} FROM {self.table_name}")
        keys = [row[0] for row in cursor.fetchall()]
        conn.close()
        return iter(keys)
        
    def __len__(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count
        
    def __contains__(self, key):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM {self.table_name} WHERE {self.key_column} = ?", (key,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
        
    def items(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {self.key_column}, data FROM {self.table_name}")
        rows = cursor.fetchall()
        conn.close()
        return [(r[0], json.loads(r[1])) for r in rows]
        
    def clear_older_than_24h(self):
        """Deletes database entries older than 24 hours."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.table_name} WHERE created_at < datetime('now', '-24 hours')")
        conn.commit()
        conn.close()
