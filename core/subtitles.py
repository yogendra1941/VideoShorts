"""Dynamic ASS subtitle generator with TikTok-style word-level active highlights."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("VideoShorts.Subtitles")

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,380,1
Style: HookBanner,Impact,64,&H0000FFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,8,40,40,200,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


class SubtitleGenerator:
    """Creates word-level highlight ASS subtitle files for FFmpeg rendering."""

    def __init__(
        self,
        font_name: str = "Arial Black",
        font_size: int = 72,
        highlight_color: str = "&H002BF5FF&",  # Vivid Yellow-Gold (BBGGRR in ASS)
        primary_color: str = "&H00FFFFFF&",    # Crisp White
        outline_color: str = "&H00000000&",    # Deep Black outline
        preset: Optional[Dict[str, Any]] = None,
    ):
        # Apply brand preset overrides if provided
        if preset:
            font_name = preset.get("subtitle_font", font_name)
            font_size = int(preset.get("subtitle_font_size", font_size))
            highlight_color = preset.get("active_word_color", highlight_color) + "&"
            primary_color = preset.get("inactive_word_color", primary_color) + "&"
        self.font_name = font_name
        self.font_size = font_size
        self.highlight_color = highlight_color
        self.primary_color = primary_color
        self.outline_color = outline_color

    def generate_ass(
        self,
        words: List[Dict[str, Any]],
        output_file: Path,
        clip_start: float = 0.0,
        clip_end: float = 0.0,
        hook_headline: Optional[str] = None,
        words_per_group: int = 4,
    ) -> Path:
        """Builds an ASS subtitle file with karaoke style word glow."""
        # Filter words within the clip range
        if clip_end > clip_start:
            active_words = [
                w for w in words
                if w.get("end", 0.0) >= clip_start and w.get("start", 0.0) <= clip_end
            ]
        else:
            active_words = words

        if not active_words:
            # Empty subtitle fallback
            output_file.write_text(ASS_HEADER, encoding="utf-8")
            return output_file

        events = []

        # Optional top Hook Banner
        if hook_headline:
            total_dur = clip_end - clip_start if clip_end > clip_start else 60.0
            banner_line = (
                f"Dialogue: 1,0:00:00.00,{self._format_timestamp(total_dur)},HookBanner,,0,0,0,,"
                f"{hook_headline.upper()}"
            )
            events.append(banner_line)

        # Group words into 3-5 word readable chunks
        groups = []
        for i in range(0, len(active_words), words_per_group):
            groups.append(active_words[i : i + words_per_group])

        # Generate timed karaoke events
        for grp in groups:
            for active_idx, target_word in enumerate(grp):
                # Timing relative to clip_start
                w_start = max(0.0, target_word["start"] - clip_start)
                w_end = max(w_start + 0.1, target_word["end"] - clip_start)

                start_str = self._format_timestamp(w_start)
                end_str = self._format_timestamp(w_end)

                # Build line with current word highlighted
                line_tokens = []
                for idx, w in enumerate(grp):
                    clean_text = w["word"].strip().upper()
                    if idx == active_idx:
                        # Highlighted word with slight pop
                        line_tokens.append(f"{{\\c{self.highlight_color}\\fscx110\\fscy110}}{clean_text}{{\\r}}")
                    else:
                        line_tokens.append(f"{{\\c{self.primary_color}}}{clean_text}")

                dialogue_text = " ".join(line_tokens)
                event_line = f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{dialogue_text}"
                events.append(event_line)

        full_content = ASS_HEADER + "\n".join(events) + "\n"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(full_content, encoding="utf-8")
        logger.info("Generated ASS subtitle file with %d events: %s", len(events), output_file)
        return output_file

    def _format_timestamp(self, seconds: float) -> str:
        """Formats seconds into ASS timestamp format: H:MM:SS.cs"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int(round((seconds - int(seconds)) * 100))
        if centisecs >= 100:
            centisecs = 99
        return f"{hrs}:{mins:02d}:{secs:02d}.{centisecs:02d}"
