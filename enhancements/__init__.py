"""
enhancements package initializer.

Prepends the enhancements directory to sys.path so that any modules under
enhancements/facefusion will shadow the originals in the main codebase.
"""

import os
import sys

_ENHANCEMENTS_ROOT: str = os.path.dirname(__file__)
if _ENHANCEMENTS_ROOT not in sys.path:
    sys.path.insert(0, _ENHANCEMENTS_ROOT)
