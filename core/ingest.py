"""Ingestion module: downloads videos (yt-dlp), extracts Whisper-ready audio, and probes scene cuts."""

import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import yt_dlp

from config import config
from core.security import validate_source_url

logger = logging.getLogger("VideoShorts.Ingest")


class VideoIngestor:
    """Handles downloading YouTube media, probing streams, and audio extraction."""

    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = temp_dir or config.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def process_source(self, source: str) -> Dict[str, Any]:
        """Accepts either a YouTube URL or a local file path.
        Returns metadata including video_path, audio_path, duration, and scene boundaries.
        """
        source = source.strip()
        if source.startswith("http://") or source.startswith("https://"):
            # SSRF guard: reject private/link-local/loopback URL targets.
            source = validate_source_url(source)
            logger.info("Downloading YouTube stream: %s", source)
            metadata = self._download_youtube(source)
            video_path = Path(metadata["video_path"])
        else:
            video_path = Path(source)
            if not video_path.exists():
                raise FileNotFoundError(f"Local video file not found: {source}")
            logger.info("Processing local video: %s", video_path)
            probe = self.probe_video(video_path)
            metadata = {
                "title": video_path.stem,
                "video_path": str(video_path),
                "duration": probe.get("duration", 0.0),
                "width": probe.get("width", 1920),
                "height": probe.get("height", 1080),
                "fps": probe.get("fps", 30.0),
            }

        # Extract 16kHz mono WAV for Whisper
        audio_path = self.extract_whisper_audio(video_path)
        metadata["audio_path"] = str(audio_path)

        # Detect visual scene cuts
        scene_cuts = self.detect_scene_cuts(video_path)
        metadata["scene_cuts"] = scene_cuts

        logger.info(
            "Ingestion complete: title='%s', duration=%.2fs, scene_cuts=%d",
            metadata["title"],
            metadata["duration"],
            len(scene_cuts),
        )
        return metadata

    def _download_youtube(self, url: str) -> Dict[str, Any]:
        """Downloads high quality MP4 stream via yt-dlp."""
        out_tmpl = str(self.temp_dir / "%(id)s.%(ext)s")
        ydl_opts = {
            "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": out_tmpl,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get("id")
            filename = ydl.prepare_filename(info)
            # When merged to mp4, filename extension changes
            mp4_path = Path(filename).with_suffix(".mp4")
            if not mp4_path.exists() and Path(filename).exists():
                mp4_path = Path(filename)

            return {
                "id": video_id,
                "title": info.get("title", video_id),
                "video_path": str(mp4_path),
                "duration": float(info.get("duration", 0.0)),
                "width": info.get("width", 1920),
                "height": info.get("height", 1080),
                "fps": info.get("fps", 30.0),
            }

    def probe_video(self, video_path: Path) -> Dict[str, Any]:
        """Uses ffprobe to extract stream dimensions, duration, and framerate."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration",
            "-show_entries", "format=duration",
            "-of", "json",
            str(video_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        duration = 0.0
        width = 1920
        height = 1080
        fps = 30.0

        if "format" in data and "duration" in data["format"]:
            duration = float(data["format"]["duration"])

        streams = data.get("streams", [])
        if streams:
            st = streams[0]
            width = int(st.get("width", 1920))
            height = int(st.get("height", 1080))
            if "duration" in st and duration == 0.0:
                duration = float(st["duration"])
            if "r_frame_rate" in st:
                parts = st["r_frame_rate"].split("/")
                if len(parts) == 2 and float(parts[1]) > 0:
                    fps = float(parts[0]) / float(parts[1])

        return {"duration": duration, "width": width, "height": height, "fps": fps}

    def extract_whisper_audio(self, video_path: Path) -> Path:
        """Extracts 16kHz mono 16-bit PCM WAV audio for optimal Whisper processing."""
        output_wav = self.temp_dir / f"{video_path.stem}_whisper.wav"
        if output_wav.exists() and output_wav.stat().st_size > 0:
            return output_wav

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_wav),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_wav

    def detect_scene_cuts(self, video_path: Path, threshold: float = 0.3) -> List[float]:
        """Detects visual scene change timestamps using FFmpeg's scene detector filter."""
        cuts: List[float] = [0.0]
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-filter_complex", f"select='gt(scene,{threshold})',metadata=print:file=-",
            "-f", "null",
            "-",
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            for line in res.stderr.splitlines():
                if "pts_time:" in line:
                    parts = line.split("pts_time:")
                    if len(parts) > 1:
                        val = parts[1].split()[0]
                        try:
                            t = float(val)
                            if t not in cuts:
                                cuts.append(t)
                        except ValueError:
                            pass
        except Exception as e:
            logger.warning("Scene detection encountered warning: %s", e)

        return sorted(cuts)
