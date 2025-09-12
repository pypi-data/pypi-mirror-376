# Basic Function Package
# This package contains Pyarmor-protected modules

__version__ = "1.0.0"
__author__ = "Unknown"
__description__ = "Basic function package with Pyarmor protection"

# Import the main module
try:
    from .index import *
except ImportError as e:
    print(f"Warning: Could not import index module: {e}")
