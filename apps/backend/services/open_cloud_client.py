"""
Roblox Open Cloud API Client
Implements 2025 Open Cloud API v2 for asset management and data operations
"""

import aiohttp
import json
import base64
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
import logging

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class AssetType(str, Enum):
    """Roblox asset types for Open Cloud API"""

    MODEL = "Model"
    DECAL = "Decal"
    AUDIO = "Audio"
    MESH = "Mesh"
    ANIMATION = "Animation"
    PLUGIN = "Plugin"
    FONT_FAMILY = "FontFamily"
    VIDEO = "Video"


class CreationContext(BaseModel):
    """Asset creation context"""

    creator_type: str = Field(default="User", description="Creator type (User or Group)")
    creator_id: str = Field(..., description="Creator ID")
    expected_price: int = Field(default=0, description="Expected price (0 for free)")


class AssetDescription(BaseModel):
    """Asset description for creation"""

    asset_type: AssetType
    display_name: str = Field(..., max_length=50)
    description: str = Field(..., max_length=1000)
    creation_context: CreationContext


class DataStoreEntry(BaseModel):
    """DataStore entry model"""

    key: str
    value: Any
    metadata: Optional[Dict[str, Any]] = None
    user_ids: Optional[List[str]] = None  # For GDPR compliance
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None
    version: Optional[str] = None


class MessagingServiceMessage(BaseModel):
    """Message for Universe Messaging Service"""

    topic: str
    message: Dict[str, Any]


class PlacePublishRequest(BaseModel):
    """Request to publish a place"""

    universe_id: str
    place_id: str
    version_type: str = Field(default="Published", description="Published or Saved")


class OpenCloudAPIClient:
    """
    Roblox Open Cloud API client for 2025 v2 endpoints
    Handles assets, data stores, messaging, and place management
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "ROBLOX_API_KEY", "")
        self.base_url = "https://apis.roblox.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    # ==================== Asset Management ====================

    async def create_asset(self, asset: AssetDescription, file_content: bytes) -> Dict[str, Any]:
        """
        Create a new asset in Roblox

        Args:
            asset: Asset description and metadata
            file_content: Binary content of the asset

        Returns:
            Dict with asset creation response including asset ID
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        # Prepare multipart form data
        form_data = aiohttp.FormData()

        # Add asset configuration
        config = {
            "assetType": asset.asset_type.value,
            "displayName": asset.display_name,
            "description": asset.description,
            "creationContext": {
                "creator": {
                    "userId": (
                        asset.creation_context.creator_id
                        if asset.creation_context.creator_type == "User"
                        else None
                    ),
                    "groupId": (
                        asset.creation_context.creator_id
                        if asset.creation_context.creator_type == "Group"
                        else None
                    ),
                },
                "expectedPrice": asset.creation_context.expected_price,
            },
        }

        form_data.add_field("request", json.dumps(config), content_type="application/json")
        form_data.add_field("fileContent", file_content, filename="asset.rbxm")

        try:
            async with self.session.post(
                f"{self.base_url}/cloud/v2/assets",
                data=form_data,
                headers={"x-api-key": self.api_key},  # Don't include Content-Type for multipart
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Asset creation failed: {error_text}")
                    raise ValueError(f"Asset creation failed: {response.status}")

                result = await response.json()
                logger.info(f"Successfully created asset: {result.get('assetId')}")
                return result

        except Exception as e:
            logger.error(f"Error creating asset: {e}")
            raise

    async def update_asset(self, asset_id: str, file_content: bytes) -> Dict[str, Any]:
        """
        Update existing asset content

        Args:
            asset_id: ID of the asset to update
            file_content: New binary content

        Returns:
            Update response
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        form_data = aiohttp.FormData()
        form_data.add_field("fileContent", file_content, filename="asset.rbxm")

        try:
            async with self.session.patch(
                f"{self.base_url}/cloud/v2/assets/{asset_id}",
                data=form_data,
                headers={"x-api-key": self.api_key},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Asset update failed: {error_text}")
                    raise ValueError(f"Asset update failed: {response.status}")

                result = await response.json()
                logger.info(f"Successfully updated asset: {asset_id}")
                return result

        except Exception as e:
            logger.error(f"Error updating asset: {e}")
            raise

    async def get_asset(self, asset_id: str) -> Dict[str, Any]:
        """
        Get asset information

        Args:
            asset_id: Asset ID

        Returns:
            Asset information
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(
                f"{self.base_url}/cloud/v2/assets/{asset_id}", headers=self.headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to get asset: {error_text}")
                    raise ValueError(f"Failed to get asset: {response.status}")

                return await response.json()

        except Exception as e:
            logger.error(f"Error getting asset: {e}")
            raise

    # ==================== DataStore v2 ====================

    async def get_datastore_entry(
        self, universe_id: str, datastore_name: str, key: str, scope: str = "global"
    ) -> DataStoreEntry:
        """
        Get entry from DataStore

        Args:
            universe_id: Universe ID
            datastore_name: Name of the datastore
            key: Entry key
            scope: Datastore scope (default: global)

        Returns:
            DataStore entry
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(
                f"{self.base_url}/cloud/v2/universes/{universe_id}/data-stores/{datastore_name}/entries/{key}",
                params={"scope": scope},
                headers=self.headers,
            ) as response:
                if response.status == 404:
                    return None
                elif response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to get datastore entry: {error_text}")
                    raise ValueError(f"Failed to get datastore entry: {response.status}")

                data = await response.json()
                return DataStoreEntry(
                    key=key,
                    value=data.get("value"),
                    metadata=data.get("metadata"),
                    user_ids=data.get("userIds"),
                    created_time=data.get("createdTime"),
                    updated_time=data.get("updatedTime"),
                    version=data.get("version"),
                )

        except Exception as e:
            logger.error(f"Error getting datastore entry: {e}")
            raise

    async def set_datastore_entry(
        self, universe_id: str, datastore_name: str, entry: DataStoreEntry, scope: str = "global"
    ) -> Dict[str, Any]:
        """
        Set entry in DataStore

        Args:
            universe_id: Universe ID
            datastore_name: Name of the datastore
            entry: DataStore entry to set
            scope: Datastore scope (default: global)

        Returns:
            Operation result
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        payload = {
            "value": entry.value,
            "userIds": entry.user_ids or [],
            "metadata": entry.metadata or {},
        }

        try:
            async with self.session.post(
                f"{self.base_url}/cloud/v2/universes/{universe_id}/data-stores/{datastore_name}/entries/{entry.key}",
                params={"scope": scope},
                json=payload,
                headers=self.headers,
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    logger.error(f"Failed to set datastore entry: {error_text}")
                    raise ValueError(f"Failed to set datastore entry: {response.status}")

                result = await response.json()
                logger.info(f"Successfully set datastore entry: {entry.key}")
                return result

        except Exception as e:
            logger.error(f"Error setting datastore entry: {e}")
            raise

    async def delete_datastore_entry(
        self, universe_id: str, datastore_name: str, key: str, scope: str = "global"
    ) -> bool:
        """
        Delete entry from DataStore

        Args:
            universe_id: Universe ID
            datastore_name: Name of the datastore
            key: Entry key
            scope: Datastore scope (default: global)

        Returns:
            True if deletion successful
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.delete(
                f"{self.base_url}/cloud/v2/universes/{universe_id}/data-stores/{datastore_name}/entries/{key}",
                params={"scope": scope},
                headers=self.headers,
            ) as response:
                if response.status != 204:
                    error_text = await response.text()
                    logger.error(f"Failed to delete datastore entry: {error_text}")
                    return False

                logger.info(f"Successfully deleted datastore entry: {key}")
                return True

        except Exception as e:
            logger.error(f"Error deleting datastore entry: {e}")
            return False

    # ==================== Ordered DataStore ====================

    async def get_ordered_datastore_entries(
        self,
        universe_id: str,
        datastore_name: str,
        scope: str = "global",
        order: str = "desc",
        limit: int = 10,
    ) -> List[DataStoreEntry]:
        """
        Get entries from Ordered DataStore (for leaderboards)

        Args:
            universe_id: Universe ID
            datastore_name: Name of the ordered datastore
            scope: Datastore scope
            order: Sort order (asc or desc)
            limit: Maximum number of entries

        Returns:
            List of ordered entries
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(
                f"{self.base_url}/cloud/v2/universes/{universe_id}/ordered-data-stores/{datastore_name}/entries",
                params={"scope": scope, "order": order, "limit": limit},
                headers=self.headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to get ordered datastore entries: {error_text}")
                    raise ValueError(f"Failed to get ordered entries: {response.status}")

                data = await response.json()
                entries = []
                for item in data.get("entries", []):
                    entries.append(
                        DataStoreEntry(
                            key=item.get("key"),
                            value=item.get("value"),
                            metadata=item.get("metadata"),
                        )
                    )

                return entries

        except Exception as e:
            logger.error(f"Error getting ordered datastore entries: {e}")
            raise

    # ==================== Universe Messaging Service ====================

    async def publish_message(
        self, universe_id: str, message: MessagingServiceMessage
    ) -> Dict[str, Any]:
        """
        Publish message to Universe Messaging Service

        Args:
            universe_id: Universe ID
            message: Message to publish

        Returns:
            Publication result
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        payload = {
            "topic": message.topic,
            "message": json.dumps(message.message),  # Message must be JSON string
        }

        try:
            async with self.session.post(
                f"{self.base_url}/cloud/v2/universes/{universe_id}/messaging-service/publish",
                json=payload,
                headers=self.headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to publish message: {error_text}")
                    raise ValueError(f"Failed to publish message: {response.status}")

                result = await response.json()
                logger.info(f"Successfully published message to topic: {message.topic}")
                return result

        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise

    # ==================== Place Publishing ====================

    async def publish_place(self, request: PlacePublishRequest) -> Dict[str, Any]:
        """
        Publish a place to Roblox

        Args:
            request: Place publish request

        Returns:
            Publication result
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        payload = {"versionType": request.version_type}

        try:
            async with self.session.post(
                f"{self.base_url}/cloud/v2/universes/{request.universe_id}/places/{request.place_id}/versions",
                json=payload,
                headers=self.headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to publish place: {error_text}")
                    raise ValueError(f"Failed to publish place: {response.status}")

                result = await response.json()
                logger.info(f"Successfully published place: {request.place_id}")
                return result

        except Exception as e:
            logger.error(f"Error publishing place: {e}")
            raise

    # ==================== Batch Operations ====================

    async def batch_create_assets(
        self, assets: List[tuple[AssetDescription, bytes]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple assets in batch

        Args:
            assets: List of (AssetDescription, file_content) tuples

        Returns:
            List of creation results
        """
        results = []
        for asset_desc, content in assets:
            try:
                result = await self.create_asset(asset_desc, content)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to create asset {asset_desc.display_name}: {e}")
                results.append({"error": str(e), "asset": asset_desc.display_name})

        return results

    async def batch_set_datastore_entries(
        self, universe_id: str, datastore_name: str, entries: List[DataStoreEntry]
    ) -> List[Dict[str, Any]]:
        """
        Set multiple datastore entries in batch

        Args:
            universe_id: Universe ID
            datastore_name: DataStore name
            entries: List of entries to set

        Returns:
            List of operation results
        """
        results = []
        for entry in entries:
            try:
                result = await self.set_datastore_entry(universe_id, datastore_name, entry)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to set entry {entry.key}: {e}")
                results.append({"error": str(e), "key": entry.key})

        return results


# Global instance
open_cloud_client = OpenCloudAPIClient()
