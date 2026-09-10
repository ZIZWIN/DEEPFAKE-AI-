from pathlib import Path

import cv2
import numpy as np

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding, Verdict


class CompressionAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "JPEG Compression Analysis"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        with open(image_path, "rb") as f:
            header = f.read(3)

        is_jpeg = header[:2] == b"\xff\xd8"
        is_png = header[:3] == b"\x89PN"
        is_webp = False

        with open(image_path, "rb") as f:
            data = f.read(12)
            if len(data) >= 12 and data[4:8] == b"WEBP":
                is_webp = True

        fmt = "JPEG" if is_jpeg else "PNG" if is_png else "WEBP" if is_webp else "Unknown"
        findings.append(
            Finding(
                name="File Format",
                value=fmt,
                suspicious=False,
                description=f"Detected format: {fmt}",
            )
        )

        if not is_jpeg:
            findings.append(
                Finding(
                    name="Double Compression",
                    value="N/A",
                    suspicious=False,
                    description="Double compression check only applies to JPEG",
                )
            )
            return AnalysisResult(
                analyzer=self.name, score=0.1, verdict=self._score_to_verdict(0.1),
                findings=findings,
            )

        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return AnalysisResult(
                analyzer=self.name,
                score=0.5,
                verdict=Verdict.INCONCLUSIVE,
                findings=findings,
            )

        h, w = img.shape
        block_size = 8
        if h < block_size or w < block_size:
            findings.append(
                Finding(
                    name="Image Too Small",
                    value=f"{w}x{h}",
                    suspicious=False,
                    description="JPEG block analysis requires at least one complete 8x8 block.",
                )
            )
            return AnalysisResult(
                analyzer=self.name,
                score=0.5,
                verdict=Verdict.INCONCLUSIVE,
                findings=findings,
            )

        zero_count_map = np.zeros((h // block_size, w // block_size))

        for by in range(h // block_size):
            for bx in range(w // block_size):
                block = img[by * block_size : (by + 1) * block_size, bx * block_size : (bx + 1) * block_size].astype(np.float64)
                dct_block = cv2.dct(block - 128)
                zero_count_map[by, bx] = np.sum(np.abs(dct_block) < 0.5)

        mean_zeros = float(np.mean(zero_count_map))
        std_zeros = float(np.std(zero_count_map))
        findings.append(
            Finding(
                name="Mean Zero DCT Coefficients",
                value=round(mean_zeros, 2),
                suspicious=False,
                description=f"Average zero-valued DCT coefficients per 8x8 block: {mean_zeros:.2f}/64",
            )
        )
        findings.append(
            Finding(
                name="DCT Zero Std Dev",
                value=round(std_zeros, 4),
                suspicious=std_zeros > 5.0,
                description=f"Std dev of zero coefficients across blocks: {std_zeros:.4f}",
            )
        )

        block_stds = []
        for by in range(h // block_size):
            for bx in range(w // block_size):
                sub_block = img[by * block_size : (by + 1) * block_size, bx * block_size : (bx + 1) * block_size]
                block_stds.append(float(np.std(sub_block.astype(np.float64))))

        block_std_arr = np.array(block_stds)
        grid_pattern = float(np.std(block_std_arr))
        findings.append(
            Finding(
                name="8x8 Grid Pattern",
                value=round(grid_pattern, 4),
                suspicious=grid_pattern < 1.0,
                description=f"Block-level variation: {grid_pattern:.4f} (very uniform blocks suggest synthetic content)",
            )
        )

        with open(image_path, "rb") as f:
            data = f.read()

        quantization_tables = data.count(b"\xff\xdb")
        findings.append(
            Finding(
                name="Quantization Tables",
                value=quantization_tables,
                suspicious=quantization_tables > 2,
                description=f"Found {quantization_tables} quantization tables (multiple may indicate double compression)",
            )
        )

        suspicion_factors = [
            std_zeros > 5.0,
            grid_pattern < 1.0,
            quantization_tables > 2,
        ]
        score = min(sum(1.0 / len(suspicion_factors) for f in suspicion_factors if f), 1.0)

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )
