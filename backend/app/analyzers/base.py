import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Verdict(str, Enum):
    AUTHENTIC = "authentic"
    SUSPICIOUS = "suspicious"
    LIKELY_FAKE = "likely_fake"
    INCONCLUSIVE = "inconclusive"


@dataclass
class Finding:
    name: str
    value: str | int | float | bool
    suspicious: bool
    description: str


@dataclass
class AnalysisResult:
    analyzer: str
    score: float  # 0.0 (authentic) to 1.0 (likely fake)
    verdict: Verdict
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analyzer": self.analyzer,
            "score": round(_clamp_score(self.score), 3),
            "verdict": self.verdict.value,
            "findings": [
                {
                    "name": f.name,
                    "value": _json_safe_value(f.value),
                    "suspicious": bool(f.suspicious),
                    "description": f.description,
                }
                for f in self.findings
            ],
        }


class BaseAnalyzer(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def analyze(self, image_path: Path) -> AnalysisResult: ...

    def _score_to_verdict(self, score: float) -> Verdict:
        score = _clamp_score(score)
        if score < 0.3:
            return Verdict.AUTHENTIC
        if score < 0.6:
            return Verdict.SUSPICIOUS
        return Verdict.LIKELY_FAKE


def _clamp_score(score: float) -> float:
    if not math.isfinite(score):
        return 0.5
    return min(max(score, 0.0), 1.0)


def _json_safe_value(value: Any) -> str | int | float | bool:
    if isinstance(value, float) and not math.isfinite(value):
        return "N/A"
    if hasattr(value, "item"):
        val = value.item()
        if isinstance(val, (str, int, float, bool)):
            return val
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
