"""Brand kit: configurable style presets for subtitles, hook banners, and overlays.

Adapted from ClipKaro's brand.py / brandkit.py concepts. Provides named presets that the
subtitle generator and renderer use to keep a consistent look, and stores brand metadata
(title/logo) for the web studio.
"""

from typing import Dict, Any

# Named style presets. Keys are consumed by core/subtitles.py (ASS styling) and
# core/renderer.py (overlay) where applicable.
BRAND_PRESETS: Dict[str, Dict[str, Any]] = {
    "default": {
        "name": "Default",
        "subtitle_font": "Montserrat-ExtraBold",
        "subtitle_font_size": 62,
        "subtitle_outline": 4,
        "active_word_color": "&H00FFD700",      # gold (ASS BGR)
        "inactive_word_color": "&H00FFFFFF",    # white
        "karaoke": True,
        "hook_banner": True,
        "hook_font_size": 72,
    },
    "minimal": {
        "name": "Minimalist",
        "subtitle_font": "Montserrat-SemiBold",
        "subtitle_font_size": 54,
        "subtitle_outline": 2,
        "active_word_color": "&H00FF8000",      # orange
        "inactive_word_color": "&H00E6E6E6",
        "karaoke": True,
        "hook_banner": True,
        "hook_font_size": 64,
    },
    "bold": {
        "name": "Bold",
        "subtitle_font": "Anton-Regular",
        "subtitle_font_size": 72,
        "subtitle_outline": 6,
        "active_word_color": "&H0000FFFF",      # yellow (BGR: G+B)
        "inactive_word_color": "&H00FFFFFF",
        "karaoke": True,
        "hook_banner": True,
        "hook_font_size": 84,
    },
    "hormozi_gold": {
        "name": "Hormozi Gold",
        "subtitle_font": "Montserrat-ExtraBold",
        "subtitle_font_size": 78,
        "subtitle_outline": 8,
        "active_word_color": "&H0000FFFF",      # vivid yellow (BGR: G+B)
        "inactive_word_color": "&H00FFFFFF",
        "karaoke": True,
        "hook_banner": True,
        "hook_font_size": 90,
    },
    "cyber_neon": {
        "name": "Cyber Neon",
        "subtitle_font": "JetBrainsMono-Bold",
        "subtitle_font_size": 60,
        "subtitle_outline": 4,
        "active_word_color": "&H00D4B606",      # cyan (BGR: B+G -> cyan)
        "inactive_word_color": "&H00FFFFFF",
        "karaoke": True,
        "hook_banner": True,
        "hook_font_size": 76,
    },
    "podcast_split": {
        "name": "Podcast Split",
        "subtitle_font": "Montserrat-SemiBold",
        "subtitle_font_size": 56,
        "subtitle_outline": 3,
        "active_word_color": "&H00FFD700",      # gold
        "inactive_word_color": "&H00FFFFFF",
        "karaoke": True,
        "hook_banner": False,
        "hook_font_size": 60,
        "seam_anchored": True,                  # captions live on the split seam
    },
}


class BrandKit:
    """Resolves brand presets and holds product identity metadata."""

    def __init__(self, name: str = "default"):
        self.name = name
        self.preset = BRAND_PRESETS.get(name, BRAND_PRESETS["default"])

    def get_preset(self) -> Dict[str, Any]:
        return dict(self.preset)

    def set_preset(self, name: str) -> None:
        if name in BRAND_PRESETS:
            self.name = name
            self.preset = BRAND_PRESETS[name]

    @staticmethod
    def available_presets() -> list:
        return list(BRAND_PRESETS.keys())
