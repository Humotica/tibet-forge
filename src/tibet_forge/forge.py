"""
The Forge - Main orchestrator for tibet-forge.

From vibe code to trusted tool.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from .config import ForgeConfig
from .score import TrustScore
from .scanners import BloatScanner, DuplicateScanner, SecurityScanner, QualityScanner
from . import mirror as mirror_client


@dataclass
class ForgeResult:
    """Result of a forge operation."""
    project_path: str
    config: ForgeConfig
    trust_score: TrustScore
    bloat_report: Any = None
    duplicate_report: Any = None
    security_report: Any = None
    quality_report: Any = None
    wrapped: bool = False
    certified: bool = False
    badge_markdown: str = ""
    content_hash: str = ""
    mirror_status: str = ""        # "registered", "already_registered", "unknown", ""
    mirror_entry: Any = None       # lookup result from Mirror
    jis_id: str = ""
    source_repo: str = ""


class Forge:
    """
    The tibet-forge.

    Pipeline:
    1. SCAN - Analyze code for issues
    2. WRAP - Auto-inject TIBET provenance
    3. CONNECT - Match with similar projects
    4. CERTIFY - Generate trust score and badge
    5. MIRROR - Register with Transparency Mirror
    """

    def __init__(self, config: Optional[ForgeConfig] = None):
        """Initialize forge."""
        self.config = config or ForgeConfig()
        self.scanners = {
            "bloat": BloatScanner(),
            "duplicate": DuplicateScanner(self.config.registry_url),
            "security": SecurityScanner(),
            "quality": QualityScanner(),
        }

    def scan(self, project_path: Path) -> ForgeResult:
        """
        Scan a project.

        Args:
            project_path: Path to project directory

        Returns:
            ForgeResult with scan reports
        """
        project_path = Path(project_path)
        config = ForgeConfig.load(project_path)

        result = ForgeResult(
            project_path=str(project_path),
            config=config,
            trust_score=TrustScore()
        )

        # Hash the project for Mirror lookups
        result.content_hash = mirror_client.hash_directory(
            project_path, ignore=config.ignore_paths
        )

        # Load JIS identity if available
        jis_id, source_repo = self._load_jis(project_path)
        result.jis_id = jis_id
        result.source_repo = source_repo

        # Run scanners
        if self.config.scan_bloat:
            result.bloat_report = self.scanners["bloat"].scan(project_path)

        if self.config.scan_duplicates:
            result.duplicate_report = self.scanners["duplicate"].scan(
                project_path,
                check_online=self.config.check_duplicates_online
            )

        if self.config.scan_security:
            result.security_report = self.scanners["security"].scan(project_path)

        # Quality scan (always)
        result.quality_report = self.scanners["quality"].scan(project_path)

        # Calculate trust score
        self._calculate_trust_score(result)

        # Mirror lookup (best-effort)
        if self.config.mirror_url:
            try:
                entry = mirror_client.lookup(self.config.mirror_url, result.content_hash)
                if entry:
                    result.mirror_status = "known"
                    result.mirror_entry = entry
                else:
                    result.mirror_status = "unknown"
            except Exception:
                result.mirror_status = "error"

        return result

    def certify(self, project_path: Path) -> ForgeResult:
        """
        Full certification pipeline.

        1. Scan
        2. Calculate score
        3. Generate badge
        4. Register with Transparency Mirror

        Args:
            project_path: Path to project

        Returns:
            ForgeResult with certification status
        """
        result = self.scan(project_path)

        # Generate badge
        if result.trust_score.total >= self.config.min_score_for_badge:
            result.certified = True
            result.badge_markdown = result.trust_score.to_badge_markdown(
                self.config.badge_style
            )

        # Register with Transparency Mirror (best-effort)
        if self.config.mirror_url and result.content_hash:
            try:
                resp = mirror_client.register_certification(
                    mirror_url=self.config.mirror_url,
                    content_hash=result.content_hash,
                    score=result.trust_score.total,
                    grade=result.trust_score.grade,
                    project_name=result.config.name or Path(result.project_path).name,
                    jis_id=result.jis_id,
                    source_repo=result.source_repo,
                )
                result.mirror_status = resp.get("status", "registered")
            except Exception:
                result.mirror_status = "error"

        return result

    def _calculate_trust_score(self, result: ForgeResult) -> None:
        """Calculate overall trust score."""
        score = result.trust_score

        # Code Quality (25%)
        if result.quality_report:
            score.add_component(
                name="Code Quality",
                score=result.quality_report.score,
                weight=0.25,
                details=f"README: {'Yes' if result.quality_report.has_readme else 'No'}, "
                        f"Tests: {'Yes' if result.quality_report.has_tests else 'No'}",
                suggestions=self._quality_suggestions(result.quality_report)
            )

        # Security (25%)
        if result.security_report:
            score.add_component(
                name="Security",
                score=result.security_report.score,
                weight=0.25,
                details=f"Critical: {result.security_report.critical_count}, "
                        f"High: {result.security_report.high_count}",
                suggestions=[f"Fix: {i.description}" for i in result.security_report.issues[:3]]
            )

        # Bloat (20%)
        if result.bloat_report:
            score.add_component(
                name="Efficiency",
                score=result.bloat_report.score,
                weight=0.20,
                details=f"Unused imports: {result.bloat_report.unused_imports}, "
                        f"Heavy deps: {len(result.bloat_report.heavy_deps)}",
                suggestions=[f"Consider: {i.suggestion}" for i in result.bloat_report.issues[:3]]
            )

        # Uniqueness (15%)
        if result.duplicate_report:
            score.add_component(
                name="Uniqueness",
                score=result.duplicate_report.score,
                weight=0.15,
                details=f"Similar projects: {len(result.duplicate_report.similar_projects)}",
                suggestions=[f"Check: {p.name} - {p.suggestion}"
                           for p in result.duplicate_report.similar_projects[:2]]
            )

        # Provenance readiness (15%)
        provenance_score = 50  # Base score
        if result.quality_report and result.quality_report.has_pyproject:
            provenance_score += 15
        if self._has_tibet_integration(Path(result.project_path)):
            provenance_score += 20
        if result.jis_id:
            provenance_score += 15  # Has JIS identity

        score.add_component(
            name="Provenance",
            score=provenance_score,
            weight=0.15,
            details=f"TIBET: {'Yes' if self._has_tibet_integration(Path(result.project_path)) else 'No'}, "
                    f"JIS: {'Yes' if result.jis_id else 'No'}",
            suggestions=self._provenance_suggestions(result)
        )

    def _provenance_suggestions(self, result: ForgeResult) -> List[str]:
        """Generate provenance-specific suggestions."""
        suggestions = []
        if not self._has_tibet_integration(Path(result.project_path)):
            suggestions.append("Add tibet-core for full provenance")
        if not result.jis_id:
            suggestions.append("Add .jis.json for identity binding (tbz init)")
        return suggestions

    def _quality_suggestions(self, report) -> List[str]:
        """Generate quality suggestions."""
        suggestions = []
        if not report.has_readme:
            suggestions.append("Add a README.md")
        if not report.has_license:
            suggestions.append("Add a LICENSE file")
        if not report.has_tests:
            suggestions.append("Add tests")
        if report.total_functions > 0 and report.documented_functions / report.total_functions < 0.5:
            suggestions.append("Add docstrings to functions")
        return suggestions

    def _has_tibet_integration(self, project_path: Path) -> bool:
        """Check if project already uses TIBET."""
        # Check for .jis.json
        if (project_path / ".jis.json").exists():
            return True

        for py_file in project_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if "tibet" in content.lower() or "TIBETProvider" in content:
                    return True
            except Exception:
                pass
        return False

    def _load_jis(self, project_path: Path) -> tuple[str, str]:
        """
        Load JIS identity from .jis.json if present.

        Returns (jis_id, source_repo) tuple.
        """
        jis_path = project_path / ".jis.json"
        if not jis_path.exists():
            return ("", "")

        try:
            data = json.loads(jis_path.read_text(encoding="utf-8"))
            jis_id = data.get("jis_id", "")
            claim = data.get("claim", {})
            source_repo = ""
            if claim:
                platform = claim.get("platform", "")
                account = claim.get("account", "")
                repo = claim.get("repo", "")
                if platform and account and repo:
                    source_repo = f"{platform}:{account}/{repo}"
            return (jis_id, source_repo)
        except Exception:
            return ("", "")
