"""VideoShorts ComfyUI Custom Node Pack.

Allows running VideoShorts highlight detection and 9:16 vertical reframing
directly inside ComfyUI workflows without external SaaS or paid API keys.
"""

import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, Tuple

logger = logging.getLogger("VideoShorts.ComfyUINode")


class VideoShortsHighlightNode:
    """ComfyUI Node: Takes video path or YouTube URL and returns viral 9:16 clips."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "source": ("STRING", {"default": "https://www.youtube.com/watch?v=...", "multiline": False}),
                "target_clips": ("INT", {"default": 3, "min": 1, "max": 10, "step": 1}),
                "brand_preset": (["cyber_neon", "hormozi_gold", "podcast_split", "bold", "minimal", "default"],),
                "server_url": ("STRING", {"default": "http://127.0.0.1:8000", "multiline": False}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("top_clip_path", "clip_title", "viral_score")
    FUNCTION = "generate_shorts"
    CATEGORY = "VideoShorts"

    def generate_shorts(self, source: str, target_clips: int, brand_preset: str, server_url: str) -> Tuple[str, str, int]:
        req_data = json.dumps({
            "source": source,
            "clips": target_clips,
            "brand": brand_preset,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{server_url.rstrip('/')}/api/jobs",
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            job_id = data.get("job_id", "")

        # Poll status
        import time
        for _ in range(120):
            time.sleep(3)
            stat_req = urllib.request.Request(f"{server_url.rstrip('/')}/api/status/{job_id}")
            with urllib.request.urlopen(stat_req, timeout=10) as s_resp:
                s_data = json.loads(s_resp.read().decode("utf-8"))
                if s_data.get("status") == "complete":
                    clips = s_data.get("clips", [])
                    if clips:
                        first = clips[0]
                        return (first.get("filename", ""), first.get("title", ""), int(first.get("score", 85)))
                    break
                elif s_data.get("status") == "error":
                    raise RuntimeError(f"VideoShorts pipeline error: {s_data.get('error')}")

        return ("", "No clips generated", 0)


NODE_CLASS_MAPPINGS = {
    "VideoShortsHighlightNode": VideoShortsHighlightNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoShortsHighlightNode": "VideoShorts Viral Clipper",
}
