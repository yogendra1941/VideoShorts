"""Audio ducking and background music mixing engine for VideoShorts.

Uses FFmpeg sidechain compression to automatically lower background music volume
during spoken speech and smoothly raise it during pauses.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional
from config import config

logger = logging.getLogger("VideoShorts.AudioDucker")


class AudioDucker:
    """Mixes background music with speech using dynamic sidechain compression."""

    def __init__(self, ducking_db: float = 14.0, attack_ms: float = 20.0, release_ms: float = 250.0):
        self.ducking_db = ducking_db
        self.attack_ms = attack_ms
        self.release_ms = release_ms

    def mix_background_music(
        self,
        video_path: Path,
        music_path: Path,
        output_path: Path,
        music_volume: float = 0.18,
    ) -> Path:
        """Applies dynamic sidechain compression to duck music beneath video dialogue.

        Args:
            video_path: Source short video with dialogue.
            music_path: Background music audio file (MP3, WAV, etc.).
            output_path: Target rendered video with ducked mix.
            music_volume: Base background music volume before ducking (0.0 to 1.0).

        Returns:
            Path to the output video.
        """
        video_path = Path(video_path)
        music_path = Path(music_path)
        output_path = Path(output_path)

        if not music_path.exists():
            logger.warning("Music track not found at %s. Skipping ducking.", music_path)
            return video_path

        # FFmpeg filter complex:
        # [0:a] is main speech. [1:a] is background music.
        # [1:a] volume adjusted -> sidechaincompress triggered by [0:a] -> amix with [0:a].
        filter_complex = (
            f"[1:a]volume={music_volume},aloop=loop=-1:size=2e+09[bg];"
            f"[bg][0:a]sidechaincompress="
            f"threshold=0.08:ratio=6:attack={self.attack_ms}:release={self.release_ms}[ducked_bg];"
            f"[0:a][ducked_bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(music_path),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]

        logger.info("Executing audio ducking: %s + %s -> %s", video_path.name, music_path.name, output_path.name)
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error("Audio ducking failed: %s", res.stderr)
            raise RuntimeError(f"FFmpeg audio ducking failed: {res.stderr[:200]}")

        return output_path
