"""
Trust Score calculation.

The gamification layer - developers want high scores!
"""

from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class ScoreComponent:
    """Individual score component."""
    name: str
    score: int  # 0-100
    weight: float  # 0.0-1.0
    details: str = ""
    suggestions: List[str] = field(default_factory=list)


@dataclass
class TrustScore:
    """
    Humotica Trust Score.

    Components:
    - Code Quality (25%)
    - Security (25%)
    - Provenance (20%)
    - Documentation (15%)
    - Community (15%)
    """

    total: int = 0
    grade: str = "F"
    components: List[ScoreComponent] = field(default_factory=list)
    timestamp: str = ""
    certified: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def calculate(self):
        """Calculate total score from components."""
        if not self.components:
            self.total = 0
            self.grade = "F"
            return

        weighted_sum = sum(c.score * c.weight for c in self.components)
        total_weight = sum(c.weight for c in self.components)

        self.total = int(weighted_sum / total_weight) if total_weight > 0 else 0
        self.grade = self._grade_from_score(self.total)
        self.certified = self.total >= 70

    @staticmethod
    def _grade_from_score(score: int) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 25:
            return "D"
        else:
            return "F"

    def grade_message(self) -> str:
        """Get the TIBET grade message with attitude."""
        if self.total >= 90:
            return "[A] FUCKING AWESOME! Fully grounded, zero bloat. Push to production."
        elif self.total >= 70:
            return "[B] Solid. Foundation stands, but throw a @tibet_audit wrapper on it."
        elif self.total >= 50:
            return "[C] Dangerous territory. It 'works', but the CISO gets hives from this."
        elif self.total >= 25:
            return "[D] Heavily over-engineered. Stop hallucinating and just use httpx."
        else:
            return "[F] SHIT. This is a digital crime. Delete the repo and start over."

    def add_component(
        self,
        name: str,
        score: int,
        weight: float,
        details: str = "",
        suggestions: List[str] = None
    ):
        """Add a score component."""
        self.components.append(ScoreComponent(
            name=name,
            score=min(100, max(0, score)),
            weight=weight,
            details=details,
            suggestions=suggestions or []
        ))
        self.calculate()

    def to_badge_url(self, style: str = "flat") -> str:
        """Generate shields.io badge URL."""
        color = self._color_from_score(self.total)
        return (
            f"https://img.shields.io/badge/"
            f"Humotica_Trust_Score-{self.total}%2F100-{color}"
            f"?style={style}&logo=data:image/svg+xml;base64,..."
        )

    def to_badge_markdown(self, style: str = "flat") -> str:
        """Generate markdown badge."""
        url = self.to_badge_url(style)
        return f"[![Humotica Trust Score]({url})](https://humotica.com/trust)"

    @staticmethod
    def _color_from_score(score: int) -> str:
        """Get badge color from score."""
        if score >= 90:
            return "brightgreen"
        elif score >= 80:
            return "green"
        elif score >= 70:
            return "yellowgreen"
        elif score >= 60:
            return "yellow"
        elif score >= 50:
            return "orange"
        else:
            return "red"

    def summary(self) -> str:
        """Generate text summary."""
        lines = [
            f"Humotica Trust Score: {self.total}/100 ({self.grade})",
            f"Certified: {'Yes' if self.certified else 'No'}",
            "",
            "Components:"
        ]

        for c in sorted(self.components, key=lambda x: x.weight, reverse=True):
            lines.append(f"  {c.name}: {c.score}/100 (weight: {c.weight:.0%})")
            if c.details:
                lines.append(f"    {c.details}")
            for s in c.suggestions:
                lines.append(f"    → {s}")

        return "\n".join(lines)
