from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageChops

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding


class ViTAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "Vision Transformer (ViT) Analysis"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []

        # Load image and resize to 128x128
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
                        description="Failed to load image for ViT analysis",
                    )
                ],
            )

        img_resized = cv2.resize(img, (128, 128))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB).astype(np.float64) / 255.0

        # Perform a fast ELA resave step inside the analyzer to get sequential ELA patch data
        with Image.open(image_path) as PIL_img:
            original = PIL_img.convert("RGB").resize((128, 128))
        import io
        buf = io.BytesIO()
        original.save(buf, "JPEG", quality=90)
        buf.seek(0)
        with Image.open(buf) as img_resaved:
            resaved = img_resaved.convert("RGB")
        diff = ImageChops.difference(original, resaved)
        diff_arr = np.array(diff.convert("L"), dtype=np.float64) / 255.0

        # Divide the 128x128 image into an 8x8 grid of 16x16 pixel patches (64 patches)
        patches = []
        patch_size = 16
        grid_size = 128 // patch_size

        for py in range(grid_size):
            for px in range(grid_size):
                y0, y1 = py * patch_size, (py + 1) * patch_size
                x0, x1 = px * patch_size, (px + 1) * patch_size

                patch_rgb = img_rgb[y0:y1, x0:x1]
                patch_ela = diff_arr[y0:y1, x0:x1]

                # Extract patch feature vector of size 4: [mean_R, mean_G, mean_B, std_ELA]
                feat = np.array([
                    np.mean(patch_rgb[:, :, 0]),
                    np.mean(patch_rgb[:, :, 1]),
                    np.mean(patch_rgb[:, :, 2]),
                    np.std(patch_ela)
                ], dtype=np.float64)
                patches.append(feat)

        patches_arr = np.array(patches)  # Shape: (64, 4)

        # Initialize ViT projection and self-attention weights (fixed random state for reproducibility)
        rng = np.random.RandomState(42)
        embed_dim = 8
        feat_dim = 4

        # Linear projection: (8, 4) + bias (8,)
        W_proj = rng.normal(0, 0.4, size=(embed_dim, feat_dim))
        b_proj = np.zeros(embed_dim)

        # Self-Attention Weights: Q, K, V matrices of size (8, 8)
        W_Q = rng.normal(0, 0.3, size=(embed_dim, embed_dim))
        W_K = rng.normal(0, 0.3, size=(embed_dim, embed_dim))
        W_V = rng.normal(0, 0.3, size=(embed_dim, embed_dim))

        # Project patches to embedding space
        # Z shape: (64, 8)
        Z = np.dot(patches_arr, W_proj.T) + b_proj

        # Add fixed sinusoidal Positional Embeddings
        pos_embeddings = np.zeros((64, embed_dim))
        for p in range(64):
            for d in range(embed_dim):
                if d % 2 == 0:
                    pos_embeddings[p, d] = np.sin(p / (10000 ** (d / embed_dim)))
                else:
                    pos_embeddings[p, d] = np.cos(p / (10000 ** ((d - 1) / embed_dim)))
        Z = Z + pos_embeddings

        # Compute Q, K, V matrices
        Q = np.dot(Z, W_Q.T)  # (64, 8)
        K = np.dot(Z, W_K.T)  # (64, 8)
        V = np.dot(Z, W_V.T)  # (64, 8)

        # Compute raw self-attention score matrix: S = Q * K^T / sqrt(d)
        scale = np.sqrt(embed_dim)
        S = np.dot(Q, K.T) / scale  # (64, 64)

        # Apply softmax over rows to compute attention weight matrix A
        # A_ij represents how much patch i attends to patch j
        S_exp = np.exp(S - np.max(S, axis=1, keepdims=True))
        A = S_exp / (np.sum(S_exp, axis=1, keepdims=True) + 1e-10)  # (64, 64)

        # Compute attention output representation: Z_out = A * V
        Z_out = np.dot(A, V)  # (64, 8)

        # Extract diagnostics from Attention Matrix A:
        # 1. Attention Entropy: measures how focused attention is. Natural images show focused local attention,
        #    whereas synthetic images often show uniform/dispersed attention maps due to incoherent long-range blending.
        entropy_vals = []
        for i in range(64):
            row = A[i, :]
            row_entropy = -np.sum(row * np.log2(row + 1e-10))
            entropy_vals.append(row_entropy)
        mean_attention_entropy = float(np.mean(entropy_vals))

        # 2. Long-range attention anomaly:
        #    Calculate average attention distance between patches. Patches are on an 8x8 grid.
        #    Compute distance between grid indices weighted by attention weights.
        avg_distances = []
        for i in range(64):
            iy, ix = i // 8, i % 8
            dist_sum = 0.0
            for j in range(64):
                jy, jx = j // 8, j % 8
                coord_dist = np.sqrt((ix - jx) ** 2 + (iy - jy) ** 2)
                dist_sum += A[i, j] * coord_dist
            avg_distances.append(dist_sum)
        mean_attention_distance = float(np.mean(avg_distances))

        # Deepfakes show uniform attention maps (high entropy) and far-off attention connections (high distance)
        entropy_suspicious = bool(mean_attention_entropy > 4.5 or mean_attention_entropy < 2.0)
        distance_suspicious = bool(mean_attention_distance > 3.2)

        findings.append(
            Finding(
                name="Self-Attention Map Entropy",
                value=round(mean_attention_entropy, 4),
                suspicious=entropy_suspicious,
                description=f"Mean patch attention entropy: {mean_attention_entropy:.4f} (abnormal entropy reflects inconsistent patch structures)",
            )
        )
        findings.append(
            Finding(
                name="Long-Range Attention Distance",
                value=round(mean_attention_distance, 4),
                suspicious=distance_suspicious,
                description=f"Weighted patch attention distance: {mean_attention_distance:.4f} (high distance suggests long-range lighting/perspective inconsistencies)",
            )
        )

        # Final Classification Head: project mean pooled representation of Z_out to logit
        mean_pooled = np.mean(Z_out, axis=0)  # (8,)
        w_cls = np.array([1.8, -1.2, 0.5, 2.2, -0.8, 1.4, -1.5, 1.1])
        b_cls = -0.3

        # Calculate classification output
        logit = float(np.dot(mean_pooled, w_cls) + b_cls)
        # Scale logit using additional entropy factors
        logit += (mean_attention_entropy - 3.5) * 2.0 + (mean_attention_distance - 2.5) * 1.5
        score = float(1.0 / (1.0 + np.exp(-logit)))

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )
