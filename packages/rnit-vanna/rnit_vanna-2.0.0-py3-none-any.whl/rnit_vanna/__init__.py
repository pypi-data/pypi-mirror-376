"""
RNIT Vanna - Enhanced wrapper for Vanna SQL generation library
Always uses the latest official Vanna version with custom utilities
"""

__version__ = "2.0.0"
__author__ = "RNIT"

# Import everything from official Vanna
# This ensures backward compatibility
try:
    from vanna import *
    from vanna.openai import OpenAI_Chat
    from vanna.chromadb import ChromaDB_VectorStore
    from vanna.flask import VannaFlaskApp
except ImportError as e:
    raise ImportError(
        "Official Vanna package not found. "
        "It will be automatically installed when you install rnit-vanna. "
        f"Error: {e}"
    )

# Import RNIT custom enhancements
from .enhanced import RNITVanna, VannaQuickStart
from .utilities import DatabaseInspector, TrainingGenerator, QueryOptimizer

# Define what's available when someone does "from rnit_vanna import *"
__all__ = [
    # Original Vanna exports (maintained for compatibility)
    'OpenAI_Chat',
    'ChromaDB_VectorStore',
    'VannaFlaskApp',

    # RNIT enhancements
    'RNITVanna',
    'VannaQuickStart',
    'DatabaseInspector',
    'TrainingGenerator',
    'QueryOptimizer',
]

# Version check to ensure compatibility
def check_vanna_version():
    """Check if Vanna version is compatible"""
    try:
        import vanna
        vanna_version = getattr(vanna, '__version__', '0.0.0')
        return vanna_version
    except:
        return None

# Print version info when imported (can be disabled)
_vanna_version = check_vanna_version()
if _vanna_version:
    import os
    if os.environ.get('RNIT_VANNA_VERBOSE', '').lower() == 'true':
        print(f"RNIT Vanna {__version__} (using Vanna {_vanna_version})")