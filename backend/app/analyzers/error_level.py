from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding


class ErrorLevelAnalyzer(BaseAnalyzer):
    def __init__(self, quality: int = 95):
        self.quality = quality

    @property
    def name(self) -> str:
        return "Error Level Analysis (ELA)"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        with Image.open(image_path) as img:
            original = img.convert("RGB")
        w, h = original.size

        resaved_buffer = BytesIO()
        original.save(resaved_buffer, "JPEG", quality=self.quality)
        resaved_buffer.seek(0)
        with Image.open(resaved_buffer) as img:
            resaved = img.convert("RGB")

        diff = ImageChops.difference(original, resaved)
        extrema = diff.getextrema()

        max_diffs: list[float] = []
        if isinstance(extrema, tuple):
            for e in extrema:
                if isinstance(e, tuple) and len(e) >= 2:
                    max_diffs.append(e[1])
                elif isinstance(e, (int, float)):
                    max_diffs.append(e)

        avg_max_diff = sum(max_diffs) / len(max_diffs) if max_diffs else 0.0
        findings.append(
            Finding(
                name="Max Pixel Difference",
                value=round(avg_max_diff, 2),
                suspicious=avg_max_diff > 15,
                description=f"Average max channel difference after re-save: {avg_max_diff:.2f}/255",
            )
        )

        diff_arr = np.array(diff, dtype=np.float64)
        mean_diff = float(np.mean(diff_arr))
        std_diff = float(np.std(diff_arr))
        findings.append(
            Finding(
                name="Mean Error Level",
                value=round(mean_diff, 3),
                suspicious=mean_diff > 5.0,
                description=f"Mean error across all pixels: {mean_diff:.3f}",
            )
        )
        findings.append(
            Finding(
                name="Error Std Deviation",
                value=round(std_diff, 3),
                suspicious=std_diff > 8.0,
                description=f"Standard deviation of error: {std_diff:.3f} (high variance = inconsistent compression)",
            )
        )

        amplified = diff.point(lambda x: min(x * 15, 255))
        amplified_gray = amplified.convert("L")
        amplified_arr = np.array(amplified_gray)

        threshold = 50
        suspicious_pixels = np.sum(amplified_arr > threshold)
        total_pixels = amplified_arr.size
        suspicious_ratio = suspicious_pixels / total_pixels
        findings.append(
            Finding(
                name="Suspicious Region Ratio",
                value=round(float(suspicious_ratio), 4),
                suspicious=bool(suspicious_ratio > 0.15),
                description=f"{suspicious_ratio * 100:.2f}% of image shows elevated error levels",
            )
        )

        block_size = 64
        block_variances = []
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = amplified_arr[y : y + block_size, x : x + block_size]
                block_variances.append(float(np.var(block)))

        if block_variances:
            variance_of_variances = float(np.var(block_variances))
            findings.append(
                Finding(
                    name="Block Variance Inconsistency",
                    value=round(variance_of_variances, 2),
                    suspicious=variance_of_variances > 1000,
                    description="High variance across blocks suggests mixed compression (splicing)",
                )
            )
        else:
            variance_of_variances = 0.0

        suspicion_factors = [
            avg_max_diff > 15,
            mean_diff > 5.0,
            std_diff > 8.0,
            suspicious_ratio > 0.15,
            variance_of_variances > 1000,
        ]
        score = min(sum(0.2 for f in suspicion_factors if f), 1.0)

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )
