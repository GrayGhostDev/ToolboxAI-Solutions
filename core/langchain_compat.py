"""
LangChain Compatibility Layer

Provides compatibility shims for different LangChain versions.
Handles the LanguageModelInput import issue between versions.
"""

import sys
from typing import Any

# Patch the langchain_core.language_models module to include LanguageModelInput
def patch_langchain_imports():
    """Patch LangChain imports for compatibility."""
    try:
        from langchain_core import language_models
        
        # Check if LanguageModelInput is missing
        if not hasattr(language_models, 'LanguageModelInput'):
            # Create a type alias for compatibility
            if hasattr(language_models, 'LanguageModelLike'):
                # Use LanguageModelLike as the base
                language_models.LanguageModelInput = language_models.LanguageModelLike
            else:
                # Create a generic type
                language_models.LanguageModelInput = Any
            
            # Also add to the module's __all__ if it exists
            if hasattr(language_models, '__all__'):
                if 'LanguageModelInput' not in language_models.__all__:
                    language_models.__all__.append('LanguageModelInput')
        
        return True
    except ImportError:
        return False

# Apply the patch when this module is imported
patch_langchain_imports()

# Export common LangChain imports with compatibility
try:
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    
    __all__ = [
        'ChatOpenAI',
        'AzureChatOpenAI',
        'HumanMessage',
        'AIMessage',
        'SystemMessage',
        'ChatPromptTemplate',
        'MessagesPlaceholder',
        'StrOutputParser',
        'RunnablePassthrough',
    ]
except ImportError as e:
    print(f"Warning: Some LangChain imports failed: {e}")
    __all__ = []