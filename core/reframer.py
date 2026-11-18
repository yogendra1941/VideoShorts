"""Smart 9:16 reframer: face tracking with Exponential Moving Average (EMA) smoothing."""

import cv2
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("VideoShorts.Reframer")


class SmartReframer:
    """Calculates smoothed 9:16 vertical crop boxes centered on active speakers."""

    def __init__(
        self,
        ema_alpha: float = 0.15,
        target_aspect_ratio: float = 9.0 / 16.0,
        sample_fps: float = 5.0,
    ):
        self.ema_alpha = ema_alpha
        self.target_aspect_ratio = target_aspect_ratio
        self.sample_fps = sample_fps
        self._mp_face = None

    def _init_detector(self):
        """Initializes MediaPipe Face Detection with OpenCV fallback."""
        if self._mp_face is not None:
            return

        try:
            import mediapipe as mp
            self._mp_face = mp.solutions.face_detection.FaceDetection(
                model_selection=1,  # 1 for full-range / distance (better for podcasts/interviews)
                min_detection_confidence=0.5,
            )
            logger.info("Initialized MediaPipe Face Detection")
        except Exception as e:
            logger.warning("MediaPipe initialization failed (%s); using OpenCV Haar Cascade fallback", e)
            self._mp_face = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

    def calculate_crop_box(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        src_width: int = 1920,
        src_height: int = 1080,
        scene_cuts: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Tracks the speaker across [start_time, end_time] and computes smoothed 9:16 crop box."""
        self._init_detector()

        # Desired 9:16 dimensions
        crop_h = src_height
        crop_w = int(src_height * self.target_aspect_ratio)
        if crop_w % 2 != 0:
            crop_w += 1
        max_x = max(0, src_width - crop_w)
        default_x = max_x // 2

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.warning("Failed to open video for reframing. Using center crop.")
            return {"x": default_x, "y": 0, "w": crop_w, "h": crop_h, "is_dynamic": False}

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_step = max(1, int(fps / self.sample_fps))

        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        face_centers_x: List[float] = []
        current_frame = start_frame

        while current_frame <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            if (current_frame - start_frame) % frame_step == 0:
                center_x = self._detect_primary_face_x(frame, src_width)
                if center_x is not None:
                    face_centers_x.append(center_x)

            current_frame += 1

        cap.release()

        if not face_centers_x:
            logger.info("No faces detected in clip duration; using center 9:16 crop")
            return {"x": default_x, "y": 0, "w": crop_w, "h": crop_h, "is_dynamic": False}

        # Apply Exponential Moving Average (EMA) Smoothing
        smoothed_x = self._apply_ema_smoothing(face_centers_x, crop_w, max_x)
        avg_target_x = int(round(np.mean(smoothed_x)))
        clamped_x = max(0, min(max_x, avg_target_x))

        logger.info(
            "Computed smoothed face crop: x=%d (range: %d-%d), w=%d, h=%d",
            clamped_x,
            int(min(smoothed_x)),
            int(max(smoothed_x)),
            crop_w,
            crop_h,
        )

        return {
            "x": clamped_x,
            "y": 0,
            "w": crop_w,
            "h": crop_h,
            "is_dynamic": False,
        }

    def _detect_primary_face_x(self, frame: np.ndarray, src_width: int) -> Optional[float]:
        """Detects the largest/most prominent face and returns its horizontal center."""
        # MediaPipe path
        if hasattr(self._mp_face, "process"):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self._mp_face.process(rgb)
            if results.detections:
                # Find largest face by bounding box area
                best_box = max(
                    results.detections,
                    key=lambda d: d.location_data.relative_bounding_box.width
                    * d.location_data.relative_bounding_box.height,
                )
                bbox = best_box.location_data.relative_bounding_box
                center_x = (bbox.xmin + bbox.width / 2.0) * src_width
                return center_x
            return None

        # OpenCV Haar cascade fallback
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._mp_face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) > 0:
            best_face = max(faces, key=lambda f: f[2] * f[3])
            return best_face[0] + (best_face[2] / 2.0)

        return None

    def _apply_ema_smoothing(
        self,
        centers: List[float],
        crop_w: int,
        max_x: int,
    ) -> List[float]:
        """Applies EMA filter to face coordinates to prevent camera micro-jitter."""
        smoothed: List[float] = []
        current_val = centers[0] - (crop_w / 2.0)

        for raw_center in centers:
            raw_target_x = raw_center - (crop_w / 2.0)
            current_val = (self.ema_alpha * raw_target_x) + ((1.0 - self.ema_alpha) * current_val)
            clamped = max(0.0, min(float(max_x), current_val))
            smoothed.append(clamped)

        return smoothed
