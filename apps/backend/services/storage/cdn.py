"""
CDN Manager for ToolBoxAI Educational Platform

Smart CDN management with image transformations, cache control,
signed URL generation, and performance optimization.

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import hashlib
import hmac
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from urllib.parse import urlencode, urlparse

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """CDN cache levels"""

    NO_CACHE = "no-cache"
    SHORT = "short"  # 5 minutes
    MEDIUM = "medium"  # 1 hour
    LONG = "long"  # 24 hours
    PERMANENT = "permanent"  # 30 days


class ImageFormat(str, Enum):
    """Supported image formats for transformation"""

    AUTO = "auto"
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    AVIF = "avif"


class ResizeMode(str, Enum):
    """Image resize modes"""

    FIT = "fit"
    FILL = "fill"
    CROP = "crop"
    SCALE = "scale"


@dataclass
class ImageTransformation:
    """Image transformation parameters"""

    width: int | None = None
    height: int | None = None
    quality: int | None = None
    format: ImageFormat | None = None
    resize_mode: ResizeMode = ResizeMode.FIT
    crop_gravity: str = "center"
    blur: int | None = None
    sharpen: int | None = None
    brightness: int | None = None
    contrast: int | None = None
    saturation: int | None = None
    rotate: int | None = None
    background_color: str | None = None

    def to_params(self) -> dict[str, str]:
        """Convert to URL parameters"""
        params = {}

        if self.width:
            params["w"] = str(self.width)
        if self.height:
            params["h"] = str(self.height)
        if self.quality:
            params["q"] = str(self.quality)
        if self.format and self.format != ImageFormat.AUTO:
            params["f"] = self.format.value
        if self.resize_mode != ResizeMode.FIT:
            params["fit"] = self.resize_mode.value
        if self.crop_gravity != "center":
            params["g"] = self.crop_gravity
        if self.blur:
            params["blur"] = str(self.blur)
        if self.sharpen:
            params["sharpen"] = str(self.sharpen)
        if self.brightness:
            params["brightness"] = str(self.brightness)
        if self.contrast:
            params["contrast"] = str(self.contrast)
        if self.saturation:
            params["saturation"] = str(self.saturation)
        if self.rotate:
            params["r"] = str(self.rotate)
        if self.background_color:
            params["bg"] = self.background_color

        return params


@dataclass
class CDNConfiguration:
    """CDN configuration settings"""

    base_url: str
    signing_key: str | None = None
    default_cache_level: CacheLevel = CacheLevel.MEDIUM
    enable_compression: bool = True
    enable_webp_conversion: bool = True
    enable_avif_conversion: bool = False
    max_age_seconds: dict[CacheLevel, int] = field(
        default_factory=lambda: {
            CacheLevel.NO_CACHE: 0,
            CacheLevel.SHORT: 300,
            CacheLevel.MEDIUM: 3600,
            CacheLevel.LONG: 86400,
            CacheLevel.PERMANENT: 2592000,
        }
    )
    regions: list[str] = field(default_factory=lambda: ["us-east-1", "eu-west-1"])
    custom_headers: dict[str, str] = field(default_factory=dict)


@dataclass
class CDNStats:
    """CDN performance statistics"""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    bandwidth_bytes: int = 0
    avg_response_time_ms: float = 0.0
    error_count: int = 0
    top_countries: list[dict[str, Any]] = field(default_factory=list)
    popular_files: list[dict[str, Any]] = field(default_factory=list)
    transformation_usage: dict[str, int] = field(default_factory=dict)

    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0

    @property
    def bandwidth_mb(self) -> float:
        """Get bandwidth in MB"""
        return self.bandwidth_bytes / (1024 * 1024)

    @property
    def bandwidth_gb(self) -> float:
        """Get bandwidth in GB"""
        return self.bandwidth_bytes / (1024 * 1024 * 1024)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": self.cache_hit_ratio,
            "bandwidth_bytes": self.bandwidth_bytes,
            "bandwidth_mb": self.bandwidth_mb,
            "bandwidth_gb": self.bandwidth_gb,
            "avg_response_time_ms": self.avg_response_time_ms,
            "error_count": self.error_count,
            "top_countries": self.top_countries,
            "popular_files": self.popular_files,
            "transformation_usage": self.transformation_usage,
        }


class CDNManager:
    """
    Smart CDN management for educational content delivery.

    Features:
    - Image transformations and optimization
    - Smart caching strategies
    - Signed URL generation
    - Performance monitoring
    - Geographic distribution
    - Bandwidth optimization
    """

    def __init__(self, config: CDNConfiguration):
        """
        Initialize CDN manager.

        Args:
            config: CDN configuration
        """
        self.config = config
        self._stats_cache: dict[str, CDNStats] = {}
        self._url_cache: dict[str, tuple[str, datetime]] = {}

        # Educational content-specific optimizations
        self.educational_presets = {
            "avatar": ImageTransformation(
                width=150,
                height=150,
                quality=85,
                format=ImageFormat.WEBP,
                resize_mode=ResizeMode.CROP,
            ),
            "thumbnail": ImageTransformation(
                width=300,
                height=200,
                quality=80,
                format=ImageFormat.WEBP,
                resize_mode=ResizeMode.FIT,
            ),
            "document_preview": ImageTransformation(
                width=800,
                height=600,
                quality=75,
                format=ImageFormat.WEBP,
                resize_mode=ResizeMode.FIT,
            ),
            "mobile_optimized": ImageTransformation(
                width=480,
                quality=70,
                format=ImageFormat.WEBP,
                resize_mode=ResizeMode.FIT,
            ),
        }

        logger.info(f"CDNManager initialized with base URL: {config.base_url}")

    async def get_optimized_url(
        self,
        storage_path: str,
        transformation: ImageTransformation | None = None,
        cache_level: CacheLevel | None = None,
        expires_in: int = 3600,
        organization_id: str | None = None,
    ) -> str:
        """
        Get optimized CDN URL with transformations.

        Args:
            storage_path: Original file storage path
            transformation: Image transformation parameters
            cache_level: Caching strategy
            expires_in: URL expiration time in seconds
            organization_id: Organization context

        Returns:
            str: Optimized CDN URL
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(storage_path, transformation, cache_level)
            if cache_key in self._url_cache:
                cached_url, cached_time = self._url_cache[cache_key]
                if datetime.utcnow() - cached_time < timedelta(minutes=5):
                    return cached_url

            # Build base URL
            base_url = f"{self.config.base_url.rstrip('/')}/{storage_path.lstrip('/')}"

            # Add transformation parameters
            params = {}
            if transformation:
                params.update(transformation.to_params())

            # Add cache control
            cache_level = cache_level or self.config.default_cache_level
            if cache_level != CacheLevel.NO_CACHE:
                params["cache"] = str(self.config.max_age_seconds[cache_level])

            # Add organization context
            if organization_id:
                params["org"] = organization_id

            # Add compression hints
            if self.config.enable_compression:
                params["compress"] = "1"

            # Build URL with parameters
            if params:
                url = f"{base_url}?{urlencode(params)}"
            else:
                url = base_url

            # Sign URL if key is available
            if self.config.signing_key:
                url = self._sign_url(url, expires_in)

            # Cache the result
            self._url_cache[cache_key] = (url, datetime.utcnow())

            logger.debug(f"Generated CDN URL: {storage_path} -> {url}")
            return url

        except Exception as e:
            logger.error(f"CDN URL generation failed: {e}")
            # Fallback to direct storage URL
            return f"{self.config.base_url.rstrip('/')}/{storage_path.lstrip('/')}"

    async def get_preset_url(
        self,
        storage_path: str,
        preset_name: str,
        cache_level: CacheLevel | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Get CDN URL with predefined transformation preset.

        Args:
            storage_path: Original file storage path
            preset_name: Transformation preset name
            cache_level: Caching strategy
            organization_id: Organization context

        Returns:
            str: CDN URL with preset transformations
        """
        if preset_name not in self.educational_presets:
            logger.warning(f"Unknown preset: {preset_name}")
            return await self.get_optimized_url(storage_path, cache_level=cache_level)

        transformation = self.educational_presets[preset_name]
        return await self.get_optimized_url(
            storage_path, transformation, cache_level, organization_id=organization_id
        )

    async def get_responsive_urls(
        self,
        storage_path: str,
        breakpoints: list[int] | None = None,
        cache_level: CacheLevel | None = None,
        organization_id: str | None = None,
    ) -> dict[str, str]:
        """
        Generate responsive image URLs for different screen sizes.

        Args:
            storage_path: Original file storage path
            breakpoints: List of width breakpoints
            cache_level: Caching strategy
            organization_id: Organization context

        Returns:
            dict[str, str]: Breakpoint name to URL mapping
        """
        breakpoints = breakpoints or [480, 768, 1024, 1920]
        responsive_urls = {}

        for width in breakpoints:
            transformation = ImageTransformation(
                width=width,
                quality=80,
                format=ImageFormat.WEBP,
                resize_mode=ResizeMode.FIT,
            )

            url = await self.get_optimized_url(
                storage_path,
                transformation,
                cache_level,
                organization_id=organization_id,
            )

            breakpoint_name = f"{width}w"
            responsive_urls[breakpoint_name] = url

        return responsive_urls

    async def invalidate_cache(
        self, storage_paths: list[str], organization_id: str | None = None
    ) -> bool:
        """
        Invalidate CDN cache for specified files.

        Args:
            storage_paths: List of file paths to invalidate
            organization_id: Organization context

        Returns:
            bool: True if invalidation successful
        """
        try:
            # Clear local cache
            for storage_path in storage_paths:
                keys_to_remove = [key for key in self._url_cache.keys() if storage_path in key]
                for key in keys_to_remove:
                    del self._url_cache[key]

            # Send invalidation request to CDN provider
            invalidation_result = await self._send_invalidation_request(
                storage_paths, organization_id
            )

            logger.info(f"Cache invalidated for {len(storage_paths)} files")
            return invalidation_result

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return False

    async def get_cdn_stats(
        self,
        organization_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> CDNStats:
        """
        Get CDN performance statistics.

        Args:
            organization_id: Organization identifier
            start_date: Statistics start date
            end_date: Statistics end date

        Returns:
            CDNStats: Performance statistics
        """
        try:
            # Check cache first
            if organization_id in self._stats_cache:
                return self._stats_cache[organization_id]

            # Set default date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            # Fetch statistics from CDN provider
            stats = await self._fetch_cdn_statistics(organization_id, start_date, end_date)

            # Cache the result
            self._stats_cache[organization_id] = stats

            return stats

        except Exception as e:
            logger.error(f"CDN stats retrieval failed: {e}")
            return CDNStats()

    async def optimize_delivery(
        self,
        storage_path: str,
        user_context: dict[str, Any],
        organization_id: str | None = None,
    ) -> str:
        """
        Optimize content delivery based on user context.

        Args:  # noqa: F841 - Reserved for geo-location data
            storage_path: File storage path
            user_context: User context (device, location, connection)
            organization_id: Organization context

        Returns:
            str: Optimized delivery URL
        """
        try:
            # Analyze user context
            device_type = user_context.get("device_type", "desktop")
            connection_speed = user_context.get("connection_speed", "fast")
            user_context.get("country", "US")

            # Choose optimization strategy
            transformation = None
            cache_level = self.config.default_cache_level

            if device_type == "mobile":
                # Mobile optimization
                transformation = ImageTransformation(
                    width=480,
                    quality=70 if connection_speed == "slow" else 80,
                    format=ImageFormat.WEBP,
                    resize_mode=ResizeMode.FIT,
                )
                cache_level = CacheLevel.LONG

            elif device_type == "tablet":
                # Tablet optimization
                transformation = ImageTransformation(
                    width=768,
                    quality=80,
                    format=ImageFormat.WEBP,
                    resize_mode=ResizeMode.FIT,
                )

            elif connection_speed == "slow":
                # Low bandwidth optimization
                transformation = ImageTransformation(
                    width=800,
                    quality=60,
                    format=ImageFormat.WEBP,
                    resize_mode=ResizeMode.FIT,
                )

            # Get optimized URL
            return await self.get_optimized_url(
                storage_path,
                transformation,
                cache_level,
                organization_id=organization_id,
            )

        except Exception as e:
            logger.error(f"Delivery optimization failed: {e}")
            return await self.get_optimized_url(storage_path, organization_id=organization_id)

    async def purge_organization_cache(self, organization_id: str) -> bool:
        """
        Purge all cached content for an organization.

        Args:
            organization_id: Organization identifier

        Returns:
            bool: True if purge successful
        """
        try:
            # Clear local caches
            keys_to_remove = [key for key in self._url_cache.keys() if organization_id in key]
            for key in keys_to_remove:
                del self._url_cache[key]

            self._stats_cache.pop(organization_id, None)

            # Send purge request to CDN
            purge_result = await self._send_purge_request(organization_id)

            logger.info(f"Organization cache purged: {organization_id}")
            return purge_result

        except Exception as e:
            logger.error(f"Cache purge failed for org {organization_id}: {e}")
            return False

    # Private helper methods

    def _generate_cache_key(
        self,
        storage_path: str,
        transformation: ImageTransformation | None,
        cache_level: CacheLevel | None,
    ) -> str:
        """Generate cache key for URL caching"""
        key_parts = [storage_path]

        if transformation:
            transform_params = transformation.to_params()
            key_parts.append(urlencode(sorted(transform_params.items())))

        if cache_level:
            key_parts.append(cache_level.value)

        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    def _sign_url(self, url: str, expires_in: int) -> str:
        """Generate signed URL with expiration"""
        if not self.config.signing_key:
            return url

        try:
            # Parse URL
            parsed = urlparse(url)

            # Generate expiration timestamp
            expires = int(time.time()) + expires_in

            # Create signature payload
            payload = f"{parsed.path}?{parsed.query}&expires={expires}"

            # Generate HMAC signature
            signature = hmac.new(
                self.config.signing_key.encode(), payload.encode(), hashlib.sha256
            ).hexdigest()

            # Add signature to URL
            separator = "&" if parsed.query else "?"
            return f"{url}{separator}expires={expires}&signature={signature}"

        except Exception as e:
            logger.error(f"URL signing failed: {e}")
            return url

    async def _send_invalidation_request(
        self, storage_paths: list[str], organization_id: str | None
    ) -> bool:
        """Send cache invalidation request to CDN provider"""
        try:
            # This would integrate with your CDN provider's API
            # For example, CloudFlare, AWS CloudFront, etc.

            {
                "files": storage_paths,
                "organization_id": organization_id,
                "timestamp": time.time(),
            }

            # Mock implementation
            logger.info(f"Mock CDN invalidation: {len(storage_paths)} files")
            return True

        except Exception as e:
            logger.error(f"CDN invalidation request failed: {e}")
            return False

    async def _send_purge_request(self, organization_id: str) -> bool:
        """Send cache purge request for organization"""
        try:
            # This would integrate with CDN provider's API
            logger.info(f"Mock CDN purge for organization: {organization_id}")
            return True

        except Exception as e:
            logger.error(f"CDN purge request failed: {e}")
            return False

    async def _fetch_cdn_statistics(
        self, organization_id: str, start_date: datetime, end_date: datetime
    ) -> CDNStats:
        """Fetch statistics from CDN provider"""
        try:
            # This would integrate with CDN provider's analytics API
            # Return mock statistics for now
            stats = CDNStats(
                total_requests=10000,
                cache_hits=8500,
                cache_misses=1500,
                bandwidth_bytes=50 * 1024 * 1024 * 1024,  # 50GB
                avg_response_time_ms=125.5,
                error_count=25,
                top_countries=[
                    {"country": "US", "requests": 6000},
                    {"country": "CA", "requests": 2000},
                    {"country": "UK", "requests": 1500},
                ],
                popular_files=[
                    {"path": "avatar.jpg", "requests": 1500},
                    {"path": "thumbnail.png", "requests": 1200},
                    {"path": "document.pdf", "requests": 800},
                ],
                transformation_usage={
                    "avatar": 3000,
                    "thumbnail": 2500,
                    "mobile_optimized": 2000,
                    "document_preview": 1500,
                },
            )

            return stats

        except Exception as e:
            logger.error(f"CDN statistics fetch failed: {e}")
            return CDNStats()

    def is_image_file(self, storage_path: str) -> bool:
        """Check if file is an image that can be transformed"""
        image_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".bmp",
            ".tiff",
            ".svg",
        }
        file_ext = storage_path.lower().split(".")[-1] if "." in storage_path else ""
        return f".{file_ext}" in image_extensions

    def get_cache_headers(self, cache_level: CacheLevel) -> dict[str, str]:
        """Get appropriate cache headers for the given cache level"""
        max_age = self.config.max_age_seconds[cache_level]

        headers = {}

        if cache_level == CacheLevel.NO_CACHE:
            headers.update(
                {
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
            )
        else:
            headers.update(
                {
                    "Cache-Control": f"public, max-age={max_age}",
                    "Expires": (datetime.utcnow() + timedelta(seconds=max_age)).strftime(
                        "%a, %d %b %Y %H:%M:%S GMT"
                    ),
                }
            )

        # Add custom headers
        headers.update(self.config.custom_headers)

        return headers
