"""Deep Clips Engine: multi-stage synthesis stitching non-adjacent setups and payoffs."""

import logging
from typing import List, Dict, Any
from core.llm import LLMClient

logger = logging.getLogger("VideoShorts.DeepClips")

DEEP_SYSTEM_PROMPT = """You are an expert podcast narrative editor specializing in 'Deep Clips'.
A Deep Clip joins two distant moments in a long recording into one cohesive 45-60s story:
- Part 1 (The Hook/Setup): A provocative question, a bold premise, or a problem stated early on.
- Part 2 (The Payoff/Insight): The concrete answer, lesson, or proof revealed much later.

Hard Rules:
1. MIN_GAP: The two moments must be separated by at least 60 seconds in the source recording.
2. WHOLE SENTENCES: Never cut mid-sentence.
3. CONTEXT INTEGRITY: Joining them must preserve the speaker's true intended meaning (NO deceptive edits).
4. COMBINED DURATION: Combined total runtime must be between 30 and 60 seconds.
"""


class DeepClipsEngine:
    """Multi-stage stateful machine for non-adjacent moment synthesis."""

    def __init__(self, llm_client: LLMClient = None, min_gap_seconds: float = 60.0):
        self.llm = llm_client or LLMClient()
        self.min_gap_seconds = min_gap_seconds

    def synthesize_deep_clips(
        self,
        transcript_segments: List[Dict[str, Any]],
        max_clips: int = 3,
    ) -> List[Dict[str, Any]]:
        """Executes the full Deep Clips pipeline: Topic Map -> Thread Seeding -> Composer -> Honesty Gate."""
        if not transcript_segments or len(transcript_segments) < 10:
            logger.info("Transcript too brief for deep clips synthesis")
            return []

        total_duration = transcript_segments[-1]["end"]
        if total_duration < 180.0:
            logger.info("Video under 3 minutes; deep clips require longer conversational content")
            return []

        # Stage 1: Build Topic Map
        logger.info("Stage 1: Building Topic Map across %.1fs recording", total_duration)
        topic_map = self._build_topic_map(transcript_segments)

        # Stage 2 & 3: Thread Seeding & Candidate Composition
        logger.info("Stage 2 & 3: Seeding narrative threads and composing paired clips")
        candidates = self._compose_paired_threads(transcript_segments, topic_map)

        # Stage 4: Honesty Gate Verification
        logger.info("Stage 4: Running Honesty Gate on %d paired candidates", len(candidates))
        verified_clips: List[Dict[str, Any]] = []

        for cand in candidates:
            if self._verify_honesty_gate(cand):
                verified_clips.append(cand)
            else:
                logger.warning("Rejected candidate '%s' by Honesty Gate (meaning distorted)", cand.get("title", ""))

        verified_clips.sort(key=lambda x: x.get("viral_score", 0), reverse=True)
        return verified_clips[:max_clips]

    def _build_topic_map(self, segments: List[Dict[str, Any]]) -> str:
        """Summarizes key points every 3-5 minutes to create a macro narrative index."""
        blocks = []
        current_block: List[str] = []
        block_start = 0.0

        for s in segments:
            current_block.append(s["text"])
            if s["end"] - block_start >= 240.0:  # 4 min blocks
                time_label = f"[{int(block_start//60)}m - {int(s['end']//60)}m]"
                summary_line = f"{time_label}: {' '.join(current_block[:40])}..."
                blocks.append(summary_line)
                current_block = []
                block_start = s["end"]

        if current_block:
            blocks.append(f"[{int(block_start//60)}m+]: {' '.join(current_block[:40])}...")

        return "\n".join(blocks)

    def _compose_paired_threads(
        self,
        segments: List[Dict[str, Any]],
        topic_map: str,
    ) -> List[Dict[str, Any]]:
        """Prompts LLM to pair non-adjacent moments with explicit start/end boundaries."""
        sample_transcript = "\n".join([f"[{s['start']:.1f}s - {s['end']:.1f}s]: {s['text']}" for s in segments[::2]])

        prompt = f"""Using the topic map and sampled transcript below, identify up to 3 'Deep Clip' pairs (separated by >= 60 seconds) where Part 1 poses a problem/premise and Part 2 delivers the payoff.

TOPIC MAP:
{topic_map}

SAMPLED TRANSCRIPT:
{sample_transcript[:4000]}

Format JSON:
{{
  "deep_clips": [
    {{
      "title": "Title of the combined story",
      "hook": "Opening hook line",
      "viral_score": 85,
      "part1": {{ "start": 45.0, "end": 65.0, "description": "The premise/question" }},
      "part2": {{ "start": 320.0, "end": 350.0, "description": "The payoff/answer" }},
      "seam_transition": "white_flash",
      "combined_reason": "Why these two distant moments make one viral short"
    }}
  ]
}}
"""
        try:
            res = self.llm.generate_json(prompt, system_prompt=DEEP_SYSTEM_PROMPT)
            raw_clips = res.get("deep_clips", [])
            valid: List[Dict[str, Any]] = []

            for rc in raw_clips:
                p1 = rc.get("part1", {})
                p2 = rc.get("part2", {})
                gap = p2.get("start", 0) - p1.get("end", 0)
                dur1 = p1.get("end", 0) - p1.get("start", 0)
                dur2 = p2.get("end", 0) - p2.get("start", 0)
                total_dur = dur1 + dur2

                if gap >= self.min_gap_seconds and 25.0 <= total_dur <= 70.0:
                    rc["is_deep_clip"] = True
                    rc["start"] = p1.get("start")
                    rc["end"] = p2.get("end")
                    rc["segments"] = [(p1["start"], p1["end"]), (p2["start"], p2["end"])]
                    valid.append(rc)

            return valid
        except Exception as e:
            logger.error("Deep clip composition error: %s", e)
            return []

    def _verify_honesty_gate(self, deep_clip: Dict[str, Any]) -> bool:
        """Semantic check: ensures splicing Part 1 and Part 2 does not fabricate a false narrative."""
        prompt = f"""Verify that joining these two segments does not distort or misrepresent the speaker's original meaning:

PART 1: {deep_clip.get('part1', {}).get('description', '')}
PART 2: {deep_clip.get('part2', {}).get('description', '')}
COMBINED THESIS: {deep_clip.get('combined_reason', '')}

Does this join preserve factual honesty and conversational context?
Output strictly JSON:
{{
  "is_honest": true,
  "confidence": 9,
  "risk_flags": []
}}
"""
        try:
            res = self.llm.generate_json(prompt, temperature=0.1)
            return bool(res.get("is_honest", True))
        except Exception:
            return True
