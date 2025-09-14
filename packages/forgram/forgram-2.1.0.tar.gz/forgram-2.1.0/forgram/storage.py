"""
Forgram Storage Module
Advanced storage backends for states, cache, and data persistence
"""

import json
import pickle
import asyncio
import aiofiles
import sqlite3
import aiosqlite
from typing import Any, Dict, Optional, Union, List
from abc import ABC, abstractmethod
import time
import os
from pathlib import Path

class BaseStorage(ABC):
    """Base storage interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Any:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def clear(self):
        pass
    
    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        pass

class MemoryStorage(BaseStorage):
    """In-memory storage with TTL support"""
    
    def __init__(self):
        self._data: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Any:
        async with self._lock:
            if key not in self._data:
                return None
                
            item = self._data[key]
            
            # Check TTL
            if item.get('ttl') and time.time() > item['ttl']:
                del self._data[key]
                return None
                
            return item['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        async with self._lock:
            item = {'value': value}
            
            if ttl:
                item['ttl'] = time.time() + ttl
                
            self._data[key] = item
    
    async def delete(self, key: str):
        async with self._lock:
            self._data.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None
    
    async def clear(self):
        async with self._lock:
            self._data.clear()
    
    async def keys(self, pattern: str = "*") -> List[str]:
        async with self._lock:
            if pattern == "*":
                return list(self._data.keys())
            
            # Simple pattern matching
            import fnmatch
            return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]
    
    async def cleanup_expired(self):
        """Remove expired keys"""
        async with self._lock:
            now = time.time()
            expired_keys = []
            
            for key, item in self._data.items():
                if item.get('ttl') and now > item['ttl']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._data[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            'total_keys': len(self._data),
            'memory_usage': sum(len(str(item)) for item in self._data.values())
        }

class FileStorage(BaseStorage):
    """File-based storage with JSON serialization"""
    
    def __init__(self, file_path: str = "forgram_storage.json", auto_save: bool = True):
        self.file_path = Path(file_path)
        self.auto_save = auto_save
        self._data: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._loaded = False
    
    async def _load(self):
        """Load data from file"""
        if self._loaded:
            return
            
        if self.file_path.exists():
            try:
                async with aiofiles.open(self.file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    self._data = json.loads(content) if content else {}
            except Exception as e:
                print(f"Failed to load storage file: {e}")
                self._data = {}
        
        self._loaded = True
    
    async def _save(self):
        """Save data to file"""
        if not self.auto_save:
            return
            
        try:
            # Create directory if it doesn't exist
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(self.file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self._data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Failed to save storage file: {e}")
    
    async def get(self, key: str) -> Any:
        async with self._lock:
            await self._load()
            
            if key not in self._data:
                return None
                
            item = self._data[key]
            
            # Check TTL
            if item.get('ttl') and time.time() > item['ttl']:
                del self._data[key]
                await self._save()
                return None
                
            return item['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        async with self._lock:
            await self._load()
            
            item = {'value': value}
            
            if ttl:
                item['ttl'] = time.time() + ttl
                
            self._data[key] = item
            await self._save()
    
    async def delete(self, key: str):
        async with self._lock:
            await self._load()
            if key in self._data:
                del self._data[key]
                await self._save()
    
    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None
    
    async def clear(self):
        async with self._lock:
            self._data.clear()
            await self._save()
    
    async def keys(self, pattern: str = "*") -> List[str]:
        async with self._lock:
            await self._load()
            
            if pattern == "*":
                return list(self._data.keys())
            
            import fnmatch
            return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]
    
    async def force_save(self):
        """Force save to file"""
        async with self._lock:
            await self._save()

class SQLiteStorage(BaseStorage):
    """SQLite-based storage"""
    
    def __init__(self, db_path: str = "forgram.db", table_name: str = "storage"):
        self.db_path = db_path
        self.table_name = table_name
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _init_db(self):
        """Initialize database"""
        if self._initialized:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    ttl INTEGER,
                    created_at INTEGER NOT NULL
                )
            ''')
            await db.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_ttl 
                ON {self.table_name}(ttl)
            ''')
            await db.commit()
        
        self._initialized = True
    
    async def get(self, key: str) -> Any:
        async with self._lock:
            await self._init_db()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    f'SELECT value, ttl FROM {self.table_name} WHERE key = ?',
                    (key,)
                )
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                value_str, ttl = row
                
                # Check TTL
                if ttl and time.time() > ttl:
                    await db.execute(f'DELETE FROM {self.table_name} WHERE key = ?', (key,))
                    await db.commit()
                    return None
                
                # Deserialize value
                try:
                    return json.loads(value_str)
                except json.JSONDecodeError:
                    return value_str
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        async with self._lock:
            await self._init_db()
            
            # Serialize value
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                value_str = str(value)
            
            ttl_timestamp = None
            if ttl:
                ttl_timestamp = int(time.time() + ttl)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f'''
                    INSERT OR REPLACE INTO {self.table_name} 
                    (key, value, ttl, created_at) VALUES (?, ?, ?, ?)
                ''', (key, value_str, ttl_timestamp, int(time.time())))
                await db.commit()
    
    async def delete(self, key: str):
        async with self._lock:
            await self._init_db()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f'DELETE FROM {self.table_name} WHERE key = ?', (key,))
                await db.commit()
    
    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None
    
    async def clear(self):
        async with self._lock:
            await self._init_db()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f'DELETE FROM {self.table_name}')
                await db.commit()
    
    async def keys(self, pattern: str = "*") -> List[str]:
        async with self._lock:
            await self._init_db()
            
            async with aiosqlite.connect(self.db_path) as db:
                if pattern == "*":
                    cursor = await db.execute(f'SELECT key FROM {self.table_name}')
                else:
                    # SQLite GLOB pattern
                    cursor = await db.execute(
                        f'SELECT key FROM {self.table_name} WHERE key GLOB ?',
                        (pattern,)
                    )
                
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    
    async def cleanup_expired(self):
        """Remove expired keys"""
        async with self._lock:
            await self._init_db()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    f'DELETE FROM {self.table_name} WHERE ttl IS NOT NULL AND ttl < ?',
                    (int(time.time()),)
                )
                await db.commit()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(f'SELECT COUNT(*) FROM {self.table_name}')
            total_keys = (await cursor.fetchone())[0]
            
            cursor = await db.execute(
                f'SELECT COUNT(*) FROM {self.table_name} WHERE ttl IS NOT NULL AND ttl < ?',
                (int(time.time()),)
            )
            expired_keys = (await cursor.fetchone())[0]
            
            return {
                'total_keys': total_keys,
                'expired_keys': expired_keys,
                'db_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            }

class RedisStorage(BaseStorage):
    """Redis-based storage (requires aioredis)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 key_prefix: str = "forgram:", **redis_kwargs):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis_kwargs = redis_kwargs
        self._redis = None
    
    async def _get_redis(self):
        """Get Redis connection"""
        if self._redis is None:
            try:
                import aioredis
                self._redis = await aioredis.from_url(self.redis_url, **self.redis_kwargs)
            except ImportError:
                raise ImportError("aioredis is required for RedisStorage")
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Any:
        redis = await self._get_redis()
        value = await redis.get(self._make_key(key))
        
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.decode('utf-8')
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        redis = await self._get_redis()
        
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value)
        
        if ttl:
            await redis.setex(self._make_key(key), ttl, value_str)
        else:
            await redis.set(self._make_key(key), value_str)
    
    async def delete(self, key: str):
        redis = await self._get_redis()
        await redis.delete(self._make_key(key))
    
    async def exists(self, key: str) -> bool:
        redis = await self._get_redis()
        return await redis.exists(self._make_key(key))
    
    async def clear(self):
        redis = await self._get_redis()
        keys = await redis.keys(f"{self.key_prefix}*")
        if keys:
            await redis.delete(*keys)
    
    async def keys(self, pattern: str = "*") -> List[str]:
        redis = await self._get_redis()
        redis_keys = await redis.keys(f"{self.key_prefix}{pattern}")
        
        # Remove prefix from keys
        return [key.decode('utf-8')[len(self.key_prefix):] for key in redis_keys]
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()

class MultiTierStorage(BaseStorage):
    """Multi-tier storage with fallback support"""
    
    def __init__(self, primary: BaseStorage, secondary: BaseStorage = None):
        self.primary = primary
        self.secondary = secondary or MemoryStorage()
        
    async def get(self, key: str) -> Any:
        # Try primary storage first
        try:
            value = await self.primary.get(key)
            if value is not None:
                return value
        except Exception:
            pass
        
        # Fallback to secondary storage
        return await self.secondary.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        # Set in both storages
        try:
            await self.primary.set(key, value, ttl)
        except Exception:
            pass
        
        await self.secondary.set(key, value, ttl)
    
    async def delete(self, key: str):
        try:
            await self.primary.delete(key)
        except Exception:
            pass
        
        await self.secondary.delete(key)
    
    async def exists(self, key: str) -> bool:
        try:
            if await self.primary.exists(key):
                return True
        except Exception:
            pass
        
        return await self.secondary.exists(key)
    
    async def clear(self):
        try:
            await self.primary.clear()
        except Exception:
            pass
        
        await self.secondary.clear()
    
    async def keys(self, pattern: str = "*") -> List[str]:
        primary_keys = []
        secondary_keys = []
        
        try:
            primary_keys = await self.primary.keys(pattern)
        except Exception:
            pass
        
        try:
            secondary_keys = await self.secondary.keys(pattern)
        except Exception:
            pass
        
        # Combine and deduplicate
        return list(set(primary_keys + secondary_keys))

class StorageManager:
    """Manages multiple storage instances"""
    
    def __init__(self):
        self.storages: Dict[str, BaseStorage] = {}
        self.default_storage = None
        
    def add_storage(self, name: str, storage: BaseStorage, is_default: bool = False):
        """Add storage instance"""
        self.storages[name] = storage
        if is_default or self.default_storage is None:
            self.default_storage = storage
    
    def get_storage(self, name: str = None) -> BaseStorage:
        """Get storage by name or default"""
        if name is None:
            return self.default_storage
        return self.storages.get(name)
    
    async def close_all(self):
        """Close all storage connections"""
        for storage in self.storages.values():
            if hasattr(storage, 'close'):
                await storage.close()

# Default storage instances
memory_storage = MemoryStorage()
file_storage = FileStorage()

def create_storage_from_url(url: str) -> BaseStorage:
    """Create storage from URL"""
    if url.startswith('redis://'):
        return RedisStorage(url)
    elif url.startswith('sqlite://'):
        db_path = url.replace('sqlite://', '')
        return SQLiteStorage(db_path)
    elif url.startswith('file://'):
        file_path = url.replace('file://', '')
        return FileStorage(file_path)
    elif url == 'memory://':
        return MemoryStorage()
    else:
        raise ValueError(f"Unsupported storage URL: {url}")

async def migrate_storage(source: BaseStorage, target: BaseStorage, pattern: str = "*"):
    """Migrate data between storages"""
    keys = await source.keys(pattern)
    
    for key in keys:
        value = await source.get(key)
        if value is not None:
            await target.set(key, value)
    
    print(f"Migrated {len(keys)} keys from source to target storage")
