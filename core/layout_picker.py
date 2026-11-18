"""Layout Picker: samples frames and determines the optimal 9:16 layout structure."""

import cv2
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import config
from core.llm import LLMClient

logger = logging.getLogger("VideoShorts.LayoutPicker")


class LayoutPicker:
    """Samples video frames and selects the best 9:16 framing layout."""

    LAYOUT_TRACK = "TRACK"           # Single speaker face tracking
    LAYOUT_SPLIT = "SPLIT"           # Two speakers stacked vertically
    LAYOUT_SCREENCAST = "SCREENCAST" # Screen capture + speaker circle
    LAYOUT_GENERAL = "GENERAL"       # Center crop with blurred background letterboxing

    def __init__(self, temp_dir: Optional[Path] = None, llm_client: Optional[LLMClient] = None):
        self.temp_dir = temp_dir or config.TEMP_DIR
        self.llm = llm_client or LLMClient()

    def determine_layout(
        self,
        video_path: Path,
        duration: float,
        num_samples: int = 12,
    ) -> Dict[str, Any]:
        """Extracts sampled frames and computes layout decision."""
        sample_dir = self.temp_dir / f"layout_samples_{video_path.stem}"
        sample_dir.mkdir(parents=True, exist_ok=True)

        frames = self._extract_sample_frames(video_path, duration, num_samples, sample_dir)
        if not frames:
            logger.warning("No frames extracted; defaulting to TRACK layout")
            return {"layout": self.LAYOUT_TRACK, "confidence": 0.5, "reason": "Default fallback"}

        # Local Computer Vision heuristic (Face count & distribution)
        cv_decision = self._analyze_frames_cv(frames)
        logger.info("Local CV layout analysis: %s (avg faces: %.1f)", cv_decision["layout"], cv_decision.get("avg_faces", 0.0))

        return cv_decision

    def _extract_sample_frames(
        self,
        video_path: Path,
        duration: float,
        num_samples: int,
        out_dir: Path,
    ) -> List[Path]:
        """Evenly extracts 12 frames scaled to 1024px width."""
        step = duration / (num_samples + 1)
        extracted: List[Path] = []

        for i in range(1, num_samples + 1):
            ts = i * step
            out_img = out_dir / f"frame_{i:02d}.jpg"
            if not out_img.exists():
                cmd = [
                    "ffmpeg",
                    "-ss", f"{ts:.2f}",
                    "-i", str(video_path),
                    "-vframes", "1",
                    "-vf", "scale=1024:-1",
                    "-q:v", "3",
                    "-y",
                    str(out_img),
                ]
                subprocess.run(cmd, capture_output=True)

            if out_img.exists() and out_img.stat().st_size > 0:
                extracted.append(out_img)

        return extracted

    def _analyze_frames_cv(self, frame_paths: List[Path]) -> Dict[str, Any]:
        """Uses OpenCV Haar Cascade / face detection to count faces across frames."""
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        face_counts = []

        for f_path in frame_paths:
            img = cv2.imread(str(f_path))
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            face_counts.append(len(faces))

        if not face_counts:
            return {"layout": self.LAYOUT_GENERAL, "avg_faces": 0.0}

        avg_faces = sum(face_counts) / len(face_counts)
        max_faces = max(face_counts)

        # Decision logic
        if avg_faces >= 1.5 or max_faces >= 2:
            # Consistent multiple people in frame -> SPLIT (stacked podcast layout)
            return {
                "layout": self.LAYOUT_SPLIT,
                "avg_faces": avg_faces,
                "confidence": 0.85,
                "reason": f"Detected dual speakers (average {avg_faces:.1f} faces per frame)",
            }
        elif avg_faces >= 0.5:
            # Single speaker -> TRACK (solo face-tracking 9:16 crop)
            return {
                "layout": self.LAYOUT_TRACK,
                "avg_faces": avg_faces,
                "confidence": 0.90,
                "reason": "Single primary speaker detected",
            }
        else:
            # Low face detection (screen tutorial, presentation, or wide landscape)
            return {
                "layout": self.LAYOUT_GENERAL,
                "avg_faces": avg_faces,
                "confidence": 0.70,
                "reason": "No prominent faces found; applying general 9:16 crop with blurred borders",
            }
