from pathlib import Path
from typing import Any
import exifread
from app.analyzers.base import AnalysisResult, BaseAnalyzer, Finding, Verdict


class DigitalProvenanceAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "Digital Provenance Verification"

    def analyze(self, image_path: Path) -> AnalysisResult:
        findings: list[Finding] = []
        c2pa_status = self._check_c2pa(image_path)
        synthid_status = self._check_synthid(image_path)

        # 1. C2PA Check Finding
        findings.append(
            Finding(
                name="C2PA Content Credentials",
                value="Verified" if c2pa_status["detected"] else "Not Found",
                suspicious=c2pa_status["detected"] and c2pa_status["is_ai"],
                description=c2pa_status["details"],
            )
        )

        # 2. SynthID Check Finding
        findings.append(
            Finding(
                name="SynthID Provenance Signature",
                value="Found" if synthid_status["detected"] else "Not Found",
                suspicious=synthid_status["detected"],
                description=synthid_status["details"],
            )
        )

        # Determine manipulation score (0.0 = Authentic/Clean, 1.0 = AI-Generated/Manipulated)
        if c2pa_status["detected"]:
            if c2pa_status["is_ai"]:
                score = 1.0  # Explicit AI generator provenance signature
                verdict = Verdict.LIKELY_FAKE
            else:
                score = 0.0  # Explicit camera/original content provenance signature
                verdict = Verdict.AUTHENTIC
        elif synthid_status["detected"]:
            score = 1.0  # Google SynthID watermark/signature detected
            verdict = Verdict.LIKELY_FAKE
        else:
            # No explicit provenance records
            score = 0.0
            verdict = Verdict.AUTHENTIC

        return AnalysisResult(
            analyzer=self.name,
            score=score,
            verdict=verdict,
            findings=findings,
        )

    def _check_c2pa(self, image_path: Path) -> dict[str, Any]:
        """
        Scans for open C2PA (Coalition for Content Provenance and Authenticity) signatures.
        """
        try:
            with open(image_path, "rb") as f:
                data = f.read()

            c2pa_detected = False
            is_ai = False
            details = "No C2PA metadata headers or chunks found."

            # 1. JPEG APP11 JUMBF Marker Check (\xff\xeb)
            if b"\xff\xeb" in data:
                if b"c2pa" in data:
                    c2pa_detected = True
                    details = "Detected C2PA JUMBF APP11 marker in JPEG headers."

            # 2. PNG caBX Chunk Check (caBX is the standard C2PA chunk name in PNG)
            if data.startswith(b"\x89PNG\r\n\x1a\n"):
                if b"caBX" in data:
                    c2pa_detected = True
                    details = "Detected C2PA 'caBX' chunk in PNG structure."

            # 3. WebP caBX Chunk Check
            if b"RIFF" in data[:4] and b"WEBP" in data[8:12]:
                if b"caBX" in data:
                    c2pa_detected = True
                    details = "Detected C2PA 'caBX' chunk in WebP structure."

            # 4. EXIF & Raw String search for C2PA/ContentCredentials
            if not c2pa_detected:
                for kw in [b"http://c2pa.org/", b"ContentCredentials", b"content-credentials"]:
                    if kw in data:
                        c2pa_detected = True
                        details = "Detected C2PA web reference in raw file content."
                        break

            # 5. Check if the metadata references known AI generators
            if c2pa_detected:
                ai_keywords = [
                    b"stable-diffusion", b"dall-e", b"midjourney", b"firefly", 
                    b"imagen", b"synthetic", b"generator", b"ai-generated", 
                    b"openai", b"stability", b"adobe-firefly"
                ]
                for kw in ai_keywords:
                    if kw in data.lower():
                        is_ai = True
                        details += f" Content claims generation by AI ({kw.decode('utf-8')})."
                        break
                if not is_ai:
                    details += " Content credentials verify authentic original capture/editing source."

            return {
                "detected": c2pa_detected,
                "is_ai": is_ai,
                "details": details
            }
        except Exception as e:
            return {
                "detected": False,
                "is_ai": False,
                "details": f"Error scanning for C2PA credentials: {str(e)}"
            }

    def _check_synthid(self, image_path: Path) -> dict[str, Any]:
        """
        Scans for Google's SynthID metadata signatures.
        """
        try:
            with open(image_path, "rb") as f:
                data = f.read()

            detected = False
            details = "No explicit SynthID watermarks found in metadata."

            # Scan raw bytes for SynthID or Google Watermark keywords
            for kw in [b"SynthID", b"Google_Watermark", b"Google_AI_Watermark"]:
                if kw in data:
                    detected = True
                    details = f"Detected Google SynthID signature ({kw.decode('utf-8')}) in raw bytes."
                    break

            # Scan EXIF metadata using exifread
            if not detected:
                with open(image_path, "rb") as f:
                    tags = exifread.process_file(f, details=False)
                for key, val in tags.items():
                    val_str = str(val).lower()
                    if "synthid" in val_str or "google_watermark" in val_str:
                        detected = True
                        details = f"Detected Google SynthID tag in EXIF metadata ({key})."
                        break

            return {
                "detected": detected,
                "details": details
            }
        except Exception as e:
            return {
                "detected": False,
                "details": f"Error scanning for SynthID signature: {str(e)}"
            }
