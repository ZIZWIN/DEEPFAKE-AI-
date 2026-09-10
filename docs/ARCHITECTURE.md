# Deepfake Detector — Architecture

## Overview

A boilerplate for detecting AI-generated or manipulated images using **non-ML forensic methods**.
No neural networks are used — only signal processing, metadata analysis, and watermark detection.

## Detection Methods

| Analyzer | What it checks | Why it works |
|---|---|---|
| **EXIF Metadata** | Camera info, software tags, timestamps, GPS, thumbnails | AI images typically lack camera EXIF or contain editing software signatures |
| **Error Level Analysis (ELA)** | Compression artifact differences after re-save | Manipulated regions have different error levels than untouched areas |
| **Noise Pattern** | Spatial noise distribution, frequency energy | AI generators produce unnaturally uniform noise patterns |
| **Frequency Domain** | FFT spectral falloff, symmetry, periodic artifacts | GAN/diffusion models leave characteristic frequency signatures and grid artifacts |
| **JPEG Compression** | DCT coefficients, quantization tables, 8x8 block patterns | Double compression and synthetic content have distinct DCT fingerprints |
| **Color Consistency** | Channel correlations, hue/saturation entropy, spatial color variance | AI-generated images often have unusual color distributions |
| **SynthID** | Conservative local frequency/LSB anomaly checks | Official SynthID verification is not exposed here; use Google verification surfaces for proof |

## Scoring

Each analyzer produces a score from 0.0 (authentic) to 1.0 (likely fake).
A weighted combination produces an overall verdict:

- `< 0.3` → **Authentic**
- `0.3–0.6` → **Suspicious**
- `≥ 0.6` → **Likely Manipulated**

`Inconclusive` is reserved for analyzers that cannot run reliably, such as unsupported image
geometry or unreadable files. Inconclusive analyzer results are shown in the response but are
excluded from the weighted overall score.

## Project Structure

```
deepfake-detector/
├── backend/
│   ├── app/
│   │   ├── analyzers/          # Each detector is a standalone class
│   │   │   ├── base.py         # ABC + data models
│   │   │   ├── metadata.py
│   │   │   ├── error_level.py
│   │   │   ├── noise.py
│   │   │   ├── frequency.py
│   │   │   ├── compression.py
│   │   │   ├── color.py
│   │   │   ├── synthid.py
│   │   │   └── pipeline.py     # Orchestrates all analyzers
│   │   ├── routes/
│   │   │   └── analysis.py     # POST /api/v1/analyze
│   │   └── main.py
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── ImageUpload.tsx
│   │   │   ├── ResultsPanel.tsx
│   │   │   ├── AnalyzerCard.tsx
│   │   │   └── ScoreGauge.tsx
│   │   ├── utils/
│   │   │   ├── types.ts
│   │   │   └── verdict.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── docker-compose.yml
├── .env.example
└── docs/
    └── ARCHITECTURE.md
```

## Adding a New Analyzer

1. Create `backend/app/analyzers/my_analyzer.py`:

```python
from app.analyzers.base import BaseAnalyzer, AnalysisResult, Finding

class MyAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "My Custom Analyzer"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings = []
        # ... your analysis logic ...
        score = 0.0  # 0 = authentic, 1 = fake
        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )
```

2. Register it in `pipeline.py` by adding to `self.analyzers`.
3. Add a weight in `pipeline.py`'s `weights` dict.

## SynthID Integration

There is no general public image SynthID detection API integrated in this project. The
SynthID analyzer only reports conservative local pixel-pattern anomalies and labels them as
experimental. For official SynthID verification, use Gemini, Vertex AI Studio, or Google's
SynthID Detector portal when available.

## Limitations

- No face-specific detection (this is intentional — analyzes full images)
- No ML/DL models — purely forensic/signal-processing heuristics
- ELA and compression checks are JPEG-specific
- Local SynthID-like checks are not equivalent to Google's official detector
- Heuristics can produce false positives on heavily edited (but authentic) photos
