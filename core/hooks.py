"""Hook headline generation: writes an attention-grabbing opening line (hook) for each candidate clip.

Adapted from OpenShorts' hooks module. This is the LLM-based text generation portion
(the heavy PIL/emoji rasterization from OpenShorts is intentionally not ported here;
the rendered hook is burned onto short video via the ASS subtitle headline).
"""

import logging
from typing import Dict, Any, Optional

from core.llm import LLMClient

logger = logging.getLogger("VideoShorts.Hooks")

HOOK_SYSTEM_PROMPT = """You are an elite short-form copywriter for viral TikToks, YouTube Shorts, and Reels.
Your only job is to write a short, punchy HOOK headline for a video clip — the 1-to-6-word
line that plays at the top of the short and stops the scroll.

Rules:
- 1 to 6 words, no more.
- Opening curiosity gap, contrarian claim, or punchy question.
- Do NOT use clickbait punctuation spam (NO "!!!!" or "???").
- Match the speaker's real point — never invent a claim the clip doesn't make.
- Return a single string. No quotes, no explanation.
"""


class HookGenerator:
    """Generates a hook headline for each candidate clip via the configured LLM."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_hook(self, clip_text: str, clip_title: str = "") -> str:
        """Return the hook headline for the clip transcript text."""
        if not clip_text or not clip_text.strip():
            return clip_title or "Watch this"
        prompt = (
            f"Clip title (context only): {clip_title}\n"
            f"Clip transcript:\n{clip_text.strip()}\n\n"
            "Write the hook headline:"
        )
        try:
            raw = self.llm.generate(prompt, system_prompt=HOOK_SYSTEM_PROMPT, json_output=False, temperature=0.5)
            hook = raw.strip().strip('"').strip("'")
            # Truncate to reasonable length
            if len(hook) > 60:
                hook = hook[:60]
            return hook or clip_title
        except Exception as e:
            logger.warning("Hook generation failed (%s); falling back to clip title", e)
            return clip_title or "Watch this"

    def enrich_clip(self, clip: Dict[str, Any], clip_text: str) -> Dict[str, Any]:
        """Attach a hook to the clip dict in place and return it."""
        clip.setdefault("hook", "")
        clip["hook"] = self.generate_hook(clip_text, clip.get("title", ""))
        return clip
