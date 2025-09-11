"""
Request/Response Compression Middleware for FastAPI

Comprehensive compression support:
- Gzip compression
- Brotli compression
- Deflate compression
- Content-encoding negotiation
- Selective compression based on content type
- Minimum size threshold
- Compression level configuration
"""

import gzip
import io
import logging
import zlib
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import Request, Response
from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

# Try to import brotli (optional dependency)
try:
    import brotli

    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    logger.warning(
        "Brotli compression not available. Install 'brotli' package for support."
    )


class CompressionConfig:
    """Configuration for compression middleware"""

    def __init__(
        self,
        minimum_size: int = 1024,  # Only compress responses larger than 1KB
        compression_level: int = 6,  # 1-9, where 9 is maximum compression
        compressible_types: Optional[Set[str]] = None,
        excluded_paths: Optional[Set[str]] = None,
        excluded_user_agents: Optional[Set[str]] = None,
        prefer_brotli: bool = True,
    ):
        self.minimum_size = minimum_size
        self.compression_level = compression_level

        # Default compressible content types
        self.compressible_types = compressible_types or {
            "text/html",
            "text/css",
            "text/plain",
            "text/xml",
            "text/javascript",
            "application/json",
            "application/javascript",
            "application/xml",
            "application/rss+xml",
            "application/atom+xml",
            "application/xhtml+xml",
            "application/x-font-ttf",
            "application/x-font-opentype",
            "application/vnd.ms-fontobject",
            "image/svg+xml",
            "image/x-icon",
        }

        self.excluded_paths = excluded_paths or {
            "/health",
            "/metrics",
            "/ws",  # WebSocket endpoints
        }

        # User agents that have issues with compression
        self.excluded_user_agents = excluded_user_agents or {
            "MSIE 6.0",
            "Mozilla/4.0",
        }

        self.prefer_brotli = prefer_brotli and BROTLI_AVAILABLE


class ContentEncoder:
    """Handles content encoding/compression"""

    @staticmethod
    def gzip_compress(data: bytes, level: int = 6) -> bytes:
        """Compress data using gzip"""
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=level) as gz:
            gz.write(data)
        return buffer.getvalue()

    @staticmethod
    def gzip_decompress(data: bytes) -> bytes:
        """Decompress gzip data"""
        return gzip.decompress(data)

    @staticmethod
    def deflate_compress(data: bytes, level: int = 6) -> bytes:
        """Compress data using deflate"""
        compress = zlib.compressobj(level, zlib.DEFLATED, -zlib.MAX_WBITS)
        compressed = compress.compress(data)
        compressed += compress.flush()
        return compressed

    @staticmethod
    def deflate_decompress(data: bytes) -> bytes:
        """Decompress deflate data"""
        return zlib.decompress(data, -zlib.MAX_WBITS)

    @staticmethod
    def brotli_compress(data: bytes, level: int = 6) -> bytes:
        """Compress data using brotli"""
        if not BROTLI_AVAILABLE:
            raise RuntimeError("Brotli compression not available")

        # Brotli uses quality level 0-11, map from 1-9
        quality = min(11, max(0, int(level * 11 / 9)))
        return brotli.compress(data, quality=quality)

    @staticmethod
    def brotli_decompress(data: bytes) -> bytes:
        """Decompress brotli data"""
        if not BROTLI_AVAILABLE:
            raise RuntimeError("Brotli decompression not available")
        return brotli.decompress(data)


class AcceptEncodingParser:
    """Parse and negotiate Accept-Encoding header"""

    @staticmethod
    def parse(accept_encoding: str) -> List[Tuple[str, float]]:
        """Parse Accept-Encoding header and return list of (encoding, quality)"""
        if not accept_encoding:
            return []

        encodings = []
        for part in accept_encoding.split(","):
            part = part.strip()
            if not part:
                continue

            # Split encoding and quality factor
            if ";" in part:
                encoding, params = part.split(";", 1)
                encoding = encoding.strip()

                # Extract quality factor
                quality = 1.0
                for param in params.split(";"):
                    param = param.strip()
                    if param.startswith("q="):
                        try:
                            quality = float(param[2:])
                        except ValueError:
                            quality = 1.0
            else:
                encoding = part
                quality = 1.0

            # Handle special cases
            if encoding == "*":
                # Wildcard means any encoding
                quality = quality * 0.01  # Lower priority
            elif encoding == "identity":
                # No encoding
                quality = quality * 0.001  # Lowest priority

            encodings.append((encoding.lower(), quality))

        # Sort by quality (descending)
        encodings.sort(key=lambda x: x[1], reverse=True)
        return encodings

    @staticmethod
    def negotiate(
        accept_encoding: str, available: List[str], prefer_brotli: bool = True
    ) -> Optional[str]:
        """Negotiate best encoding based on client preferences and available encodings"""
        client_encodings = AcceptEncodingParser.parse(accept_encoding)

        if not client_encodings:
            return None

        # If brotli is preferred and available, boost its quality
        if prefer_brotli and BROTLI_AVAILABLE:
            for i, (enc, quality) in enumerate(client_encodings):
                if enc == "br":
                    client_encodings[i] = (enc, quality * 1.1)
            client_encodings.sort(key=lambda x: x[1], reverse=True)

        # Find best match
        for encoding, quality in client_encodings:
            if quality <= 0:
                continue

            if encoding in available:
                return encoding
            elif encoding == "*" and available:
                # Wildcard accepts any available encoding
                return available[0]

        return None


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware for compressing HTTP responses"""

    def __init__(self, app: ASGIApp, config: Optional[CompressionConfig] = None):
        super().__init__(app)
        self.config = config or CompressionConfig()
        self.encoder = ContentEncoder()
        self.parser = AcceptEncodingParser()

        # Available compression methods
        self.available_encodings = ["gzip", "deflate"]
        if BROTLI_AVAILABLE:
            self.available_encodings.insert(0, "br")  # Prefer brotli

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and potentially compress response"""

        # Check if path is excluded
        if any(
            request.url.path.startswith(path) for path in self.config.excluded_paths
        ):
            return await call_next(request)

        # Check if user agent is excluded
        user_agent = request.headers.get("user-agent", "")
        if any(excluded in user_agent for excluded in self.config.excluded_user_agents):
            return await call_next(request)

        # Check if request has compressed body
        content_encoding = request.headers.get("content-encoding")
        if content_encoding:
            # Decompress request body if needed
            request = await self._decompress_request(request, content_encoding)

        # Get client's encoding preferences
        accept_encoding = request.headers.get("accept-encoding", "")

        # Process request
        response = await call_next(request)

        # Check if response should be compressed
        if not self._should_compress_response(response):
            return response

        # Negotiate encoding
        encoding = self.parser.negotiate(
            accept_encoding, self.available_encodings, self.config.prefer_brotli
        )

        if not encoding:
            return response

        # Compress response
        return await self._compress_response(response, encoding)

    async def _decompress_request(self, request: Request, encoding: str) -> Request:
        """Decompress request body"""
        try:
            body = await request.body()

            if encoding == "gzip":
                decompressed = self.encoder.gzip_decompress(body)
            elif encoding == "deflate":
                decompressed = self.encoder.deflate_decompress(body)
            elif encoding == "br" and BROTLI_AVAILABLE:
                decompressed = self.encoder.brotli_decompress(body)
            else:
                logger.warning(f"Unsupported content encoding: {encoding}")
                return request

            # Update request with decompressed body
            # This is a simplified approach; in production, you'd need proper request reconstruction
            request._body = decompressed

        except Exception as e:
            logger.error(f"Failed to decompress request: {e}")

        return request

    def _should_compress_response(self, response: Response) -> bool:
        """Check if response should be compressed"""

        # Don't compress if already compressed
        if "content-encoding" in response.headers:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if content_type not in self.config.compressible_types:
            return False

        # Check content length (if available)
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) < self.config.minimum_size:
                    return False
            except ValueError:
                pass

        return True

    async def _compress_response(self, response: Response, encoding: str) -> Response:
        """Compress response body"""
        try:
            # Read response body
            body = b""
            if hasattr(response, 'body_iterator'):
                async for chunk in response.body_iterator:
                    body += chunk
            elif hasattr(response, 'body'):
                body = response.body if isinstance(response.body, bytes) else response.body.encode()
            else:
                # If no body is available, return the response as-is
                return response

            # Check minimum size
            if len(body) < self.config.minimum_size:
                return response

            # Compress body
            if encoding == "gzip":
                compressed = self.encoder.gzip_compress(
                    body, self.config.compression_level
                )
            elif encoding == "deflate":
                compressed = self.encoder.deflate_compress(
                    body, self.config.compression_level
                )
            elif encoding == "br":
                compressed = self.encoder.brotli_compress(
                    body, self.config.compression_level
                )
            else:
                return response

            # Calculate compression ratio
            original_size = len(body)
            compressed_size = len(compressed)
            ratio = (
                (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            )

            # Only use compression if it's beneficial
            if compressed_size >= original_size:
                logger.debug(
                    f"Compression not beneficial for response ({ratio:.1f}% increase)"
                )
                return response

            # Create new response with compressed body
            # For Starlette Response objects, we need to return a new Response
            from starlette.responses import Response as StarletteResponse
            
            new_response = StarletteResponse(
                content=compressed,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            new_response.headers["content-encoding"] = encoding
            new_response.headers["content-length"] = str(compressed_size)

            # Add compression statistics header (optional, for debugging)
            new_response.headers["x-compression-ratio"] = f"{ratio:.1f}%"

            logger.debug(
                f"Compressed response with {encoding}: {original_size} -> {compressed_size} ({ratio:.1f}% reduction)"
            )
            
            return new_response

        except Exception as e:
            logger.error(f"Failed to compress response: {e}")
            # Return original response on error
            return response


class StreamingCompressionMiddleware:
    """Middleware for streaming compression of large responses"""

    def __init__(self, app: ASGIApp, config: Optional[CompressionConfig] = None):
        self.app = app
        self.config = config or CompressionConfig()
        self.encoder = ContentEncoder()
        self.parser = AcceptEncodingParser()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Parse headers
        headers = Headers(scope=scope)
        accept_encoding = headers.get("accept-encoding", "")

        # Negotiate encoding
        available = ["gzip", "deflate"]
        if BROTLI_AVAILABLE:
            available.insert(0, "br")

        encoding = self.parser.negotiate(
            accept_encoding, available, self.config.prefer_brotli
        )

        if not encoding:
            await self.app(scope, receive, send)
            return

        # Create compression context
        compressor = None

        async def send_compressed(message: Message) -> None:
            nonlocal compressor

            if message["type"] == "http.response.start":
                # Check if we should compress
                headers = MutableHeaders(scope=message)
                content_type = headers.get("content-type", "").split(";")[0].strip()

                if (
                    content_type in self.config.compressible_types
                    and "content-encoding" not in headers
                ):
                    # Add content-encoding header
                    headers["content-encoding"] = encoding

                    # Initialize compressor
                    if encoding == "gzip":
                        compressor = zlib.compressobj(
                            self.config.compression_level,
                            zlib.DEFLATED,
                            zlib.MAX_WBITS | 16,  # gzip format
                        )
                    elif encoding == "deflate":
                        compressor = zlib.compressobj(
                            self.config.compression_level,
                            zlib.DEFLATED,
                            -zlib.MAX_WBITS,
                        )
                    elif encoding == "br" and BROTLI_AVAILABLE:
                        quality = min(
                            11, max(0, int(self.config.compression_level * 11 / 9))
                        )
                        compressor = brotli.Compressor(quality=quality)

            elif message["type"] == "http.response.body":
                if compressor and message.get("body"):
                    # Compress body chunk
                    if encoding in ("gzip", "deflate"):
                        compressed = compressor.compress(message["body"])
                        if not message.get("more_body", False):
                            compressed += compressor.flush()
                    elif encoding == "br":
                        compressed = compressor.process(message["body"])
                        if not message.get("more_body", False):
                            compressed += compressor.finish()
                    else:
                        compressed = message["body"]

                    message = {**message, "body": compressed}

            await send(message)

        await self.app(scope, receive, send_compressed)


def create_compression_middleware(
    minimum_size: int = 1024, compression_level: int = 6, streaming: bool = False
) -> BaseHTTPMiddleware:
    """Create compression middleware with configuration"""

    config = CompressionConfig(
        minimum_size=minimum_size, compression_level=compression_level
    )

    if streaming:
        return StreamingCompressionMiddleware(config=config)
    else:
        return CompressionMiddleware(config=config)
