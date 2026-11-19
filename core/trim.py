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

    def snap_clip_to_words(
        self,
        start: float,
        end: float,
        words: List[Dict[str, Any]],
        video_duration: float = 3600.0,
        min_duration: float = 15.0,
        max_duration: float = 60.0,
        search_window: float = 1.5,
        max_lead: float = 0.35,
        max_tail: float = 0.45,
    ) -> Tuple[float, float]:
        """Snaps raw AI-generated clip boundaries onto ground-truth word boundaries.
        Adds natural silence padding so speech never starts or cuts off mid-word (OpenShorts style).
        """
        original = (round(float(start), 3), round(float(end), 3))
        if not words:
            return original

        starts = [float(w.get("start", w.get("s", 0))) for w in words]
        ends = [float(w.get("end", w.get("e", 0))) for w in words]

        # Snap start to nearest word start, leading into preceding silence
        new_start = float(start)
        candidates = [s for s in starts if abs(s - new_start) <= search_window]
        if candidates:
            word_start = min(candidates, key=lambda s: abs(s - new_start))
            prev_ends = [e for e in ends if e <= word_start]
            if prev_ends:
                gap = max(0.0, word_start - max(prev_ends))
                lead = min(max_lead, gap / 2)
            else:
                lead = max_lead
            new_start = max(0.0, word_start - lead)

        # Snap end to nearest word end, trailing into following silence
        new_end = float(end)
        candidates = [e for e in ends if abs(e - new_end) <= search_window]
        if candidates:
            word_end = min(candidates, key=lambda e: abs(e - new_end))
            next_starts = [s for s in starts if s >= word_end]
            if next_starts:
                gap = max(0.0, min(next_starts) - word_end)
                tail = min(max_tail, gap / 2)
            else:
                tail = max_tail
            new_end = min(video_duration, word_end + tail)

        if new_end - new_start < min_duration or new_end - new_start > max_duration + 5.0:
            return original

        return round(new_start, 3), round(new_end, 3)
