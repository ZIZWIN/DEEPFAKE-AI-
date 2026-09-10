"""Image classifier using OpenCV Haar/LBP Cascades — no ML models required.

Detects both human and anime/cartoon faces so that stylised artwork,
AI-generated anime portraits, and filtered photos are all treated as
face-containing images (no "No Face Detected" warning).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2

# Path to the bundled anime face LBP cascade (alongside this file)
_ANIME_CASCADE_PATH = str(Path(__file__).parent / "lbpcascade_animeface.xml")


@dataclass
class FaceRegion:
    x: int
    y: int
    w: int
    h: int

    def to_dict(self) -> dict[str, Any]:
        return {"x": int(self.x), "y": int(self.y), "w": int(self.w), "h": int(self.h)}


@dataclass
class ClassificationResult:
    image_type: str  # "face" | "object" | "mixed"
    face_count: int
    face_regions: list[FaceRegion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_type": self.image_type,
            "face_count": self.face_count,
            "face_regions": [f.to_dict() for f in self.face_regions],
        }


def _deduplicate(
    existing: list[tuple[int, int, int, int]],
    candidates: list[tuple[int, int, int, int]],
) -> list[tuple[int, int, int, int]]:
    """Add *candidates* to *existing*, skipping any that overlap an existing box."""
    for fx, fy, fw, fh in candidates:
        overlap = False
        for sx, sy, sw, sh in existing:
            ix1, iy1 = max(fx, sx), max(fy, sy)
            ix2, iy2 = min(fx + fw, sx + sw), min(fy + fh, sy + sh)
            if ix2 > ix1 and iy2 > iy1:
                overlap = True
                break
        if not overlap:
            existing.append((fx, fy, fw, fh))
    return existing


def classify_image(image_path: Path) -> ClassificationResult:
    """
    Detect faces using multiple OpenCV cascades and classify the image as:
      - "face"   : one or more faces detected (human OR anime/cartoon)
      - "object" : no faces detected at all
      - "mixed"  : faces detected alongside large non-face regions
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return ClassificationResult(image_type="object", face_count=0)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # ── Human face cascades ──────────────────────────────────────────
    frontal_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # type: ignore[attr-defined]
    )
    alt_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"  # type: ignore[attr-defined]
    )
    profile_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_profileface.xml"  # type: ignore[attr-defined]
    )

    # ── Anime / cartoon face cascade ─────────────────────────────────
    anime_cascade = cv2.CascadeClassifier(_ANIME_CASCADE_PATH)

    def _detect(
        casc: cv2.CascadeClassifier,
        scale: float = 1.1,
        neighbours: int = 5,
        min_px: int = 30,
    ) -> list[tuple[int, int, int, int]]:
        if casc.empty():
            return []
        detections = casc.detectMultiScale(
            gray,
            scaleFactor=scale,
            minNeighbors=neighbours,
            minSize=(min_px, min_px),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        if len(detections) == 0:
            return []
        return [(int(x), int(y), int(ww), int(hh)) for x, y, ww, hh in detections]

    # Run all detectors — standard params first, then a sensitive pass
    all_faces: list[tuple[int, int, int, int]] = []

    # 1. Frontal (default)
    all_faces = _deduplicate(all_faces, _detect(frontal_cascade))

    # 2. Frontal alt2 — more sensitive, catches small / partially occluded faces
    all_faces = _deduplicate(all_faces, _detect(alt_cascade, scale=1.05, neighbours=3, min_px=20))

    # 3. Profile faces
    all_faces = _deduplicate(all_faces, _detect(profile_cascade))

    # 4. Anime / cartoon faces
    all_faces = _deduplicate(all_faces, _detect(anime_cascade, scale=1.1, neighbours=3, min_px=24))

    face_count = len(all_faces)
    face_regions = [FaceRegion(x=x, y=y, w=ww, h=hh) for x, y, ww, hh in all_faces]

    if face_count == 0:
        image_type = "object"
    else:
        # Calculate the proportion of image area covered by faces
        face_area = sum(r.w * r.h for r in face_regions)
        total_area = w * h
        face_ratio = face_area / max(total_area, 1)
        # If faces cover >10% of the image, it's a face-dominant image
        image_type = "face" if face_ratio > 0.10 else "mixed"

    return ClassificationResult(
        image_type=image_type,
        face_count=face_count,
        face_regions=face_regions,
    )

