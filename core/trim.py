"""Speech hygiene module: removes filler words and excessive dead silence pauses."""

import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("VideoShorts.Trim")

# Standard verbal tics and filler words
DEFAULT_FILLER_WORDS = {
    "um", "uh", "umm", "uhh", "er", "ah", "ahh", "hmm", "hm"
}

class SpeechTrimmer:
    """Cleans word-level timestamps by trimming silence gaps and verbal pauses."""

    def __init__(
        self,
        max_silence_gap: float = 1.2,
        min_word_duration: float = 0.05,
        filler_words: set = None,
    ):
        self.max_silence_gap = max_silence_gap
        self.min_word_duration = min_word_duration
        self.filler_words = filler_words or DEFAULT_FILLER_WORDS

    def clean_word_stream(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters out hesitation filler words from the word stream."""
        cleaned: List[Dict[str, Any]] = []
        removed_count = 0

        for w in words:
            word_clean = w["word"].strip().lower().strip(".,!?:;\"'()[]{}")
            if word_clean in self.filler_words:
                removed_count += 1
                continue
            cleaned.append(w)

        logger.info("Cleaned %d filler words from word stream", removed_count)
        return cleaned

    def detect_speech_segments(
        self,
        words: List[Dict[str, Any]],
        start_bound: float,
        end_bound: float,
    ) -> List[Tuple[float, float]]:
        """Returns non-silent time intervals within [start_bound, end_bound],
        collapsing long pauses exceeding max_silence_gap.
        """
        if not words:
            return [(start_bound, end_bound)]

        # Filter words within the clip bounds
        clip_words = [
            w for w in words
            if w.get("end", 0.0) >= start_bound and w.get("start", 0.0) <= end_bound
        ]

        if not clip_words:
            return [(start_bound, end_bound)]

        segments: List[Tuple[float, float]] = []
        seg_start = max(start_bound, clip_words[0]["start"] - 0.1)
        prev_end = clip_words[0]["end"]

        for w in clip_words[1:]:
            gap = w["start"] - prev_end
            if gap > self.max_silence_gap:
                # Pause is too long: finalize current segment and begin new segment
                seg_end = min(end_bound, prev_end + 0.15)
                segments.append((seg_start, seg_end))
                seg_start = max(start_bound, w["start"] - 0.15)
            prev_end = w["end"]

        final_end = min(end_bound, prev_end + 0.2)
        segments.append((seg_start, final_end))

        return segments
