# DEEPFAKE-AI- 🛡️

Multi-modal deepfake and AI-generated image detection system combining forensic signal processing, frequency domain analysis, and deep learning models with a modern React web interface.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![React](https://img.shields.io/badge/React-18-20232A?style=flat&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Overview

Generative AI models (GANs, Diffusion models) leave subtle footprints across different image representations. **DEEPFAKE-AI-** uses a multi-layered detection pipeline that combines non-ML forensic signal processing with neural network classifiers to assess whether an uploaded image is authentic, suspicious, or likely AI-generated.

---

## 🔍 Forensic & ML Analyzers

The pipeline evaluates images across 14 specialized detectors:

| Analyzer | Method / Technique |
| :--- | :--- |
| **Error Level Analysis (ELA)** | Analyzes compression artifact discrepancies after standard JPEG re-saving. |
| **Frequency Domain (FFT)** | 2D Fast Fourier Transform looking for periodic grid patterns & high-frequency spectral falloff. |
| **Noise Pattern Analysis** | Spatial noise residue extraction and energy variance uniformity across regions. |
| **JPEG Compression Forensics** | DCT coefficient zero distributions, quantization matrix checks, and 8x8 grid misalignments. |
| **Color Consistency** | Inter-channel RGB covariance, hue/saturation entropy, and color gamut boundaries. |
| **EXIF & Metadata Inspection** | Camera hardware tags, timestamp validation, software tags, and thumbnail consistency. |
| **SynthID Watermark Detection** | Frequency and LSB anomaly checks for synthetic generation watermarks. |
| **Digital Provenance Verification** | Cryptographic signature and content credentials (C2PA) verification. |
| **AI Texture Analysis** | Local Binary Patterns (LBP) and structural micro-texture irregularities. |
| **CNN Feature Analysis** | Deep convolutional neural network feature representations for synthetic artifacts. |
| **Vision Transformer (ViT)** | Self-attention patch analysis for global structural coherence. |
| **RNN Sequential Analysis** | Multi-frame / slice sequential anomaly classification. |
| **Classical ML Classifier** | Handcrafted statistical feature extraction evaluated with SVM / Random Forest. |
| **Ensemble Model Analyzer** | Aggregated weighted decision matrix combining all detector signals into an overall risk score. |

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & npm

---

### 1. Backend Setup (FastAPI)

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run the backend server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
