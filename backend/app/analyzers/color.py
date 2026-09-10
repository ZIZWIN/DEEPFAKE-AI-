from pathlib import Path

import cv2
import numpy as np

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding, Verdict


class ColorConsistencyAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "Color Consistency Analysis"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        img = cv2.imread(str(image_path))
        if img is None:
            return AnalysisResult(
                analyzer=self.name,
                score=0.5,
                verdict=Verdict.INCONCLUSIVE,
                findings=[
                    Finding(
                        name="Error",
                        value="Could not read image",
                        suspicious=True,
                        description="Failed to load image",
                    )
                ],
            )

        b, g, r = cv2.split(img)

        channel_corrs = {
            "R-G": self._safe_corrcoef(r, g),
            "R-B": self._safe_corrcoef(r, b),
            "G-B": self._safe_corrcoef(g, b),
        }

        for pair, corr in channel_corrs.items():
            findings.append(
                Finding(
                    name=f"Channel Correlation {pair}",
                    value=round(corr, 4),
                    suspicious=corr < 0.7,
                    description=f"{pair} correlation: {corr:.4f} (very low correlation may indicate channel-wise generation artifacts)",
                )
            )

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h_channel, s_channel, v_channel = cv2.split(hsv)

        h_hist_raw = cv2.calcHist([h_channel], [0], None, [36], [0, 180]).flatten()
        h_hist = h_hist_raw / max(float(h_hist_raw.sum()), 1.0)
        h_entropy = -np.sum(h_hist * np.log2(h_hist + 1e-10))

        s_hist_raw = cv2.calcHist([s_channel], [0], None, [32], [0, 256]).flatten()
        s_hist = s_hist_raw / max(float(s_hist_raw.sum()), 1.0)
        s_entropy = -np.sum(s_hist * np.log2(s_hist + 1e-10))

        findings.append(
            Finding(
                name="Hue Entropy",
                value=round(float(h_entropy), 3),
                suspicious=h_entropy < 2.0,
                description=f"Hue entropy: {h_entropy:.3f} (low entropy = limited color variety)",
            )
        )
        findings.append(
            Finding(
                name="Saturation Entropy",
                value=round(float(s_entropy), 3),
                suspicious=s_entropy < 2.5,
                description=f"Saturation entropy: {s_entropy:.3f} (low entropy may indicate synthetic colors)",
            )
        )

        h, w, _ = img.shape
        block_size = min(h, w) // 4
        if block_size > 0:
            blocks = []
            for y in range(0, h - block_size, block_size):
                for x in range(0, w - block_size, block_size):
                    block = img[y : y + block_size, x : x + block_size]
                    blocks.append(np.mean(block, axis=(0, 1)))

            if len(blocks) >= 2:
                blocks_arr = np.array(blocks)
                color_variance = float(np.mean(np.std(blocks_arr, axis=0)))
                findings.append(
                    Finding(
                        name="Spatial Color Variance",
                        value=round(color_variance, 3),
                        suspicious=color_variance < 5.0,
                        description=f"Color variance across regions: {color_variance:.3f}",
                    )
                )
            else:
                color_variance = 0.0
        else:
            color_variance = 0.0

        low_corr_count = sum(1 for c in channel_corrs.values() if c < 0.7)
        suspicion_factors = [
            low_corr_count >= 2,
            h_entropy < 2.0,
            s_entropy < 2.5,
            color_variance < 5.0,
        ]
        score = min(sum(0.25 for f in suspicion_factors if f), 1.0)

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )

    def _safe_corrcoef(self, first: np.ndarray, second: np.ndarray) -> float:
        first_std = float(np.std(first))
        second_std = float(np.std(second))
        if first_std < 1e-10 or second_std < 1e-10:
            return 1.0
        corr = float(np.corrcoef(first.flat, second.flat)[0, 1])
        if not np.isfinite(corr):
            return 1.0
        return corr
