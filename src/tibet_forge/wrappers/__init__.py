"""
Wrappers for tibet-forge.

Auto-inject TIBET provenance into existing code.
"""

from .decorator import tibet_audit
from .injector import TibetInjector

__all__ = ["tibet_audit", "TibetInjector"]
