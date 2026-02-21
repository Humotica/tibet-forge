"""
tibet-forge: From vibe code to trusted tool.

The Let's Encrypt of AI provenance.

Usage:
    # Scan your project
    tibet-forge scan .

    # Full pipeline: scan, wrap, certify
    tibet-forge certify .

    # Check trust score
    tibet-forge score .

What it does:
    1. SCAN - AST analysis for bloat, duplicates, security
    2. WRAP - Auto-inject TIBET provenance
    3. CONNECT - Match with similar projects
    4. CERTIFY - Generate trust score and badge

The vibe coder doesn't need to understand TIBET.
It just works. Like HTTPS.
"""

from .forge import Forge
from .score import TrustScore
from .config import ForgeConfig

__version__ = "0.1.0"
__all__ = ["Forge", "TrustScore", "ForgeConfig"]
