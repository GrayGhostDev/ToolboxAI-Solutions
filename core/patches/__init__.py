"""Runtime patches to keep third-party integrations stable."""

from __future__ import annotations

import logging

from core.patches.langchain_openai_http_client import (
    patch_langchain_openai_http_client,
)

logger = logging.getLogger(__name__)

_PATCHES_APPLIED = False


def apply_runtime_patches() -> None:
    """Apply all safe-to-run patches once per process."""

    global _PATCHES_APPLIED

    if _PATCHES_APPLIED:
        return

    patched_openai = patch_langchain_openai_http_client()

    if patched_openai:
        logger.debug("Patched langchain-openai HTTP client compatibility")

    _PATCHES_APPLIED = True


__all__ = ["apply_runtime_patches"]
