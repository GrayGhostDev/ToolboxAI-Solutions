"""Dependency injection container"""

from typing import Any, Dict, Type, Callable, Optional
import threading
import logging

logger = logging.getLogger(__name__)


class DIContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register singleton instance"""
        with self._lock:
            self._singletons[name] = instance
            logger.debug("Registered singleton: %s", name)
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """Register factory function"""
        with self._lock:
            self._factories[name] = factory
            logger.debug("Registered factory: %s", name)
    
    def register_class(self, name: str, cls: Type, *args, **kwargs) -> None:
        """Register class with constructor arguments"""
        def factory():
            return cls(*args, **kwargs)
        
        self.register_factory(name, factory)
    
    def get(self, name: str) -> Any:
        """Get service instance"""
        with self._lock:
            # Check singletons first
            if name in self._singletons:
                return self._singletons[name]
            
            # Check factories
            if name in self._factories:
                instance = self._factories[name]()
                # Cache as singleton if it's a class instance
                if hasattr(instance, '__class__'):
                    self._singletons[name] = instance
                return instance
            
            raise ValueError(f"Service '{name}' not registered")
    
    def has(self, name: str) -> bool:
        """Check if service is registered"""
        with self._lock:
            return name in self._singletons or name in self._factories
    
    def clear(self) -> None:
        """Clear all registrations"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()


class ServiceFactory:
    """Factory for creating configured services"""
    
    def __init__(self, container: DIContainer):
        self.container = container
    
    def create_plugin_manager(self) -> 'PluginManager':
        """Create configured PluginManager"""
        from server.roblox_server import PluginManager
        return PluginManager()
    
    def create_content_bridge(self) -> 'ContentBridge':
        """Create configured ContentBridge"""
        from server.roblox_server import ContentBridge
        return ContentBridge()
    
    def create_security_manager(self) -> 'PluginSecurity':
        """Create configured PluginSecurity"""
        from src.shared.utils.security import PluginSecurity
        from server.config import settings
        
        secret_key = getattr(settings, 'JWT_SECRET_KEY', 'default-secret')
        return PluginSecurity(secret_key)
    
    def create_cache(self) -> 'LRUCache':
        """Create configured LRUCache"""
        from src.shared.utils.cache import LRUCache
        from src.shared.utils.config import config_manager
        
        return LRUCache(
            max_size=config_manager.get('cache_max_size', 1000),
            ttl=config_manager.get('cache_ttl', 300),
            persist_file="content_cache.json"
        )
    
    def create_memory_store(self) -> 'PersistentMemoryStore':
        """Create configured PersistentMemoryStore"""
        from src.shared.utils.storage import PersistentMemoryStore
        from src.shared.utils.config import config_manager
        
        return PersistentMemoryStore(
            backup_file="roblox_server_backup.json",
            max_memory_mb=config_manager.get('max_memory_mb', 100)
        )


def setup_container() -> DIContainer:
    """Setup and configure DI container"""
    container = DIContainer()
    factory = ServiceFactory(container)
    
    # Register factories
    container.register_factory('plugin_manager', factory.create_plugin_manager)
    container.register_factory('content_bridge', factory.create_content_bridge)
    container.register_factory('security_manager', factory.create_security_manager)
    container.register_factory('cache', factory.create_cache)
    container.register_factory('memory_store', factory.create_memory_store)
    
    # Register singletons
    from src.shared.utils.monitoring import metrics, health_checker
    from src.shared.utils.config import config_manager
    
    container.register_singleton('metrics', metrics)
    container.register_singleton('health_checker', health_checker)
    container.register_singleton('config_manager', config_manager)
    
    logger.info("DI container configured with %d services", 
                len(container._factories) + len(container._singletons))
    
    return container


# Global container instance
container = setup_container()