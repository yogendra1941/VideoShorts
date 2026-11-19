"""Video rendering module: hardware-accelerated NVENC, layout filters, and ASS subtitle burning."""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from config import config

logger = logging.getLogger("VideoShorts.Renderer")


class VideoRenderer:
    """Renders final 9:16 video clips with layout filters, loudnorm audio, and subtitles."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def cut_clip(
        self,
        input_video: Path,
        output_slice: Path,
        start: float,
        end: float,
    ) -> bool:
        """Precision slice [start, end] out of input_video (OpenShorts cut_clip contract).
        Uses NVENC hardware acceleration where available, ensuring zero audio drift.
        """
        duration = max(0.5, end - start)
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-t", f"{duration:.3f}",
            "-i", str(input_video),
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-b:v", "8M",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_slice),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_slice.exists() and output_slice.stat().st_size > 0
        except Exception:
            # Fallback to libx264
            cmd[5] = "libx264"
            cmd[7] = "veryfast"
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                return output_slice.exists() and output_slice.stat().st_size > 0
            except Exception as e:
                logger.error("cut_clip slice failed: %s", e)
                return False

    def render_clip(
        self,
        video_path: Path,
        clip_info: Dict[str, Any],
        subtitle_path: Optional[Path] = None,
        layout: str = "GENERAL",
        crop_box: Optional[Dict[str, Any]] = None,
        output_filename: Optional[str] = None,
    ) -> Path:
        """Renders a single short clip with layout cropping, audio normalization, and burned captions."""
        start = clip_info["start"]
        end = clip_info["end"]
        duration = max(1.0, end - start)

        safe_title = "".join(c for c in clip_info.get("title", "clip") if c.isalnum() or c in (" ", "-", "_")).strip()
        safe_title = safe_title.replace(" ", "_")[:30]
        out_name = output_filename or f"{safe_title}_{int(start)}s.mp4"
        out_path = self.output_dir / out_name

        # Build video filter graph based on layout and crop_box
        v_filter = self._build_layout_filter(layout, subtitle_path, crop_box)
        a_filter = "loudnorm=I=-16:TP=-1.5:LRA=11" if config.LOUDNORM_ENABLED else "anull"

        logger.info("Rendering [%.1fs - %.1fs] using layout '%s' -> %s", start, end, layout, out_path.name)

        # Attempt NVENC hardware accelerated render
        success = self._run_ffmpeg_render(
            video_path=video_path,
            start=start,
            duration=duration,
            v_filter=v_filter,
            a_filter=a_filter,
            out_path=out_path,
            use_nvenc=True,
        )

        # CPU fallback if NVENC fails
        if not success:
            logger.warning("NVENC render failed. Falling back to CPU libx264 encoding...")
            self._run_ffmpeg_render(
                video_path=video_path,
                start=start,
                duration=duration,
                v_filter=v_filter,
                a_filter=a_filter,
                out_path=out_path,
                use_nvenc=False,
            )

        return out_path

    def _build_layout_filter(
        self,
        layout: str,
        subtitle_path: Optional[Path],
        crop_box: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Constructs FFmpeg filter complex string for 9:16 layout formatting."""
        sub_str = ""
        if subtitle_path and subtitle_path.exists():
            clean_sub = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
            sub_str = f",ass='{clean_sub}'"

        if layout == "SPLIT":
            # Stacked two-speaker podcast layout: Top half (0 to 50% width), Bottom half (50% to 100% width)
            filt = (
                "[0:v]crop=iw/2:ih:0:0,scale=1080:960[top];"
                "[0:v]crop=iw/2:ih:iw/2:0,scale=1080:960[bottom];"
                f"[top][bottom]vstack=inputs=2{sub_str}"
            )
            return filt
        elif layout == "TRACK":
            # Face-tracked 9:16 crop box with EMA smoothing
            if crop_box:
                x = crop_box.get("x", 0)
                y = crop_box.get("y", 0)
                w = crop_box.get("w", 608)
                h = crop_box.get("h", 1080)
                filt = f"crop={w}:{h}:{x}:{y},scale=1080:1920:force_original_aspect_ratio=decrease{sub_str}"
            else:
                filt = f"crop=ih*(9/16):ih:(iw-ih*(9/16))/2:0,scale=1080:1920:force_original_aspect_ratio=decrease{sub_str}"
            return filt
        else:
            # GENERAL: 16:9 in center with blurred background filling 9:16
            filt = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
                "[0:v]scale=1080:-1[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2{sub_str}"
            )
            return filt

    def _run_ffmpeg_render(
        self,
        video_path: Path,
        start: float,
        duration: float,
        v_filter: str,
        a_filter: str,
        out_path: Path,
        use_nvenc: bool = True,
    ) -> bool:
        """Executes FFmpeg rendering command."""
        vcodec = "h264_nvenc" if use_nvenc else "libx264"
        preset = "p4" if use_nvenc else "veryfast"

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", f"{start:.2f}",
            "-t", f"{duration:.2f}",
            "-i", str(video_path),
            "-filter_complex", v_filter,
            "-af", a_filter,
            "-c:v", vcodec,
            "-preset", preset,
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            str(out_path),
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return out_path.exists() and out_path.stat().st_size > 0
        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg render failed with exit code %s:\n%s", e.returncode, e.stderr[-500:])
            return False
