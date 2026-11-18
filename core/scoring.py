"""Virality framework: scoring moments, long-video chunking, and overlap deduplication."""

import logging
from typing import List, Dict, Any
from core.llm import LLMClient

logger = logging.getLogger("VideoShorts.Scoring")

VIRALITY_SYSTEM_PROMPT = """You are an elite short-form content producer who creates viral TikToks, YouTube Shorts, and Reels.
Your objective is to find the most captivating, high-retention moments from a transcript.

Evaluation criteria:
1. HOOK (Weight 3x): Starts with an immediate curiosity gap, contrarian opinion, or punchy question.
2. NARRATIVE PAYOFF (Weight 3x): Delivers a complete, satisfying thought or insight.
3. EMOTION & INTENSITY (Weight 2x): High energy, surprise, vulnerability, or debate.
4. QUOTABILITY (Weight 1x): Memorable punchlines that people share or comment on.

Rules:
- Clip length MUST be between 20 and 60 seconds.
- Every clip must be completely standalone (no dangling "as I said earlier" without context).
- Return valid JSON matching the requested schema.
"""


class ViralityScorer:
    """Detects and scores viral candidate moments from transcripts."""

    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()

    def find_highlights(
        self,
        transcript_segments: List[Dict[str, Any]],
        min_duration: float = 20.0,
        max_duration: float = 60.0,
        target_clips: int = 5,
        fallback_total_duration: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Analyzes transcript segments and returns ranked viral candidates."""
        total_duration = transcript_segments[-1].get("end", 0.0) if transcript_segments else fallback_total_duration
        logger.info("Analyzing transcript (duration: %.1fs) for viral highlights", total_duration)

        # Chunk if longer than 30 minutes (1800s)
        if total_duration > 1800.0:
            candidates = self._process_chunked(transcript_segments, min_duration, max_duration)
        elif transcript_segments and len(transcript_segments) >= 2:
            candidates = self._score_segment_block(transcript_segments, min_duration, max_duration)
        else:
            candidates = []

        # Graceful fallback for short demo videos or clips with sparse dialogue
        if not candidates and total_duration > 0:
            clip_len = min(total_duration, max_duration)
            logger.info("Creating baseline highlight candidate for %.1fs clip", clip_len)
            candidates = [{
                "start": 0.0,
                "end": clip_len,
                "title": "Highlight Moment",
                "hook": "Check out this highlight",
                "viral_score": 85,
                "reason": "Complete continuous segment",
            }]

        # Apply Overlap Deduplication (NMS)
        deduped = self.deduplicate_overlaps(candidates, max_overlap_ratio=0.30)
        deduped.sort(key=lambda x: x.get("viral_score", 0), reverse=True)

        return deduped[:target_clips]

    def _score_segment_block(
        self,
        segments: List[Dict[str, Any]],
        min_duration: float,
        max_duration: float,
    ) -> List[Dict[str, Any]]:
        """Sends a block of transcript segments to the LLM for virality evaluation."""
        formatted_lines = []
        for s in segments:
            formatted_lines.append(f"[{s['start']:.1f}s - {s['end']:.1f}s]: {s['text']}")
        transcript_body = "\n".join(formatted_lines)

        user_prompt = f"""Analyze the timestamped transcript below and extract up to 8 candidate viral clips ({min_duration}s to {max_duration}s long).

TRANSCRIPT:
{transcript_body}

Output JSON format strictly:
{{
  "clips": [
    {{
      "start": 12.5,
      "end": 48.0,
      "hook": "Opening sentence that hooks viewers",
      "title": "Short Punchy Title (Max 6 words)",
      "viral_score": 88,
      "reason": "Why this moment hooks and retains viewers",
      "dimension_scores": {{
        "hook": 9,
        "payoff": 8,
        "emotion": 9,
        "quotability": 8
      }}
    }}
  ]
}}
"""
        try:
            res = self.llm.generate_json(user_prompt, system_prompt=VIRALITY_SYSTEM_PROMPT)
            clips = res.get("clips", [])
            valid_clips = []
            for c in clips:
                dur = c.get("end", 0.0) - c.get("start", 0.0)
                if min_duration <= dur <= max_duration + 5.0:
                    valid_clips.append(c)
            return valid_clips
        except Exception as e:
            logger.error("Error during LLM virality extraction: %s", e)
            return []

    def _process_chunked(
        self,
        segments: List[Dict[str, Any]],
        min_duration: float,
        max_duration: float,
        chunk_seconds: float = 1200.0,
        overlap_seconds: float = 180.0,
    ) -> List[Dict[str, Any]]:
        """Slides a window across long transcripts with overlap."""
        all_candidates: List[Dict[str, Any]] = []
        start_time = 0.0
        max_time = segments[-1]["end"]

        while start_time < max_time:
            end_time = start_time + chunk_seconds
            chunk_segs = [s for s in segments if s["start"] >= start_time and s["end"] <= end_time]
            if chunk_segs:
                found = self._score_segment_block(chunk_segs, min_duration, max_duration)
                all_candidates.extend(found)
            start_time += (chunk_seconds - overlap_seconds)

        return all_candidates

    def deduplicate_overlaps(
        self,
        candidates: List[Dict[str, Any]],
        max_overlap_ratio: float = 0.30,
    ) -> List[Dict[str, Any]]:
        """Non-Maximum Suppression (NMS): removes lower-scoring clips that overlap excessively."""
        if not candidates:
            return []

        sorted_clips = sorted(candidates, key=lambda x: x.get("viral_score", 0), reverse=True)
        kept: List[Dict[str, Any]] = []

        for clip in sorted_clips:
            c_start = clip["start"]
            c_end = clip["end"]
            c_dur = max(0.1, c_end - c_start)

            is_duplicate = False
            for existing in kept:
                e_start = existing["start"]
                e_end = existing["end"]
                e_dur = max(0.1, e_end - e_start)

                # Compute overlap intersection
                inter_start = max(c_start, e_start)
                inter_end = min(c_end, e_end)
                inter_dur = max(0.0, inter_end - inter_start)

                if inter_dur > 0:
                    ratio = inter_dur / min(c_dur, e_dur)
                    if ratio >= max_overlap_ratio:
                        is_duplicate = True
                        break

            if not is_duplicate:
                kept.append(clip)

        logger.info("Overlap deduplication: pruned %d redundant candidates, %d kept", len(candidates) - len(kept), len(kept))
        return kept
