import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from app.analyzers.pipeline import AnalysisPipeline

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class AnalysisResponse(BaseModel):
    overall_score: float
    overall_verdict: str
    analyzers: list[dict[str, Any]]
    image_type: str = "object"        # "face" | "object" | "mixed"
    face_count: int = 0
    face_regions: list[dict[str, Any]] = []     # [{x, y, w, h}, ...]


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)) -> AnalysisResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    try:
        with Image.open(BytesIO(contents)) as img:
            img.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image") from exc

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        pipeline = AnalysisPipeline()
        result = pipeline.run(tmp_path)
        return AnalysisResponse(**result.to_dict())
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get("/analyzers")
async def list_analyzers() -> dict[str, Any]:
    pipeline = AnalysisPipeline()
    return {
        "analyzers": [
            {"name": a.name, "description": a.__class__.__doc__ or ""}
            for a in pipeline.analyzers
        ]
    }
