"""Social platform copy generation: per-platform titles and descriptions for each finished short.

Adapted from OpenShorts' social_platforms.py: builds short, platform-appropriate metadata
(TikTok/Reels/Shorts) from the clip content.
"""

import logging
from typing import Dict, Any, List, Optional

from core.llm import LLMClient

logger = logging.getLogger("VideoShorts.Social")

SOCIAL_SYSTEM_PROMPT = """You are a social media strategist. Given a short video clip's hook,
title, and a one-line description, produce ready-to-post metadata.

Return STRICT JSON with keys:
- "tiktok_caption": str (<=220 chars, with 2-4 relevant hashtags)
- "reels_caption": str (<=220 chars, with 2-4 relevant hashtags)
- "shorts_title": str (<=100 chars)
- "shorts_description": str (<=500 chars, includes a call to action)
"""


class SocialCopyGenerator:
    """Generates per-platform posting metadata for a finished short."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate(self, clip: Dict[str, Any]) -> Dict[str, Any]:
        """Return {platform: copy} for the clip."""
        hook = clip.get("hook") or clip.get("title") or ""
        title = clip.get("title") or hook
        reason = clip.get("reason") or clip.get("why_it_works") or ""
        prompt = (
            f"Hook: {hook}\n"
            f"Title: {title}\n"
            f"Why it works: {reason}\n\n"
            "Generate posting metadata."
        )
        try:
            data = self.llm.generate_json(prompt, system_prompt=SOCIAL_SYSTEM_PROMPT, temperature=0.4)
            clip["social"] = {
                "tiktok_caption": data.get("tiktok_caption", f"#shorts {title}"),
                "reels_caption": data.get("reels_caption", f"#reels {title}"),
                "shorts_title": data.get("shorts_title", title),
                "shorts_description": data.get("shorts_description", f"{reason} {title}"),
            }
        except Exception as e:
            logger.warning("Social copy generation failed (%s); using defaults", e)
            clip["social"] = {
                "tiktok_caption": f"#shorts {title}",
                "reels_caption": f"#reels {title}",
                "shorts_title": title,
                "shorts_description": f"{reason} {title}",
            }
        return clip

    def generate_all(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.generate(c) for c in clips]
