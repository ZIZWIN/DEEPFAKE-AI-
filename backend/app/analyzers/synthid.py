from pathlib import Path

import cv2
import exifread
import numpy as np
from PIL import Image

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding


class SynthIDAnalyzer(BaseAnalyzer):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "SynthID Watermark Detection"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        with Image.open(image_path) as img:
            img_arr = np.array(img.convert("RGB"), dtype=np.uint8)

        # 1. Digital Watermark Frequency Forensic Check
        watermark_score = self._check_frequency_pattern(img_arr)
        findings.append(
            Finding(
                name="Frequency Pattern Anomaly Score",
                value=round(watermark_score, 4),
                suspicious=watermark_score > 0.7,
                description=(
                    "Experimental frequency-domain pattern score. This is not an official "
                    f"SynthID detector. Score: {watermark_score:.4f}"
                ),
            )
        )

        # 2. Least-Significant-Bit (LSB) Noise Forensic Check
        lsb_score = self._check_lsb_pattern(img_arr)
        findings.append(
            Finding(
                name="LSB Pattern Anomaly Score",
                value=round(lsb_score, 4),
                suspicious=lsb_score > 0.7,
                description=(
                    "Experimental least-significant-bit anomaly score. This is not an "
                    f"official SynthID detector. Score: {lsb_score:.4f}"
                ),
            )
        )

        # 3. Metadata Scanner for Digital Watermarks (C2PA/SynthID headers)
        metadata_found = False
        watermark_metadata_type = "None"
        try:
            # Search standard EXIF tags
            with open(image_path, "rb") as f:
                tags = exifread.process_file(f, details=False)
            for key, val in tags.items():
                val_str = str(val).lower()
                if any(w in val_str for w in ["synthid", "watermark", "c2pa", "google_ai"]):
                    metadata_found = True
                    watermark_metadata_type = f"EXIF ({key})"
                    break

            # Scan raw file content for metadata signatures (e.g. C2PA or PNG text chunks)
            if not metadata_found:
                with open(image_path, "rb") as f:
                    file_bytes = f.read(250 * 1024)  # check first 250KB for speed
                    for keyword in [b"SynthID", b"C2PA", b"ContentCredentials", b"Google_Watermark"]:
                        if keyword in file_bytes:
                            metadata_found = True
                            watermark_metadata_type = keyword.decode("utf-8")
                            break
        except Exception:
            pass

        findings.append(
            Finding(
                name="Watermark Metadata Signature",
                value="Found" if metadata_found else "Not Found",
                suspicious=metadata_found,
                description=f"Scanned EXIF & PNG headers. Signature type: {watermark_metadata_type}",
            )
        )

        # 4. Digital Watermark Template Correlation
        template_corr = self._check_template_correlation(img_arr)
        findings.append(
            Finding(
                name="Watermark Template Correlation",
                value=round(template_corr, 4),
                suspicious=template_corr > 0.45,
                description=f"Periodic spatial autocorrelation score: {template_corr:.4f} (high indicates embedded dither pattern)",
            )
        )

        # 5. Local Visual Forensics of Watermarked Pixels
        visual_forensics = self._check_visual_forensics(img_arr)
        findings.append(
            Finding(
                name="Watermark Visual Forensics",
                value=round(visual_forensics, 4),
                suspicious=visual_forensics > 0.6,
                description=f"Luminance/gradient fluctuation score: {visual_forensics:.4f}",
            )
        )

        # Official verification summary
        findings.append(
            Finding(
                name="Official SynthID Verification",
                value="Google portal recommended",
                suspicious=False,
                description="Google's official SynthID detector API is closed-source. Match findings against Google Gemini/Vertex AI for full proof.",
            )
        )

        # Overall aggregate score
        agg_score = max(watermark_score, lsb_score, template_corr, visual_forensics)
        if metadata_found:
            agg_score = max(agg_score, 0.85)

        # We keep the final score within a suspicious/likely_fake range based on strength of watermark detection
        score = min(agg_score, 0.95)

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )

    def _check_frequency_pattern(self, img_arr: np.ndarray) -> float:
        gray = np.mean(img_arr, axis=2)
        if min(gray.shape) < 32:
            return 0.0

        fft = np.fft.fft2(gray)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.log1p(np.abs(fft_shift))

        h, w = gray.shape
        cy, cx = h // 2, w // 2
        Y, X = np.ogrid[:h, :w]
        dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

        mid_mask = (dist > min(cx, cy) * 0.3) & (dist < min(cx, cy) * 0.7)
        if not mid_mask.any():
            return 0.0

        mid_values = magnitude[mid_mask]
        mid_std = float(np.std(mid_values))
        if mid_std < 1e-10:
            return 0.0

        z_scores = (mid_values - float(np.mean(mid_values))) / mid_std
        spike_ratio = float(np.mean(z_scores > 4.0))
        spike_score = min(spike_ratio * 25.0, 1.0)

        row_score = self._profile_peak_score(np.mean(magnitude, axis=1))
        col_score = self._profile_peak_score(np.mean(magnitude, axis=0))
        return max(spike_score, row_score, col_score)

    def _check_lsb_pattern(self, img_arr: np.ndarray) -> float:
        lsb = img_arr & 1
        channel_means = [float(np.mean(lsb[:, :, c])) for c in range(3)]
        mean_deviation = min(sum(abs(m - 0.5) for m in channel_means) / 3.0 * 4.0, 1.0)

        channel_corrs = [
            abs(self._safe_corrcoef(lsb[:, :, 0], lsb[:, :, 1])),
            abs(self._safe_corrcoef(lsb[:, :, 0], lsb[:, :, 2])),
            abs(self._safe_corrcoef(lsb[:, :, 1], lsb[:, :, 2])),
        ]
        corr_score = min(max(channel_corrs) * 2.0, 1.0)

        h, w, _ = lsb.shape
        block_score = 0.0
        block_size = 32
        if h >= block_size * 2 and w >= block_size * 2:
            block_means = []
            for y in range(0, h - block_size + 1, block_size):
                for x in range(0, w - block_size + 1, block_size):
                    block_means.append(float(np.mean(lsb[y : y + block_size, x : x + block_size])))
            block_score = min(max(float(np.std(block_means)) - 0.04, 0.0) * 8.0, 1.0)

        return max(mean_deviation, corr_score, block_score)

    def _check_template_correlation(self, img_arr: np.ndarray) -> float:
        gray = np.mean(img_arr, axis=2).astype(np.float64)
        h, w = gray.shape
        if h < 64 or w < 64:
            return 0.0

        # Take a center block of 32x32 to test autocorrelation spikes at standard watermark dither grids
        cy, cx = h // 2, w // 2
        block = gray[cy - 16 : cy + 16, cx - 16 : cx + 16]

        shifts = [8, 16]
        corr_scores = []
        for s in shifts:
            if cx + s + 16 < w:
                adj_block = gray[cy - 16 : cy + 16, cx - 16 + s : cx + 16 + s]
                std_b = np.std(block)
                std_a = np.std(adj_block)
                if std_b > 1e-5 and std_a > 1e-5:
                    corr = float(
                        np.mean((block - np.mean(block)) * (adj_block - np.mean(adj_block)))
                        / (std_b * std_a)
                    )
                    corr_scores.append(abs(corr))

        return max(corr_scores) if corr_scores else 0.0

    def _check_visual_forensics(self, img_arr: np.ndarray) -> float:
        gray = np.mean(img_arr, axis=2).astype(np.float64)
        h, w = gray.shape
        if h < 32 or w < 32:
            return 0.0

        # Calculate image gradients
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        mag = np.sqrt(gx**2 + gy**2)

        # Digital watermarks create minute fluctuations in flat/low-gradient regions
        flat_regions = mag < 0.05
        if not flat_regions.any():
            return 0.0

        flat_noise = np.std(mag[flat_regions])
        return min(float(flat_noise) * 15.0, 1.0)

    def _profile_peak_score(self, profile: np.ndarray) -> float:
        if profile.size < 32:
            return 0.0
        std = float(np.std(profile))
        if std < 1e-10:
            return 0.0
        z_scores = (profile - float(np.mean(profile))) / std
        center = profile.size // 2
        exclusion = max(profile.size // 20, 2)
        z_scores[max(center - exclusion, 0) : center + exclusion + 1] = 0.0
        return min(float(np.mean(z_scores > 3.5)) * 20.0, 1.0)

    def _safe_corrcoef(self, first: np.ndarray, second: np.ndarray) -> float:
        first_std = float(np.std(first))
        second_std = float(np.std(second))
        if first_std < 1e-10 or second_std < 1e-10:
            return 0.0
        corr = float(np.corrcoef(first.flat, second.flat)[0, 1])
        if not np.isfinite(corr):
            return 0.0
        return corr
