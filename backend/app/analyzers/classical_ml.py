from pathlib import Path

import cv2
import exifread
import numpy as np
from PIL import Image, ImageChops

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding


class ClassicalMLAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "Classical ML Classification"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        # 1. Feature Extraction
        # Feature 1: Metadata stripped check (EXIF data availability)
        try:
            with open(image_path, "rb") as f:
                tags = exifread.process_file(f, details=False)
            num_tags = len(tags)
        except Exception:
            num_tags = 0
        feat_metadata_stripped = 1.0 if num_tags < 3 else 0.0

        # Load image for visual features
        img = cv2.imread(str(image_path))
        if img is None:
            return AnalysisResult(
                analyzer=self.name,
                score=0.5,
                verdict=self._score_to_verdict(0.5),
                findings=[
                    Finding(
                        name="Error",
                        value="Could not load image",
                        suspicious=True,
                        description="Failed to load image for Classical ML analysis",
                    )
                ],
            )

        h, w, _ = img.shape
        img_resized = cv2.resize(img, (128, 128))
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

        # Feature 2: ELA (Error Level Analysis) variance
        with Image.open(image_path) as PIL_img:
            original = PIL_img.convert("RGB").resize((128, 128))
        import io
        buf = io.BytesIO()
        original.save(buf, "JPEG", quality=90)
        buf.seek(0)
        with Image.open(buf) as img_resaved:
            resaved = img_resaved.convert("RGB")
        diff = ImageChops.difference(original, resaved)
        diff_arr = np.array(diff, dtype=np.float64)
        feat_ela_var = float(np.var(diff_arr))

        # Feature 3: High-frequency noise level (estimate from Laplacian)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        feat_noise_level = float(np.std(laplacian))

        # Feature 4: Saturation entropy (color variety)
        hsv = cv2.cvtColor(img_resized, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:, :, 1]
        s_hist = cv2.calcHist([s_channel], [0], None, [32], [0, 256]).flatten()
        s_hist_norm = s_hist / max(float(s_hist.sum()), 1.0)
        feat_sat_entropy = float(-np.sum(s_hist_norm * np.log2(s_hist_norm + 1e-10)))

        # Feature 5: Edge strength
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        feat_edge_strength = float(np.mean(np.sqrt(sobel_x**2 + sobel_y**2)))

        # Collect features into vector: [metadata_stripped, ela_var, noise_level, sat_entropy, edge_strength]
        features = np.array([
            feat_metadata_stripped,
            feat_ela_var,
            feat_noise_level,
            feat_sat_entropy,
            feat_edge_strength
        ], dtype=np.float64)

        # 2. Ensemble Classifier Models
        # Model A: Logistic Regression Classifier
        # Weights: higher metadata stripping, ELA variance, and edge strength boost fake score;
        #          high natural noise and saturation entropy boost authentic score.
        w_lr = np.array([1.5, 0.05, -0.15, -1.2, 0.08], dtype=np.float64)
        b_lr = -0.5
        lr_z = float(np.dot(features, w_lr) + b_lr)
        prob_lr = float(1.0 / (1.0 + np.exp(-lr_z)))

        # Model B: Linear Support Vector Machine (SVM)
        # Decision boundary plane SVM score
        w_svm = np.array([0.8, 0.02, -0.08, -0.6, 0.04], dtype=np.float64)
        b_svm = -0.3
        svm_dist = float(np.dot(features, w_svm) + b_svm)
        # Map margin distance to a probability-like score (0 to 1 range)
        prob_svm = float(1.0 / (1.0 + np.exp(-svm_dist)))

        # Model C: Decision Tree (Rule-based decision tree)
        dt_signals = 0.0
        if feat_ela_var > 120.0:
            dt_signals += 0.4
        if feat_metadata_stripped > 0.5 and feat_sat_entropy < 2.0:
            dt_signals += 0.4
        if feat_noise_level < 8.0:
            dt_signals += 0.2
        prob_dt = dt_signals

        # Combine scores (Ensemble average)
        ensemble_score = float(0.4 * prob_lr + 0.4 * prob_svm + 0.2 * prob_dt)

        findings.append(
            Finding(
                name="SVM Decision Margin",
                value=round(svm_dist, 4),
                suspicious=svm_dist > 0.0,
                description=f"Distance to SVM hyper-plane: {svm_dist:.4f} (positive margins denote classification of editing/manipulation)",
            )
        )
        findings.append(
            Finding(
                name="Logistic Probability",
                value=round(prob_lr, 4),
                suspicious=prob_lr > 0.6,
                description=f"Logistic Regression prediction: {prob_lr * 100:.1f}% risk score",
            )
        )
        findings.append(
            Finding(
                name="Decision Tree Consensus",
                value=round(prob_dt, 4),
                suspicious=prob_dt > 0.5,
                description=f"Ensemble rules score: {prob_dt:.2f} (higher indicates multiple forensic thresholds violated)",
            )
        )

        return AnalysisResult(
            analyzer=self.name,
            score=ensemble_score,
            verdict=self._score_to_verdict(ensemble_score),
            findings=findings,
        )
