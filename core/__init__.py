"""
Core business logic package for ToolboxAI Solutions
"""

__version__ = "1.0.0"
__all__ = [
    "agents",
    "coordinators",
    "database",
    "integrations",
    "mcp",
    "performance",
    "plugin_system",
    "sparc",
    "swarm",
    "types",
    "utils",
]


def _apply_runtime_patches() -> None:
    """Apply compatibility patches that must run before importing subpackages."""

    try:
        from core.patches import apply_runtime_patches

        apply_runtime_patches()
    except Exception as patch_error:  # pragma: no cover - defensive logging
        import logging

        logging.getLogger(__name__).warning(
            "Runtime patch initialization failed: %s",
            patch_error,
        )


_apply_runtime_patches()
