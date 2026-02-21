"""
Forge configuration.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class ForgeConfig:
    """
    Configuration for tibet-forge.

    Can be loaded from:
    - tibet-forge.json
    - .tibetrc
    - pyproject.toml [tool.tibet-forge]
    """

    # Project info
    name: str = ""
    version: str = "0.0.0"
    description: str = ""
    author: str = ""

    # Scan settings
    scan_bloat: bool = True
    scan_duplicates: bool = True
    scan_security: bool = True
    ignore_paths: List[str] = field(default_factory=lambda: [
        "__pycache__", ".git", ".venv", "venv", "node_modules",
        "dist", "build", "*.egg-info"
    ])

    # Wrap settings
    auto_wrap: bool = True
    wrap_functions: bool = True
    wrap_classes: bool = True
    wrap_api_calls: bool = True

    # Registry settings
    registry_url: str = "https://humotica.com/api/forge"
    check_duplicates_online: bool = True
    suggest_collaborations: bool = True

    # Certification
    min_score_for_badge: int = 70
    badge_style: str = "flat"  # flat, flat-square, plastic

    # Actor identity (JIS format)
    actor: str = ""

    @classmethod
    def load(cls, path: Path) -> "ForgeConfig":
        """Load config from file or directory."""
        if path.is_dir():
            # Look for config files
            for name in ["tibet-forge.json", ".tibetrc", ".tibet-forge.json"]:
                config_file = path / name
                if config_file.exists():
                    return cls.from_json(config_file)

            # Try pyproject.toml
            pyproject = path / "pyproject.toml"
            if pyproject.exists():
                return cls.from_pyproject(pyproject)

            # Default config
            return cls()

        elif path.suffix == ".json" or path.name == ".tibetrc":
            return cls.from_json(path)
        elif path.name == "pyproject.toml":
            return cls.from_pyproject(path)
        else:
            return cls()

    @classmethod
    def from_json(cls, path: Path) -> "ForgeConfig":
        """Load from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_pyproject(cls, path: Path) -> "ForgeConfig":
        """Load from pyproject.toml [tool.tibet-forge] section."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)

        forge_config = data.get("tool", {}).get("tibet-forge", {})

        # Also get project info
        project = data.get("project", {})
        if "name" not in forge_config and "name" in project:
            forge_config["name"] = project["name"]
        if "version" not in forge_config and "version" in project:
            forge_config["version"] = project["version"]
        if "description" not in forge_config and "description" in project:
            forge_config["description"] = project["description"]

        return cls(**{k: v for k, v in forge_config.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def save(self, path: Path):
        """Save config to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
