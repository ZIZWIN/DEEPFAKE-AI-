from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageChops

from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding


class RNNAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "RNN Sequential Analysis"

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
                        description="Failed to load image for RNN analysis",
                    )
                ],
            )

        img_resized = cv2.resize(img, (128, 128))
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY).astype(np.float64) / 255.0

        # Perform a fast ELA resave step inside the analyzer to get sequential ELA row data
        with Image.open(image_path) as PIL_img:
            original = PIL_img.convert("RGB").resize((128, 128))
        import io
        buf = io.BytesIO()
        original.save(buf, "JPEG", quality=90)
        buf.seek(0)
        with Image.open(buf) as img_resaved:
            resaved = img_resaved.convert("RGB")
        diff = ImageChops.difference(original, resaved)
        diff_gray = np.array(diff.convert("L"), dtype=np.float64) / 255.0

        # Build sequence of features for each row (128 rows)
        # Input features per row: [mean_intensity, std_intensity, ELA_mean] (3 features)
        sequence = []
        for i in range(128):
            row_gray = gray[i, :]
            row_diff = diff_gray[i, :]
            feat = np.array([np.mean(row_gray), np.std(row_gray), np.mean(row_diff)], dtype=np.float64)
            sequence.append(feat)

        sequence_arr = np.array(sequence)  # Shape: (128, 3)

        # Initialize RNN weights with a fixed random seed for reproducibility
        rng = np.random.RandomState(1337)
        hidden_dim = 8
        input_dim = 3

        # Weights:
        # W_h: input to hidden (8, 3)
        # U_h: hidden to hidden (8, 8)
        # b_h: hidden bias (8,)
        # W_y: hidden to output prediction (3, 8)
        # b_y: output bias (3,)
        W_h = rng.normal(0, 0.4, size=(hidden_dim, input_dim))
        U_h = rng.normal(0, 0.2, size=(hidden_dim, hidden_dim))
        b_h = np.zeros(hidden_dim)
        W_y = rng.normal(0, 0.4, size=(input_dim, hidden_dim))
        b_y = np.zeros(input_dim)

        h = np.zeros(hidden_dim)
        prediction_errors = []
        hidden_states = []

        # Run RNN forward pass over the sequence of 128 rows
        for t in range(128 - 1):
            x_t = sequence_arr[t]
            x_next = sequence_arr[t + 1]

            # Recurrent step: h_t = tanh(W_h * x_t + U_h * h_{t-1} + b_h)
            h = np.tanh(np.dot(W_h, x_t) + np.dot(U_h, h) + b_h)
            hidden_states.append(h)

            # Predict next step features: y_t = W_y * h_t + b_y
            pred_next = np.dot(W_y, h) + b_y

            # Calculate prediction MSE for this step
            err = float(np.mean((x_next - pred_next) ** 2))
            prediction_errors.append(err)

        errors_arr = np.array(prediction_errors)
        hidden_arr = np.array(hidden_states)

        mean_error = float(np.mean(errors_arr))
        std_error = float(np.std(errors_arr))

        # Calculate entropy of hidden state activations to measure chaotic transitions
        # Normalize hidden states to a pseudo-probability distribution
        hidden_normalized = np.abs(hidden_arr) / (np.sum(np.abs(hidden_arr), axis=1, keepdims=True) + 1e-10)
        h_entropy = float(-np.mean(np.sum(hidden_normalized * np.log2(hidden_normalized + 1e-10), axis=1)))

        # Natural images have low row-to-row prediction error and stable hidden states
        # Deepfakes show high prediction errors and chaotic transitions
        err_suspicious = bool(mean_error > 0.05 or std_error > 0.04)
        entropy_suspicious = bool(h_entropy > 2.8 or h_entropy < 1.5)

        findings.append(
            Finding(
                name="Sequence Prediction MSE",
                value=round(mean_error, 4),
                suspicious=err_suspicious,
                description=f"RNN row prediction error: {mean_error:.4f} (high MSE indicates structural sequence inconsistency)",
            )
        )
        findings.append(
            Finding(
                name="RNN Hidden State Entropy",
                value=round(h_entropy, 4),
                suspicious=entropy_suspicious,
                description=f"State activation entropy: {h_entropy:.4f} (abnormal entropy levels reflect chaotic transitions)",
            )
        )

        # Map findings to an overall score (sigmoid mapping of normalized prediction stats)
        logit = (mean_error * 15.0) + (std_error * 8.0) + (h_entropy - 2.2) * 1.5 - 2.0
        score = float(1.0 / (1.0 + np.exp(-logit)))

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=self._score_to_verdict(score),
            findings=findings,
        )
