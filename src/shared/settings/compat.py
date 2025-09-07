"""Compatibility layer for pydantic v2 (pydantic-settings) and pydantic v1.

Exports: BaseSettings, SettingsConfigDict, Field, field_validator
so callers can import from toolboxai_settings.compat when needed.
"""

from typing import Any

try:
    # pydantic v2
    from pydantic import Field, field_validator  # type: ignore
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore

    PREFERRED = "v2"
except ImportError:
    # fallback to pydantic v1
    from pydantic import BaseSettings, Field  # type: ignore
    from pydantic import validator as field_validator  # type: ignore

    class SettingsConfigDict(dict):
        """Lightweight shim for pydantic v1 Config mapping."""

        pass

    PREFERRED = "v1"

__all__ = [
    "Field",
    "field_validator",
    "BaseSettings",
    "SettingsConfigDict",
    "PREFERRED",
]
