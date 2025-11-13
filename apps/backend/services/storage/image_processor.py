"""
Image Processor for ToolBoxAI Educational Platform

Comprehensive image processing including thumbnail generation, optimization,
format conversion, and responsive variants with EXIF data handling.

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import io
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    from PIL import ExifTags, Image, ImageFilter, ImageOps
    from PIL.ExifTags import TAGS

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("Pillow not available - image processing will be mocked")

logger = logging.getLogger(__name__)


class ImageFormat(str, Enum):
    """Supported image formats"""

    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"
    GIF = "GIF"
    BMP = "BMP"
    TIFF = "TIFF"


class ResizeMode(str, Enum):
    """Image resize modes"""

    FIT = "fit"  # Fit within dimensions maintaining aspect ratio
    FILL = "fill"  # Fill dimensions, may crop
    STRETCH = "stretch"  # Stretch to exact dimensions
    THUMBNAIL = "thumbnail"  # Create thumbnail with aspect ratio


@dataclass
class ImageVariant:
    """Processed image variant"""

    name: str
    data: bytes
    format: ImageFormat
    width: int
    height: int
    file_size: int
    quality: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio"""
        return self.width / self.height if self.height > 0 else 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "format": self.format.value,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
            "quality": self.quality,
            "aspect_ratio": self.aspect_ratio,
            "metadata": self.metadata,
        }


@dataclass
class ProcessingOptions:
    """Image processing options"""

    generate_thumbnails: bool = True
    optimize: bool = True
    strip_exif: bool = True
    convert_to_webp: bool = False
    max_width: int | None = None
    max_height: int | None = None
    quality: int = 85
    thumbnail_sizes: list[tuple[int, int]] = field(
        default_factory=lambda: [
            (150, 150),  # Small thumbnail
            (300, 300),  # Medium thumbnail
            (600, 600),  # Large thumbnail
        ]
    )
    responsive_sizes: list[int] = field(
        default_factory=lambda: [
            480,  # Mobile
            768,  # Tablet
            1024,  # Desktop
            1920,  # Large desktop
        ]
    )
    progressive_jpeg: bool = True
    lossless_webp: bool = False


class ImageProcessor:
    """
    Comprehensive image processing service.

    Features:
    - Thumbnail generation in multiple sizes
    - Image optimization and compression
    - Format conversion (JPEG, PNG, WebP)
    - Responsive image variants
    - EXIF data handling and privacy
    - Progressive JPEG support
    """

    def __init__(self, default_options: ProcessingOptions | None = None):
        """
        Initialize image processor.

        Args:
            default_options: Default processing options
        """
        self.default_options = default_options or ProcessingOptions()

        if not PIL_AVAILABLE:
            logger.warning("Pillow not available - using mock image processor")

        logger.info("ImageProcessor initialized")

    async def process_image(
        self,
        image_data: bytes,
        options: ProcessingOptions | None = None,
        generate_thumbnails: bool = True,
        optimize: bool = True,
    ) -> dict[str, ImageVariant]:
        """
        Process image with various optimizations and variants.

        Args:
            image_data: Original image data
            options: Processing options
            generate_thumbnails: Whether to generate thumbnails
            optimize: Whether to optimize images

        Returns:
            Dict[str, ImageVariant]: Dictionary of processed variants
        """
        options = options or self.default_options
        variants = {}

        try:
            if not PIL_AVAILABLE:
                return await self._mock_process_image(image_data, options)

            # Open and validate image
            original_image = await self._load_image(image_data)
            if not original_image:
                raise ValueError("Invalid image data")

            # Get original metadata
            metadata = await self._extract_metadata(original_image)

            # Process original image
            processed_original = await self._process_original(original_image, options, metadata)
            if processed_original:
                variants["original"] = processed_original

            # Generate thumbnails
            if generate_thumbnails and options.generate_thumbnails:
                thumbnails = await self._generate_thumbnails(original_image, options, metadata)
                variants.update(thumbnails)

            # Generate responsive variants
            responsive_variants = await self._generate_responsive_variants(
                original_image, options, metadata
            )
            variants.update(responsive_variants)

            # Convert to WebP if requested
            if options.convert_to_webp:
                webp_variants = await self._convert_to_webp(original_image, options, metadata)
                variants.update(webp_variants)

            logger.info(f"Image processing completed: {len(variants)} variants generated")

            return variants

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise ValueError(f"Image processing failed: {str(e)}")

    async def generate_thumbnail(
        self,
        image_data: bytes,
        size: tuple[int, int] = (300, 300),
        mode: ResizeMode = ResizeMode.THUMBNAIL,
        quality: int = 85,
    ) -> ImageVariant | None:
        """
        Generate a single thumbnail.

        Args:
            image_data: Original image data
            size: Thumbnail size (width, height)
            mode: Resize mode
            quality: JPEG quality

        Returns:
            ImageVariant: Thumbnail variant or None if failed
        """
        try:
            if not PIL_AVAILABLE:
                return await self._mock_generate_thumbnail(image_data, size, quality)

            original_image = await self._load_image(image_data)
            if not original_image:
                return None

            # Create thumbnail
            thumbnail = await self._resize_image(original_image, size, mode)

            # Convert to bytes
            thumbnail_data = await self._image_to_bytes(thumbnail, ImageFormat.JPEG, quality)

            return ImageVariant(
                name="thumbnail",
                data=thumbnail_data,
                format=ImageFormat.JPEG,
                width=thumbnail.width,
                height=thumbnail.height,
                file_size=len(thumbnail_data),
                quality=quality,
            )

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None

    async def optimize_image(
        self,
        image_data: bytes,
        max_width: int | None = None,
        max_height: int | None = None,
        quality: int = 85,
        format_hint: ImageFormat | None = None,
    ) -> ImageVariant | None:
        """
        Optimize image for web delivery.

        Args:
            image_data: Original image data
            max_width: Maximum width
            max_height: Maximum height
            quality: Compression quality
            format_hint: Preferred output format

        Returns:
            ImageVariant: Optimized image variant
        """
        try:
            if not PIL_AVAILABLE:
                return await self._mock_optimize_image(image_data, quality)

            original_image = await self._load_image(image_data)
            if not original_image:
                return None

            # Resize if needed
            if max_width or max_height:
                target_size = (
                    max_width or original_image.width,
                    max_height or original_image.height,
                )
                original_image = await self._resize_image(
                    original_image, target_size, ResizeMode.FIT
                )

            # Determine output format
            output_format = format_hint or self._get_optimal_format(original_image)

            # Optimize
            optimized_image = await self._optimize_for_web(original_image)

            # Convert to bytes
            optimized_data = await self._image_to_bytes(optimized_image, output_format, quality)

            return ImageVariant(
                name="optimized",
                data=optimized_data,
                format=output_format,
                width=optimized_image.width,
                height=optimized_image.height,
                file_size=len(optimized_data),
                quality=quality,
            )

        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return None

    async def extract_image_info(self, image_data: bytes) -> dict[str, Any]:
        """
        Extract comprehensive image information.

        Args:
            image_data: Image data

        Returns:
            Dict[str, Any]: Image information
        """
        try:
            if not PIL_AVAILABLE:
                return {"error": "Pillow not available"}

            image = await self._load_image(image_data)
            if not image:
                return {"error": "Invalid image"}

            # Basic info
            info = {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height,
                "aspect_ratio": image.width / image.height if image.height > 0 else 1.0,
                "file_size": len(image_data),
                "has_transparency": self._has_transparency(image),
                "color_mode": image.mode,
                "bit_depth": self._get_bit_depth(image),
            }

            # EXIF data
            exif_data = await self._extract_exif_data(image)
            if exif_data:
                info["exif"] = exif_data

            # Color analysis
            color_info = await self._analyze_colors(image)
            info.update(color_info)

            return info

        except Exception as e:
            logger.error(f"Image info extraction failed: {e}")
            return {"error": str(e)}

    # Private helper methods

    async def _load_image(self, image_data: bytes) -> Image.Image | None:
        """Load image from bytes"""
        try:
            return Image.open(io.BytesIO(image_data))
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return None

    async def _extract_metadata(self, image: Image.Image) -> dict[str, Any]:
        """Extract image metadata"""
        metadata = {
            "original_format": image.format,
            "original_mode": image.mode,
            "original_size": image.size,
            "has_transparency": self._has_transparency(image),
        }

        # Extract EXIF if present
        exif_data = await self._extract_exif_data(image)
        if exif_data:
            metadata["exif"] = exif_data

        return metadata

    async def _extract_exif_data(self, image: Image.Image) -> dict[str, Any] | None:
        """Extract EXIF data from image"""
        try:
            if not hasattr(image, "_getexif") or image._getexif() is None:
                return None

            exif_dict = image._getexif()
            if not exif_dict:
                return None

            exif_data = {}
            for tag_id, value in exif_dict.items():
                tag = TAGS.get(tag_id, tag_id)

                # Skip binary data and sensitive information
                if isinstance(value, bytes) or tag in ["MakerNote", "UserComment"]:
                    continue

                # Convert GPS info if present
                if tag == "GPSInfo":
                    exif_data["has_gps"] = True
                    # Don't store actual GPS coordinates for privacy
                    continue

                exif_data[tag] = str(value)

            return exif_data

        except Exception as e:
            logger.debug(f"EXIF extraction failed: {e}")
            return None

    async def _process_original(
        self, image: Image.Image, options: ProcessingOptions, metadata: dict[str, Any]
    ) -> ImageVariant | None:
        """Process the original image"""
        try:
            processed_image = image.copy()

            # Apply size limits
            if options.max_width or options.max_height:
                max_size = (
                    options.max_width or processed_image.width,
                    options.max_height or processed_image.height,
                )
                if processed_image.width > max_size[0] or processed_image.height > max_size[1]:
                    processed_image = await self._resize_image(
                        processed_image, max_size, ResizeMode.FIT
                    )

            # Optimize if requested
            if options.optimize:
                processed_image = await self._optimize_for_web(processed_image)

            # Strip EXIF if requested
            if options.strip_exif:
                processed_image = self._strip_exif(processed_image)

            # Determine format
            output_format = self._get_optimal_format(processed_image)

            # Convert to bytes
            image_data = await self._image_to_bytes(processed_image, output_format, options.quality)

            return ImageVariant(
                name="original",
                data=image_data,
                format=output_format,
                width=processed_image.width,
                height=processed_image.height,
                file_size=len(image_data),
                quality=options.quality,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Original image processing failed: {e}")
            return None

    async def _generate_thumbnails(
        self, image: Image.Image, options: ProcessingOptions, metadata: dict[str, Any]
    ) -> dict[str, ImageVariant]:
        """Generate thumbnail variants"""
        thumbnails = {}

        for i, size in enumerate(options.thumbnail_sizes):
            try:
                # Create thumbnail
                thumbnail = await self._resize_image(image, size, ResizeMode.THUMBNAIL)

                # Optimize thumbnail
                thumbnail = await self._optimize_for_web(thumbnail)

                # Strip EXIF
                if options.strip_exif:
                    thumbnail = self._strip_exif(thumbnail)

                # Convert to bytes
                thumbnail_data = await self._image_to_bytes(
                    thumbnail, ImageFormat.JPEG, options.quality
                )

                # Name based on size
                size_name = f"{size[0]}x{size[1]}"
                name = f"thumbnail_{size_name}"

                thumbnails[name] = ImageVariant(
                    name=name,
                    data=thumbnail_data,
                    format=ImageFormat.JPEG,
                    width=thumbnail.width,
                    height=thumbnail.height,
                    file_size=len(thumbnail_data),
                    quality=options.quality,
                )

            except Exception as e:
                logger.warning(f"Thumbnail generation failed for size {size}: {e}")

        return thumbnails

    async def _generate_responsive_variants(
        self, image: Image.Image, options: ProcessingOptions, metadata: dict[str, Any]
    ) -> dict[str, ImageVariant]:
        """Generate responsive image variants"""
        variants = {}

        for width in options.responsive_sizes:
            try:
                # Skip if image is smaller than target width
                if image.width <= width:
                    continue

                # Calculate proportional height
                aspect_ratio = image.height / image.width
                height = int(width * aspect_ratio)

                # Resize image
                responsive_image = await self._resize_image(image, (width, height), ResizeMode.FIT)

                # Optimize
                responsive_image = await self._optimize_for_web(responsive_image)

                # Strip EXIF
                if options.strip_exif:
                    responsive_image = self._strip_exif(responsive_image)

                # Convert to bytes
                responsive_data = await self._image_to_bytes(
                    responsive_image, ImageFormat.JPEG, options.quality
                )

                variants[f"responsive_{width}w"] = ImageVariant(
                    name=f"responsive_{width}w",
                    data=responsive_data,
                    format=ImageFormat.JPEG,
                    width=responsive_image.width,
                    height=responsive_image.height,
                    file_size=len(responsive_data),
                    quality=options.quality,
                )

            except Exception as e:
                logger.warning(f"Responsive variant generation failed for width {width}: {e}")

        return variants

    async def _convert_to_webp(
        self, image: Image.Image, options: ProcessingOptions, metadata: dict[str, Any]
    ) -> dict[str, ImageVariant]:
        """Convert image to WebP format"""
        variants = {}

        try:
            # Create WebP version
            webp_image = image.copy()

            # Optimize for WebP
            webp_image = await self._optimize_for_web(webp_image)

            # Convert to WebP
            webp_data = await self._image_to_bytes(
                webp_image, ImageFormat.WEBP, options.quality if not options.lossless_webp else None
            )

            variants["webp"] = ImageVariant(
                name="webp",
                data=webp_data,
                format=ImageFormat.WEBP,
                width=webp_image.width,
                height=webp_image.height,
                file_size=len(webp_data),
                quality=options.quality if not options.lossless_webp else None,
            )

        except Exception as e:
            logger.warning(f"WebP conversion failed: {e}")

        return variants

    async def _resize_image(
        self, image: Image.Image, size: tuple[int, int], mode: ResizeMode
    ) -> Image.Image:
        """Resize image with specified mode"""
        if mode == ResizeMode.THUMBNAIL:
            # Create thumbnail maintaining aspect ratio
            image_copy = image.copy()
            image_copy.thumbnail(size, Image.Resampling.LANCZOS)
            return image_copy

        elif mode == ResizeMode.FIT:
            # Fit within size maintaining aspect ratio
            return ImageOps.fit(image, size, Image.Resampling.LANCZOS)

        elif mode == ResizeMode.FILL:
            # Fill size, may crop
            return ImageOps.fit(image, size, Image.Resampling.LANCZOS, centering=(0.5, 0.5))

        elif mode == ResizeMode.STRETCH:
            # Stretch to exact size
            return image.resize(size, Image.Resampling.LANCZOS)

        else:
            raise ValueError(f"Unknown resize mode: {mode}")

    async def _optimize_for_web(self, image: Image.Image) -> Image.Image:
        """Optimize image for web delivery"""
        # Convert to RGB if necessary
        if image.mode in ("RGBA", "LA", "P"):
            if image.mode == "P" and "transparency" in image.info:
                # Preserve transparency for PNG
                image = image.convert("RGBA")
            elif image.mode in ("RGBA", "LA"):
                # Keep as is for transparency
                pass
            else:
                # Convert to RGB
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if len(image.split()) > 3 else None)
                image = background

        return image

    async def _image_to_bytes(
        self, image: Image.Image, format: ImageFormat, quality: int | None = None
    ) -> bytes:
        """Convert image to bytes"""
        output = io.BytesIO()

        save_kwargs = {}

        if format == ImageFormat.JPEG:
            save_kwargs.update(
                {"format": "JPEG", "quality": quality or 85, "optimize": True, "progressive": True}
            )
        elif format == ImageFormat.PNG:
            save_kwargs.update({"format": "PNG", "optimize": True})
        elif format == ImageFormat.WEBP:
            save_kwargs.update({"format": "WEBP", "quality": quality or 85, "optimize": True})
            if quality is None:  # Lossless
                save_kwargs["lossless"] = True
        else:
            save_kwargs["format"] = format.value

        image.save(output, **save_kwargs)
        return output.getvalue()

    def _get_optimal_format(self, image: Image.Image) -> ImageFormat:
        """Determine optimal output format"""
        # If image has transparency, use PNG
        if self._has_transparency(image):
            return ImageFormat.PNG

        # For simple images, use PNG
        if image.mode in ("1", "L", "P"):
            return ImageFormat.PNG

        # Default to JPEG
        return ImageFormat.JPEG

    def _has_transparency(self, image: Image.Image) -> bool:
        """Check if image has transparency"""
        return image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)

    def _get_bit_depth(self, image: Image.Image) -> int:
        """Get image bit depth"""
        mode_bits = {
            "1": 1,
            "L": 8,
            "P": 8,
            "RGB": 24,
            "RGBA": 32,
            "CMYK": 32,
            "YCbCr": 24,
            "LAB": 24,
            "HSV": 24,
        }
        return mode_bits.get(image.mode, 8)

    def _strip_exif(self, image: Image.Image) -> Image.Image:
        """Strip EXIF data from image"""
        try:
            # Create new image without EXIF
            data = list(image.getdata())
            image_without_exif = Image.new(image.mode, image.size)
            image_without_exif.putdata(data)
            return image_without_exif
        except Exception:
            return image

    async def _analyze_colors(self, image: Image.Image) -> dict[str, Any]:
        """Analyze image colors"""
        try:
            # Convert to RGB for analysis
            rgb_image = image.convert("RGB")

            # Get dominant colors (simplified)
            colors = rgb_image.getcolors(maxcolors=256 * 256 * 256)
            if colors:
                # Sort by frequency
                colors.sort(key=lambda x: x[0], reverse=True)
                dominant_color = colors[0][1]

                return {
                    "dominant_color": dominant_color,
                    "color_count": len(colors),
                    "is_grayscale": len(set(dominant_color)) == 1,
                }

        except Exception as e:
            logger.debug(f"Color analysis failed: {e}")

        return {}

    # Mock methods for when PIL is not available

    async def _mock_process_image(
        self, image_data: bytes, options: ProcessingOptions
    ) -> dict[str, ImageVariant]:
        """Mock image processing"""
        variants = {}

        # Mock original
        variants["original"] = ImageVariant(
            name="original",
            data=image_data,
            format=ImageFormat.JPEG,
            width=800,
            height=600,
            file_size=len(image_data),
            quality=85,
        )

        # Mock thumbnails
        for size in options.thumbnail_sizes:
            name = f"thumbnail_{size[0]}x{size[1]}"
            variants[name] = ImageVariant(
                name=name,
                data=image_data[:1000],  # Mock smaller data
                format=ImageFormat.JPEG,
                width=size[0],
                height=size[1],
                file_size=1000,
                quality=85,
            )

        return variants

    async def _mock_generate_thumbnail(
        self, image_data: bytes, size: tuple[int, int], quality: int
    ) -> ImageVariant:
        """Mock thumbnail generation"""
        return ImageVariant(
            name="thumbnail",
            data=image_data[:1000],
            format=ImageFormat.JPEG,
            width=size[0],
            height=size[1],
            file_size=1000,
            quality=quality,
        )

    async def _mock_optimize_image(self, image_data: bytes, quality: int) -> ImageVariant:
        """Mock image optimization"""
        return ImageVariant(
            name="optimized",
            data=image_data,
            format=ImageFormat.JPEG,
            width=800,
            height=600,
            file_size=len(image_data),
            quality=quality,
        )
