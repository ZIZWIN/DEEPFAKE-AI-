from pathlib import Path

import exifread
from PIL import Image

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding

SUSPICIOUS_SOFTWARE = {"photoshop", "gimp", "paint.net", "faceapp", "reface", "deepface", "dall-e", "midjourney", "stable diffusion", "comfyui"}


class MetadataAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "EXIF Metadata Analysis"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []
        suspicion_score = 0.0

        with open(image_path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        has_camera = any(t in tags for t in ["Image Make", "Image Model"])
        findings.append(
            Finding(
                name="Camera Info Present",
                value=has_camera,
                suspicious=not has_camera,
                description="Real photos typically have camera make/model in EXIF",
            )
        )
        if not has_camera:
            suspicion_score += 0.10

        has_software = "Image Software" in tags
        software_val = str(tags.get("Image Software", "")).lower()
        is_ai_software = any(s in software_val for s in SUSPICIOUS_SOFTWARE) if has_software else False
        findings.append(
            Finding(
                name="Software Tag",
                value=software_val if has_software else "None",
                suspicious=is_ai_software,
                description="AI/editing software detected in metadata" if is_ai_software else "No AI software signature found",
            )
        )
        if is_ai_software:
            suspicion_score += 0.4

        has_timestamp = any(t in tags for t in ["Image DateTime", "EXIF DateTimeOriginal"])
        findings.append(
            Finding(
                name="Timestamp Present",
                value=has_timestamp,
                suspicious=not has_timestamp,
                description="Missing timestamps are common in AI-generated images",
            )
        )
        if not has_timestamp:
            suspicion_score += 0.05

        has_gps = "GPS GPSLatitude" in tags
        findings.append(
            Finding(
                name="GPS Data Present",
                value=has_gps,
                suspicious=False,
                description="GPS data adds provenance (absence is neutral)",
            )
        )

        has_thumbnail = any(t in tags for t in ["JPEGThumbnail", "TIFFThumbnail"])
        findings.append(
            Finding(
                name="Thumbnail Present",
                value=has_thumbnail,
                suspicious=not has_thumbnail,
                description="Missing thumbnail can indicate image was re-generated",
            )
        )
        if not has_thumbnail:
            suspicion_score += 0.05

        try:
            with Image.open(image_path) as img:
                findings.append(
                    Finding(
                        name="Image Format",
                        value=img.format or "Unknown",
                        suspicious=False,
                        description=f"Image format: {img.format}, Mode: {img.mode}",
                    )
                )
                findings.append(
                    Finding(
                        name="Image Size",
                        value=f"{img.size[0]}x{img.size[1]}",
                        suspicious=False,
                        description=f"Dimensions: {img.size[0]}x{img.size[1]} pixels",
                    )
                )
        except Exception:
            pass

        num_tags = len(tags)
        findings.append(
            Finding(
                name="Total EXIF Tags",
                value=num_tags,
                suspicious=num_tags < 3,
                description="Very few EXIF tags may indicate metadata was stripped or image is AI-generated",
            )
        )
        if num_tags < 3:
            suspicion_score += 0.05

        score = min(suspicion_score, 1.0)
        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )
