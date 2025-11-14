"""Mitigate OpenAI 1.109+ strict httpx client checks for LangChain."""

from __future__ import annotations

import logging
import os
from typing import Any

try:  # httpx is a direct dependency of the project
    import httpx
except ImportError:  # pragma: no cover - should not happen in runtime envs
    httpx = None

logger = logging.getLogger(__name__)

_DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"


def _resolve_timeout(value: Any) -> float:
    """Convert configured timeout to float seconds."""

    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            logger.debug("Invalid timeout %s provided by caller", value)

    env_timeout = os.getenv("OPENAI_HTTP_TIMEOUT", "60")
    try:
        return float(env_timeout)
    except ValueError:
        logger.debug("Invalid OPENAI_HTTP_TIMEOUT=%s; falling back to 60s", env_timeout)
        return 60.0


def _resolve_base_url(candidate: str | None) -> str:
    """Pick the effective base URL for OpenAI requests."""

    return candidate or os.getenv("OPENAI_API_BASE") or _DEFAULT_OPENAI_BASE


def _build_sync_client(base_url: str | None, timeout: Any) -> httpx.Client:
    """Create a plain httpx.Client accepted by openai>=1.109."""

    return httpx.Client(
        base_url=_resolve_base_url(base_url),
        timeout=_resolve_timeout(timeout),
        follow_redirects=True,
    )


def _build_async_client(base_url: str | None, timeout: Any) -> httpx.AsyncClient:
    """Create a plain httpx.AsyncClient accepted by openai>=1.109."""

    return httpx.AsyncClient(
        base_url=_resolve_base_url(base_url),
        timeout=_resolve_timeout(timeout),
        follow_redirects=True,
    )


def patch_langchain_openai_http_client() -> bool:
    """Replace langchain-openai's wrappers with vanilla httpx clients."""

    if httpx is None:
        logger.warning("httpx not installed; cannot patch langchain-openai clients")
        return False

    try:
        from langchain_openai.chat_models import _client_utils
    except ImportError:
        logger.debug("langchain_openai not present; skipping http client patch")
        return False

    _client_utils._get_default_httpx_client = _build_sync_client  # type: ignore[attr-defined]
    _client_utils._get_default_async_httpx_client = _build_async_client  # type: ignore[attr-defined]

    logger.info(
        "Applied langchain-openai httpx client patch for OpenAI>=1.109 compatibility",
    )
    return True


__all__ = ["patch_langchain_openai_http_client"]
