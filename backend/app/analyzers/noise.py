from pathlib import Path

import cv2
import numpy as np

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding


class NoiseAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "Noise Pattern Analysis"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        img = cv2.imread(str(image_path))
        if img is None:
            return AnalysisResult(
                analyzer=self.name,
                score=0.5,
                verdict=self._score_to_verdict(0.5),
                findings=[
                    Finding(
                        name="Error",
                        value="Could not read image",
                        suspicious=True,
                        description="Failed to load image",
                    )
                ],
            )

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = gray.astype(np.float64) - blurred.astype(np.float64)

        noise_mean = float(np.mean(noise))
        noise_std = float(np.std(noise))
        findings.append(
            Finding(
                name="Noise Mean",
                value=round(noise_mean, 4),
                suspicious=abs(noise_mean) > 2.0,
                description=f"Noise mean should be near 0, got {noise_mean:.4f}",
            )
        )
        findings.append(
            Finding(
                name="Noise Std Dev",
                value=round(noise_std, 4),
                suspicious=noise_std < 1.0,
                description=f"Very low noise ({noise_std:.4f}) may indicate AI generation or heavy denoising",
            )
        )

        h, w = noise.shape
        block_size = 64
        noise_map = []
        for y in range(0, max(h - block_size + 1, 0), block_size):
            row = []
            for x in range(0, max(w - block_size + 1, 0), block_size):
                block = noise[y : y + block_size, x : x + block_size]
                row.append(float(np.std(block)))
            noise_map.append(row)

        noise_map_arr = np.array(noise_map)
        if noise_map_arr.size > 0:
            noise_uniformity = float(np.std(noise_map_arr))
            noise_uniformity_suspicious = (
                noise_map_arr.size >= 4 and noise_uniformity < 0.5 and noise_std >= 1.0
            )
            findings.append(
                Finding(
                    name="Noise Uniformity",
                    value=round(noise_uniformity, 4),
                    suspicious=noise_uniformity_suspicious,
                    description=f"Spatial noise consistency: {noise_uniformity:.4f} (AI images often have uniform noise)",
                )
            )
        else:
            noise_uniformity = 0.0
            noise_uniformity_suspicious = False

        img_float = img.astype(np.float64)
        fft_magnitude = np.log1p(np.abs(np.fft.fft2(img_float[:, :, 0])))
        fft_normalized = (fft_magnitude - fft_magnitude.min()) / (fft_magnitude.max() - fft_magnitude.min() + 1e-10)

        center_h, center_w = h // 4, w // 4
        center_region = fft_normalized[:center_h, :center_w]
        edge_region = fft_normalized[center_h : 2 * center_h, center_w : 2 * center_w]

        center_energy = float(np.mean(center_region))
        edge_energy = float(np.mean(edge_region))
        energy_ratio = center_energy / (edge_energy + 1e-10)

        findings.append(
            Finding(
                name="Frequency Energy Ratio",
                value=round(energy_ratio, 3),
                suspicious=energy_ratio > 10.0 or energy_ratio < 0.5,
                description=f"Low/high frequency energy ratio: {energy_ratio:.3f}",
            )
        )

        suspicion_factors = [
            abs(noise_mean) > 2.0,
            noise_std < 1.0,
            noise_uniformity_suspicious,
            energy_ratio > 10.0 or energy_ratio < 0.5,
        ]
        score = min(sum(0.25 for f in suspicion_factors if f), 1.0)

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )
