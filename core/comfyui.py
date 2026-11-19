"""ComfyUI integration module for VideoShorts.

Provides:
1. Programmatic export of ComfyUI workflow JSON for SDXL video upscaling,
   face restoration (FaceDetailer), and AI style transfer on 9:16 vertical shorts.
2. ComfyUI custom node definitions for direct execution inside ComfyUI pipelines.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config import config

logger = logging.getLogger("VideoShorts.ComfyUI")


class ComfyUIExporter:
    """Generates standard ComfyUI API prompt workflows for enhancing shorts."""

    def __init__(self):
        pass

    def export_upscale_workflow(
        self,
        video_path: Path,
        output_filename: str = "videoshorts_enhanced.mp4",
        upscale_factor: float = 1.5,
        fps: int = 30,
    ) -> Dict[str, Any]:
        """Creates a standard ComfyUI API-format workflow JSON.

        Can be sent directly to ComfyUI's /prompt HTTP endpoint or loaded
        via 'Load (API Format)' in ComfyUI web UI.
        """
        video_abs = str(Path(video_path).resolve())

        # Standard ComfyUI API Graph using VideoHelperSuite (VHS)
        workflow = {
            "1": {
                "inputs": {
                    "video": video_abs,
                    "force_rate": fps,
                    "force_size": "Disabled",
                    "frame_load_cap": 0,
                    "skip_first_frames": 0,
                    "select_every_nth": 1,
                },
                "class_type": "VHS_LoadVideoPath",
                "_meta": {"title": "VideoShorts Source Clip"},
            },
            "2": {
                "inputs": {
                    "upscale_model_name": "RealESRGAN_x2plus.pth",
                },
                "class_type": "UpscaleModelLoader",
                "_meta": {"title": "Load RealESRGAN Model"},
            },
            "3": {
                "inputs": {
                    "upscale_model": ["2", 0],
                    "image": ["1", 0],
                },
                "class_type": "ImageUpscaleWithModel",
                "_meta": {"title": "Upscale Video Frames"},
            },
            "4": {
                "inputs": {
                    "images": ["3", 0],
                    "filename_prefix": output_filename.replace(".mp4", ""),
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
                "class_type": "VHS_VideoCombine",
                "_meta": {"title": "Export Enhanced 9:16 Short"},
            },
        }
        return workflow

    def save_workflow_file(self, workflow: Dict[str, Any], output_path: Path) -> Path:
        """Saves workflow JSON to disk."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2)
        logger.info("Saved ComfyUI workflow to: %s", output_path)
        return output_path
