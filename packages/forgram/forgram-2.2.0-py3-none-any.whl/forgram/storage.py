import json
import os
from typing import Any

class MemoryStorage:
    def __init__(self):
        self._data = {}
        
    def get(self, key: str) -> Any:
        return self._data.get(key)
    
    def set(self, key: str, value: Any):
        self._data[key] = value
    
    def delete(self, key: str):
        self._data.pop(key, None)
    
    def clear(self):
        self._data.clear()

class FileStorage:
    def __init__(self, filename: str = "storage.json"):
        self.filename = filename
        self._data = {}
        self._load()
        
    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self._data = json.load(f)
            except:
                self._data = {}
    
    def _save(self):
        with open(self.filename, 'w') as f:
            json.dump(self._data, f)
    
    def get(self, key: str) -> Any:
        return self._data.get(key)
    
    def set(self, key: str, value: Any):
        self._data[key] = value
        self._save()
    
    def delete(self, key: str):
        self._data.pop(key, None)
        self._save()
    
    def clear(self):
        self._data.clear()
        self._save()
