"""
Scanners for tibet-forge.

Each scanner analyzes a specific aspect of the code.
"""

from .bloat import BloatScanner
from .duplicate import DuplicateScanner
from .security import SecurityScanner
from .quality import QualityScanner

__all__ = ["BloatScanner", "DuplicateScanner", "SecurityScanner", "QualityScanner"]
