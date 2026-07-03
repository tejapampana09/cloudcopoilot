import os
import json
import collections.abc
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Dummy DB_PATH to prevent import crashes in main.py
DB_PATH = "postgresql"

# Configure SQLAlchemy connection with SQLite fallback
db_url = settings.DATABASE_URL
is_sqlite = not db_url or "postgresql" not in db_url

if is_sqlite and not db_url.startswith("sqlite://"):
    DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cloudpilot.db")
    db_url = f"sqlite:///{DB_FILE}"

if "sqlite" in db_url:
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        db_url,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initializes database tables if they do not exist."""
    # Importing models here registers them on Base.metadata
    from app.models.user import User
    from app.models.analysis import Analysis, Generation, RepositoryChunk
    Base.metadata.create_all(bind=engine)

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

class PostgresDict(collections.abc.MutableMapping):
    """A dictionary-like interface mapping read/write operations to PostgreSQL tables."""
    def __init__(self, table_name, key_column):
        self.table_name = table_name
        self.key_column = key_column
        
    def write_back(self, key, val_dict):
        """Serializes and writes/updates data to PostgreSQL."""
        db = SessionLocal()
        try:
            data_str = json.dumps(val_dict)
            status = val_dict.get("status", "pending")
            user_id = val_dict.get("user_id")
            # PostgreSQL upsert query: ON CONFLICT updates the data/status/user_id
            db.execute(text(f"""
                INSERT INTO {self.table_name} ({self.key_column}, data, status, user_id)
                VALUES (:key, :data, :status, :user_id)
                ON CONFLICT ({self.key_column})
                DO UPDATE SET data = EXCLUDED.data, status = EXCLUDED.status, user_id = EXCLUDED.user_id
            """), {"key": key, "data": data_str, "status": status, "user_id": user_id})
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
        
    def __getitem__(self, key):
        db = SessionLocal()
        try:
            result = db.execute(text(f"SELECT data FROM {self.table_name} WHERE {self.key_column} = :key"), {"key": key}).fetchone()
            if not result:
                raise KeyError(key)
            return PersistentDict(key, self, json.loads(result[0]))
        finally:
            db.close()
        
    def __setitem__(self, key, value):
        self.write_back(key, value)
        
    def __delitem__(self, key):
        db = SessionLocal()
        try:
            db.execute(text(f"DELETE FROM {self.table_name} WHERE {self.key_column} = :key"), {"key": key})
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
        
    def __iter__(self):
        db = SessionLocal()
        try:
            result = db.execute(text(f"SELECT {self.key_column} FROM {self.table_name}")).fetchall()
            return iter([r[0] for r in result])
        finally:
            db.close()
        
    def __len__(self):
        db = SessionLocal()
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {self.table_name}")).scalar()
            return count
        finally:
            db.close()
        
    def __contains__(self, key):
        db = SessionLocal()
        try:
            result = db.execute(text(f"SELECT 1 FROM {self.table_name} WHERE {self.key_column} = :key"), {"key": key}).fetchone()
            return result is not None
        finally:
            db.close()

    def get(self, key, default=None):
        """Returns item by key, or default if not found. Prevents AttributeError on dict.get() calls."""
        try:
            return self[key]
        except KeyError:
            return default
        
    def items(self):
        db = SessionLocal()
        try:
            rows = db.execute(text(f"SELECT {self.key_column}, data FROM {self.table_name}")).fetchall()
            return [(r[0], json.loads(r[1])) for r in rows]
        finally:
            db.close()
        
    def clear_older_than_24h(self):
        """Deletes database entries older than 24 hours."""
        db = SessionLocal()
        try:
            db.execute(text(f"DELETE FROM {self.table_name} WHERE created_at < NOW() - INTERVAL '24 hours'"))
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

# Alias for backward compatibility
SqliteDict = PostgresDict
