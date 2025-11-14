"""
Supabase Client Integration
Provides a centralized Supabase client for database and auth operations
"""

import logging
import os
from functools import lru_cache

from supabase import Client, create_client

logger = logging.getLogger(__name__)


class SupabaseManager:
    """Manage Supabase client connection"""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self._client: Client | None = None
        self._admin_client: Client | None = None

    @property
    def client(self) -> Client:
        """Get Supabase client with anon key (for client-side operations)"""
        if not self._client:
            if not self.url or not self.anon_key:
                logger.warning("Supabase credentials not configured, using fallback")
                # Return a mock client or raise exception based on requirements
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

            self._client = create_client(self.url, self.anon_key)
            logger.info(f"Supabase client initialized for {self.url}")

        return self._client

    @property
    def admin_client(self) -> Client:
        """Get Supabase client with service role key (for admin operations)"""
        if not self._admin_client:
            if not self.url or not self.service_role_key:
                logger.warning("Supabase service role key not configured")
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

            self._admin_client = create_client(self.url, self.service_role_key)
            logger.info(f"Supabase admin client initialized for {self.url}")

        return self._admin_client

    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Try a simple query to test connection
            self.client.table("_test_").select("*").limit(1).execute()
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False


@lru_cache
def get_supabase_manager() -> SupabaseManager:
    """Get cached Supabase manager instance"""
    return SupabaseManager()


def get_supabase_client() -> Client:
    """Get Supabase client for dependency injection"""
    return get_supabase_manager().client


def get_supabase_admin_client() -> Client:
    """Get Supabase admin client for dependency injection"""
    return get_supabase_manager().admin_client
