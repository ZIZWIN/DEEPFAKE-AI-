from pathlib import Path

import cv2
import numpy as np

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding, Verdict


class AITextureAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "AI Texture Analysis"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        img = cv2.imread(str(image_path))
        if img is None:
            return AnalysisResult(analyzer=self.name, score=0.5, verdict=Verdict.INCONCLUSIVE)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Laplacian Variance (Global Sharpness)
        # Real photos have a mix of sharp and soft areas. AI is often uniformly sharp.
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = float(laplacian.var())

        # 2. Local Texture Smoothness (Local Variance)
        # We check small blocks for 'dead' textures (plastic look)
        h, w = gray.shape
        block_size = 32
        low_variance_blocks = 0
        total_blocks = 0

        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = gray[y:y+block_size, x:x+block_size]
                var = np.var(block)
                if var < 10.0: # Very smooth region
                    low_variance_blocks += 1
                total_blocks += 1

        smoothness_ratio = low_variance_blocks / max(total_blocks, 1)

        # 3. Combined Logic: High sharpness + significant local smoothness = AI 'Plastic' Look
        # Mobile phones apply aggressive sharpening and noise reduction (smoothing).
        # We raise these thresholds to avoid falsely flagging authentic mobile photos.
        is_plastic = sharpness > 1500 and smoothness_ratio > 0.35
        is_extremely_sharp = sharpness > 4000
        is_too_flat = smoothness_ratio > 0.70

        findings.append(Finding(
            name="Artificial Sharpness",
            value=round(sharpness, 2),
            suspicious=is_extremely_sharp,
            description="High frequency sharpening often used in AI upscaling"
        ))

        findings.append(Finding(
            name="Texture Plasticity",
            value=round(smoothness_ratio, 3),
            suspicious=is_plastic or is_too_flat,
            description=f"{smoothness_ratio*100:.1f}% of image shows unnatural smoothness (typical of GAN/Diffusion skin)"
        ))

        # Scoring logic (Inverted: 1.0 = Authentic, 0.0 = Fake)
        # We want the 'auth_score' to drop significantly.
        # Since this analyzer returns a 'manipulation score' (0=good, 1=bad)
        # which is later inverted by pipeline.py, we return HIGH score for AI.
        manipulation_score = 0.0
        if is_plastic: manipulation_score += 0.6
        if is_extremely_sharp: manipulation_score += 0.3
        if is_too_flat: manipulation_score += 0.4

        manipulation_score = min(manipulation_score, 1.0)

        return AnalysisResult(
            analyzer=self.name,
            score=manipulation_score,
            verdict=self._score_to_verdict(manipulation_score),
            findings=findings
        )
