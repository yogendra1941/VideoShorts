"""Honesty gate: prevents decontextualized / misleading 'Frankenstein' deep-clip edits.

Adapted from ClipKaro's honesty.py. A deep clip stitches two distant moments; the honesty
gate verifies the joined edit preserves the speaker's true meaning and does not create a
false impression, an invented connection, or a distorted quote.
"""

import logging
from typing import Dict, Any, List, Optional

from core.llm import LLMClient

logger = logging.getLogger("VideoShorts.Honesty")

HONESTY_SYSTEM_PROMPT = """You are a factuality and fairness auditor for video edits.
You are shown a DEEP CLIP that stitches two non-adjacent moments from one recording into a
single short. Your job is to judge whether the edit is HONEST.

Return STRICT JSON: {"honest": bool, "reason": str, "issues": [str]}.

An edit is DISHONEST if any of:
- It makes the speaker appear to say something they did not actually say.
- It invents a causal or narrative connection the original did not make.
- It removes an important qualifier, context, or softening phrase that changes the meaning.
- It combines two quotes in a way that misrepresents the speaker's true position.
An edit is HONEST if it faithfully preserves the speaker's meaning and the connection between
the two moments is genuinely present in the original recording.
"""


class HonestyGate:
    """Filters deep clips that would be misleading or decontextualized."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def check(self, clip: Dict[str, Any]) -> Dict[str, Any]:
        """Return the clip with an 'honesty' verdict attached. A failed clip is marked for rejection."""
        part1 = clip.get("part1", {}).get("text") or clip.get("setup") or ""
        part2 = clip.get("part2", {}).get("text") or clip.get("payoff") or ""
        if not part1 or not part2:
            clip["honesty"] = {"honest": True, "reason": "No join to audit"}
            return clip

        prompt = (
            f"PART 1 (setup, from the start of the recording):\n{part1}\n\n"
            f"PART 2 (payoff, from later in the recording):\n{part2}\n\n"
            "Assess honesty of joining these two moments."
        )
        try:
            verdict = self.llm.generate_json(prompt, system_prompt=HONESTY_SYSTEM_PROMPT, temperature=0.2)
            clip["honesty"] = {
                "honest": bool(verdict.get("honest", True)),
                "reason": verdict.get("reason", ""),
                "issues": verdict.get("issues", []),
            }
        except Exception as e:
            logger.warning("Honesty gate error (%s); defaulting to honest", e)
            clip["honesty"] = {"honest": True, "reason": "gate error; defaulted"}
        return clip

    def filter_honest(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Drop deep clips that fail the honesty gate, returning the survivors."""
        survivors = []
        for clip in clips:
            clip = self.check(clip)
            if clip.get("honesty", {}).get("honest", True):
                survivors.append(clip)
            else:
                logger.info("Deep clip rejected by honesty gate: %s", clip.get("honesty", {}).get("reason"))
        return survivors
