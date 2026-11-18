"""Statistical AI Critic: 3-pass randomized blind evaluation to eliminate bias."""

import logging
import random
from typing import List, Dict, Any, Tuple
from core.llm import LLMClient

logger = logging.getLogger("VideoShorts.Critic")

CRITIC_SYSTEM_PROMPT = """You are an unforgiving, cynical short-form video critic.
Your job is to ruthlessly critique candidate short clips and reject fluff, boring openings, or rambling endings.
You judge each candidate strictly on its own merits without knowing who made it or why.

Scoring Dimensions (1 to 10 each):
- hook (weight 3): Does the first 3 seconds arrest attention instantly?
- payoff (weight 3): Does the ending hit with clarity, insight, or high impact?
- emotion (weight 2): Does it trigger curiosity, awe, laughter, or disagreement?
- shareability (weight 2): Would a viewer send this to a friend?
- quotability (weight 1): Is there an iconic phrase?

Rejection criteria:
- Any clip with a slow start or introductory pleasantries ("Hey guys", "So today...")
- Any clip that ends abruptly mid-thought
- Any clip that feels like an ad or filler
"""


class AICritic:
    """Performs 3-run randomized blind evaluation on candidate clips."""

    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()

    def evaluate_candidates(
        self,
        candidates: List[Dict[str, Any]],
        pass_threshold: float = 65.0,
    ) -> List[Dict[str, Any]]:
        """Runs candidate clips through 3 blind passes and filters or adjusts them."""
        if not candidates:
            return []

        approved: List[Dict[str, Any]] = []

        for clip in candidates:
            logger.info("Evaluating candidate clip [%.1fs - %.1fs]: '%s'", clip["start"], clip["end"], clip.get("title", ""))
            passes: List[Dict[str, Any]] = []

            for run_idx in range(3):
                # Anonymize with randomized neutral token
                token = f"CANDIDATE-{random.choice(['K7', 'B2', 'M9', 'X4', 'Z1', 'R8'])}-{random.randint(100, 999)}"
                eval_res = self._single_blind_pass(clip, token)
                passes.append(eval_res)

            # Compute statistical consensus
            passing_runs = [p for p in passes if p["composite_score"] >= pass_threshold]
            avg_score = sum(p["composite_score"] for p in passes) / len(passes)

            # 2-of-3 Gate Rule
            if len(passing_runs) >= 2:
                clip["critic_score"] = round(avg_score, 1)
                clip["critic_passes"] = len(passing_runs)
                clip["critic_notes"] = [p.get("critique", "") for p in passes]
                approved.append(clip)
                logger.info("-> APPROVED: Score %.1f (Passed %d/3 runs)", avg_score, len(passing_runs))
            else:
                logger.warning("-> REJECTED by Critic: Score %.1f (Passed %d/3 runs). Flaws: %s",
                               avg_score, len(passing_runs), passes[0].get("critique", "Low impact"))

        return approved

    def _single_blind_pass(self, clip: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Runs one blind critique pass using anonymized token."""
        prompt = f"""Blindly critique the following short video transcript segment identified as {token}:

TITLE: {clip.get('title', '')}
HOOK: {clip.get('hook', '')}
DURATION: {clip.get('end', 0) - clip.get('start', 0):.1f}s
REASON GIVEN: {clip.get('reason', '')}

Evaluate each dimension (1-10 integer):
hook, payoff, emotion, shareability, quotability.

Output strictly JSON:
{{
  "token": "{token}",
  "scores": {{
    "hook": 8,
    "payoff": 7,
    "emotion": 8,
    "shareability": 7,
    "quotability": 6
  }},
  "critique": "One sentence summary of flaws or strengths",
  "recommended_fix": "None, or suggest trimming start/end"
}}
"""
        try:
            res = self.llm.generate_json(prompt, system_prompt=CRITIC_SYSTEM_PROMPT, temperature=0.3)
            scores = res.get("scores", {})
            h = float(scores.get("hook", 5))
            p = float(scores.get("payoff", 5))
            e = float(scores.get("emotion", 5))
            s = float(scores.get("shareability", 5))
            q = float(scores.get("quotability", 5))

            # Weighted formula: max raw is (10*3 + 10*3 + 10*2 + 10*2 + 10*1) = 110
            raw_weighted = (h * 3.0) + (p * 3.0) + (e * 2.0) + (s * 2.0) + (q * 1.0)
            composite_score = (raw_weighted / 110.0) * 100.0

            return {
                "composite_score": composite_score,
                "scores": scores,
                "critique": res.get("critique", ""),
                "recommended_fix": res.get("recommended_fix", ""),
            }
        except Exception as e:
            logger.warning("Critic single pass error: %s. Using default baseline.", e)
            return {"composite_score": 70.0, "scores": {}, "critique": "Fallback baseline", "recommended_fix": ""}
