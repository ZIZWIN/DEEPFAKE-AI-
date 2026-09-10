from pathlib import Path

import cv2
import numpy as np

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding, Verdict


class FrequencyAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "Frequency Domain Analysis"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
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

        img_float = img.astype(np.float64)
        h, w = img.shape
        if min(h, w) < 32:
            return AnalysisResult(
                analyzer=self.name,
                score=0.5,
                verdict=Verdict.INCONCLUSIVE,
                findings=[
                    Finding(
                        name="Image Too Small",
                        value=f"{w}x{h}",
                        suspicious=False,
                        description="Frequency analysis requires at least 32 pixels on each side.",
                    )
                ],
            )

        fft = np.fft.fft2(img_float)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)
        magnitude_log = np.log1p(magnitude)

        cy, cx = h // 2, w // 2

        Y, X = np.ogrid[:h, :w]
        dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

        max_radius = min(cx, cy)
        ring_width = max(max_radius // 10, 1)

        energies = []
        for i in range(10):
            inner = i * ring_width
            outer = (i + 1) * ring_width
            mask = (dist >= inner) & (dist < outer)
            if mask.any():
                energies.append(float(np.mean(magnitude_log[mask])))
            else:
                energies.append(0.0)

        if len(energies) >= 2 and energies[0] > 0:
            falloff = energies[0] / (energies[-1] + 1e-10)
            findings.append(
                Finding(
                    name="Spectral Falloff",
                    value=round(falloff, 2),
                    suspicious=falloff > 300 or falloff < 1.2,
                    description=f"Energy ratio low/high freq: {falloff:.2f}",
                )
            )
        else:
            falloff = 0.0

        ny, nx = h // 2, w // 2
        q1 = magnitude_log[:ny, :nx]
        q2 = magnitude_log[:ny, nx:]
        q3 = magnitude_log[ny:, :nx]
        q4 = magnitude_log[ny:, nx:]

        quadrant_stds = [float(np.std(q)) for q in [q1, q2, q3, q4]]
        symmetry = float(np.std(quadrant_stds))
        findings.append(
            Finding(
                name="Spectral Symmetry",
                value=round(symmetry, 4),
                suspicious=symmetry > 0.7,
                description=f"Quadrant energy std: {symmetry:.4f} (natural images are roughly symmetric)",
            )
        )

        rows_mean = np.mean(magnitude_log, axis=1)
        cols_mean = np.mean(magnitude_log, axis=0)

        row_peaks = self._detect_periodic_peaks(rows_mean)
        col_peaks = self._detect_periodic_peaks(cols_mean)

        total_peaks = row_peaks + col_peaks
        findings.append(
            Finding(
                name="Periodic Artifacts",
                value=total_peaks,
                suspicious=total_peaks > 15,
                description=f"Detected {total_peaks} periodic frequency peaks (grid/tile artifacts from generation)",
            )
        )

        # Graduated scoring — first flag is weaker, each additional adds more
        suspicion_factors = [
            (falloff > 300 or falloff < 1.2, 0.20),
            (symmetry > 0.7, 0.25),
            (total_peaks > 15, 0.30),
        ]
        score = min(sum(weight for triggered, weight in suspicion_factors if triggered), 1.0)

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )

    def _detect_periodic_peaks(self, signal: np.ndarray, threshold: float = 4.0) -> int:
        if len(signal) < 10:
            return 0
        mean = np.mean(signal)
        std = np.std(signal)
        if std < 1e-10:
            return 0
        normalized = (signal - mean) / std
        peaks = np.sum(normalized > threshold)
        return int(peaks)
