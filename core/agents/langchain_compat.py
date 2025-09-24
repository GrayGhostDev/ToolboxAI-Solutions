"""
LangChain Pydantic v2 Compatibility Layer
Phase 1.5 Temporary Fix for LLMChain compatibility issues

This module provides compatibility adapters to resolve Pydantic v2
conflicts with LangChain 0.3.x components.
"""

import sys
from typing import Any, Dict, Type
import warnings

# Suppress deprecation warnings during compatibility phase
warnings.filterwarnings("ignore", message=".*__init_subclass__.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain.*")

def patch_llmchain_init_subclass():
    """
    Patch LLMChain to handle Pydantic v2 __init_subclass__ signature changes.

    This is a temporary fix for Phase 1.5 - full migration planned for Phase 2.
    """
    try:
        from langchain.chains.llm import LLMChain

        # Store original method if it exists
        original_init_subclass = getattr(LLMChain, '__init_subclass__', None)

        @classmethod
        def patched_init_subclass(cls, **kwargs):
            """Patched __init_subclass__ that filters Pydantic v2 kwargs"""
            # Remove Pydantic v2 specific kwargs that cause issues
            filtered_kwargs = {
                k: v for k, v in kwargs.items()
                if k not in ['__pydantic_extra__', '__pydantic_fields_set__', '__pydantic_private__']
            }

            # Call original if it exists, otherwise call super
            if original_init_subclass:
                try:
                    return original_init_subclass(**filtered_kwargs)
                except TypeError:
                    # If original fails, try parent class
                    pass

            # Try parent class with filtered kwargs
            try:
                return super(LLMChain, cls).__init_subclass__(**filtered_kwargs)
            except TypeError:
                # Last resort: call without kwargs
                return super(LLMChain, cls).__init_subclass__()

        # Apply the patch
        LLMChain.__init_subclass__ = patched_init_subclass

        return True

    except ImportError:
        # LangChain not available
        return False
    except Exception as e:
        print(f"Warning: Failed to patch LLMChain: {e}")
        return False

def patch_pydantic_metaclass():
    """
    Patch Pydantic metaclass issues with LangChain inheritance.
    """
    try:
        from pydantic._internal._model_construction import ModelMetaclass

        # Store original __new__
        original_new = ModelMetaclass.__new__

        def patched_new(mcs, cls_name, bases, namespace, **kwargs):
            """Patched metaclass __new__ that handles LangChain classes"""

            # Check if this is a LangChain class
            is_langchain_class = any(
                'langchain' in getattr(base, '__module__', '')
                for base in bases
            )

            if is_langchain_class:
                # Filter out problematic kwargs for LangChain classes
                safe_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k not in ['output_key', '__config__']
                }
                kwargs = safe_kwargs

            try:
                return original_new(mcs, cls_name, bases, namespace, **kwargs)
            except TypeError as e:
                if "__init_subclass__" in str(e):
                    # Try without kwargs
                    return original_new(mcs, cls_name, bases, namespace)
                raise

        ModelMetaclass.__new__ = patched_new
        return True

    except Exception as e:
        print(f"Warning: Failed to patch Pydantic metaclass: {e}")
        return False

def apply_compatibility_patches():
    """
    Apply all compatibility patches for Phase 1.5.

    Returns:
        bool: True if patches applied successfully
    """
    success = True

    print("🔧 Applying LangChain/Pydantic v2 compatibility patches...")

    # Patch 1: LLMChain __init_subclass__
    if patch_llmchain_init_subclass():
        print("✅ LLMChain __init_subclass__ patch applied")
    else:
        print("❌ LLMChain patch failed")
        success = False

    # Patch 2: Pydantic metaclass
    if patch_pydantic_metaclass():
        print("✅ Pydantic metaclass patch applied")
    else:
        print("❌ Pydantic metaclass patch failed")
        success = False

    if success:
        print("🎉 All compatibility patches applied successfully")
    else:
        print("⚠️  Some patches failed - functionality may be limited")

    return success

# Auto-apply patches when module is imported
if __name__ != "__main__":
    apply_compatibility_patches()