from pathlib import Path

import cv2
import numpy as np

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding


class CNNAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "CNN Feature Analysis"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        # Load and resize image to standardized size for CNN (128x128)
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
                        description="Failed to load image for CNN analysis",
                    )
                ],
            )

        h, w, _ = img.shape
        img_resized = cv2.resize(img, (128, 128))
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY).astype(np.float64) / 255.0

        # Define 4 distinct CNN kernels (filters) to detect forensic features
        # 1. Horizontal Sobel (detects horizontal boundaries/splicing)
        k1 = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
        # 2. Vertical Sobel (detects vertical boundaries/splicing)
        k2 = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
        # 3. Laplacian (high-frequency noise / sharpening artifacts)
        k3 = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64)
        # 4. GAN/Diffusion grid pattern detector (alternating checkerboard weights)
        k4 = np.array([[1, -1, 1], [-1, 1, -1], [1, -1, 1]], dtype=np.float64)

        kernels = [k1, k2, k3, k4]
        conv_maps = []

        # Layer 1: 2D Convolution (using cv2.filter2D for high performance)
        for k in kernels:
            conv = cv2.filter2D(gray, -1, k)
            conv_maps.append(conv)

        # Layer 2: ReLU Activation (np.maximum with 0)
        relu_maps = [np.maximum(m, 0.0) for m in conv_maps]

        # Layer 3: 2x2 Max Pooling (reduces map from 128x128 to 64x64)
        pooled_maps = []
        for m in relu_maps:
            # Reshape to 64x2x64x2 and take max over axes 1 and 3 to perform fast 2x2 pooling
            reshaped = m.reshape(64, 2, 64, 2)
            pooled = reshaped.max(axis=(1, 3))
            pooled_maps.append(pooled)

        # Extract features from pooled activations
        # Feature 0: Horizontal boundaries
        feat_h = pooled_maps[0]
        # Feature 1: Vertical boundaries
        feat_v = pooled_maps[1]
        # Feature 2: High-frequency details/noise
        feat_lap = pooled_maps[2]
        # Feature 3: Grid artifacts
        feat_grid = pooled_maps[3]

        mean_h = float(np.mean(feat_h))
        std_h = float(np.std(feat_h))
        mean_v = float(np.mean(feat_v))
        std_v = float(np.std(feat_v))
        mean_lap = float(np.mean(feat_lap))
        std_lap = float(np.std(feat_lap))
        mean_grid = float(np.mean(feat_grid))
        std_grid = float(np.std(feat_grid))

        # Check for abnormal edge/detail characteristics typical of deepfakes:
        # 1. GAN and diffusion images tend to have grid structures (higher mean/std of grid filter)
        # 2. AI generators often blur local textures, producing low Laplacian std in flat regions
        # 3. Splicing often creates unnatural sharp borders, leading to high horizontal/vertical edge spikes
        grid_suspicious = bool(mean_grid > 0.08 or std_grid > 0.12)
        lap_suspicious = bool(std_lap < 0.02 or std_lap > 0.18)
        edge_ratio = abs(mean_h - mean_v) / (max(mean_h + mean_v, 1e-5))
        edge_suspicious = bool(edge_ratio > 0.35)

        findings.append(
            Finding(
                name="Grid Artifact Activation",
                value=round(mean_grid, 4),
                suspicious=grid_suspicious,
                description=f"Mean grid pattern filter activation: {mean_grid:.4f} (high levels indicate checkerboard artifacts)",
            )
        )
        findings.append(
            Finding(
                name="Laplacian Detail Variance",
                value=round(std_lap, 4),
                suspicious=lap_suspicious,
                description=f"Standard deviation of details: {std_lap:.4f} (very low/high variance implies synthetic smoothing/sharpening)",
            )
        )
        findings.append(
            Finding(
                name="Edge Inconsistency Ratio",
                value=round(edge_ratio, 4),
                suspicious=edge_suspicious,
                description=f"Mismatched directional boundary ratio: {edge_ratio:.4f}",
            )
        )

        # Layer 4: Fully Connected Layer + Sigmoid
        # Combine extracted activations into a classification output logit.
        # Weights correspond to typical impact of each feature
        w_grid, w_lap, w_edge = 3.5, -2.5, 2.0
        bias = -0.5

        # Calculate logit input
        x_grid = mean_grid + std_grid
        x_lap = std_lap
        x_edge = edge_ratio

        # Higher grid and mismatched edges boost manipulation score; natural detail variance reduces it
        logit = (x_grid * w_grid) + (x_lap * w_lap) + (x_edge * w_edge) + bias
        score = float(1.0 / (1.0 + np.exp(-logit)))

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )
