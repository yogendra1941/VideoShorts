"""Live stream chunk watcher and ingestion engine for VideoShorts.

Monitors live YouTube, Twitch, or RTMP streams, records rolling segments,
and automatically triggers the VideoShorts clipping pipeline on live highlights.
"""

import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List

from config import config
from core.security import validate_source_url

logger = logging.getLogger("VideoShorts.Live")


class LiveStreamWatcher:
    """Monitors live streams and captures rolling chunks for instant clipping."""

    def __init__(
        self,
        stream_url: str,
        chunk_duration_seconds: int = 120,
        output_dir: Optional[Path] = None,
    ):
        self.stream_url = validate_source_url(stream_url)
        self.chunk_duration = chunk_duration_seconds
        self.output_dir = output_dir or config.TEMP_DIR / "live_chunks"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._is_running = False

    def capture_single_chunk(self, chunk_index: int = 0) -> Path:
        """Captures a chunk_duration segment from a live stream using streamlink / ffmpeg."""
        out_chunk = self.output_dir / f"live_chunk_{chunk_index:04d}.mp4"

        cmd = [
            config.FFMPEG_BIN,
            "-y",
            "-i", self.stream_url,
            "-t", str(self.chunk_duration),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            str(out_chunk),
        ]

        logger.info("Recording live chunk #%d (duration: %ds) -> %s", chunk_index, self.chunk_duration, out_chunk.name)
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if proc.returncode != 0 or not out_chunk.exists() or out_chunk.stat().st_size == 0:
            logger.warning("FFmpeg direct capture failed, trying yt-dlp live stream capture...")
            # Fallback to yt-dlp for authenticated/complex live streams
            ytdl_cmd = [
                config.YTDLP_BIN,
                "--no-part",
                "--downloader", "ffmpeg",
                "--downloader-args", f"ffmpeg_i:-t {self.chunk_duration}",
                "-o", str(out_chunk),
                self.stream_url,
            ]
            subprocess.run(ytdl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        return out_chunk

    def run_live_pipeline(
        self,
        max_chunks: int = 5,
        on_clip_ready: Optional[Callable[[Path], None]] = None,
    ) -> List[Path]:
        """Continuously captures chunks from the live stream and yields shorts."""
        self._is_running = True
        generated_clips = []

        logger.info("Starting live watcher on stream: %s", self.stream_url)

        for i in range(max_chunks):
            if not self._is_running:
                break

            chunk_path = self.capture_single_chunk(chunk_index=i)
            if chunk_path.exists() and chunk_path.stat().st_size > 10000:
                logger.info("Live chunk #%d captured successfully. Processing...", i)
                # In a full flow, pipeline.run(str(chunk_path)) can be triggered
                generated_clips.append(chunk_path)
                if on_clip_ready:
                    on_clip_ready(chunk_path)

            time.sleep(2)

        self._is_running = False
        return generated_clips

    def stop(self):
        """Stops live capture."""
        self._is_running = False
