"""Enhanced in-memory storage with persistence"""

import json
import os
import threading
import time
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PersistentMemoryStore:
    """In-memory storage with disk persistence and monitoring"""
    
    def __init__(self, backup_file: str = "memory_store_backup.json", 
                 max_memory_mb: int = 100, backup_interval: int = 300):
        self.data: Dict[str, Any] = {}
        self.backup_file = backup_file
        self.max_memory_mb = max_memory_mb
        self.backup_interval = backup_interval
        self._lock = threading.RLock()
        self._last_backup = 0
        self._load_backup()
        self._start_backup_thread()
    
    def set(self, key: str, value: Any) -> None:
        """Set value with memory monitoring"""
        with self._lock:
            self.data[key] = value
            self._check_memory_limit()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value"""
        with self._lock:
            return self.data.get(key, default)
    
    def delete(self, key: str) -> bool:
        """Delete key"""
        with self._lock:
            if key in self.data:
                del self.data[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all data"""
        with self._lock:
            self.data.clear()
    
    def size(self) -> int:
        """Get data size"""
        with self._lock:
            return len(self.data)
    
    def _check_memory_limit(self) -> None:
        """Check and enforce memory limits"""
        try:
            import sys
            size_mb = sys.getsizeof(self.data) / (1024 * 1024)
            if size_mb > self.max_memory_mb:
                # Simple LRU: remove oldest 25% of items
                items_to_remove = len(self.data) // 4
                keys_to_remove = list(self.data.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del self.data[key]
                logger.warning("Memory limit exceeded, removed %d items", items_to_remove)
        except Exception as e:
            logger.error("Memory check failed: %s", e)
    
    def _load_backup(self) -> None:
        """Load data from backup file"""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info("Loaded backup from %s", self.backup_file)
        except Exception as e:
            logger.error("Failed to load backup: %s", e)
            self.data = {}
    
    def _save_backup(self) -> None:
        """Save data to backup file"""
        try:
            with self._lock:
                with open(self.backup_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2, default=str)
                self._last_backup = time.time()
                logger.debug("Saved backup to %s", self.backup_file)
        except Exception as e:
            logger.error("Failed to save backup: %s", e)
    
    def _start_backup_thread(self) -> None:
        """Start periodic backup thread"""
        def backup_loop():
            while True:
                time.sleep(self.backup_interval)
                if time.time() - self._last_backup > self.backup_interval:
                    self._save_backup()
        
        backup_thread = threading.Thread(target=backup_loop, daemon=True)
        backup_thread.start()