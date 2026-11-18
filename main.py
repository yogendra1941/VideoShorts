"""Master pipeline coordinator for VideoShorts."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import config
from core.ingest import VideoIngestor
from core.transcribe import WhisperTranscriber
from core.trim import SpeechTrimmer
from core.scoring import ViralityScorer
from core.deep import DeepClipsEngine
from core.honesty import HonestyGate
from core.critic import AICritic
from core.hooks import HookGenerator
from core.social import SocialCopyGenerator
from core.brand import BrandKit
from core.layout_picker import LayoutPicker
from core.reframer import SmartReframer
from core.subtitles import SubtitleGenerator
from core.renderer import VideoRenderer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("VideoShorts.Pipeline")


class VideoShortsPipeline:
    """End-to-end AI video clipping and vertical reframing pipeline."""

    def __init__(self, brand_preset: Optional[str] = None):
        self.ingestor = VideoIngestor()
        self.transcriber = WhisperTranscriber()
        self.trimmer = SpeechTrimmer()
        self.scorer = ViralityScorer()
        self.deep_engine = DeepClipsEngine()
        self.honesty_gate = HonestyGate()
        self.critic = AICritic()
        self.hook_gen = HookGenerator()
        self.social_gen = SocialCopyGenerator()
        self.brand_kit = BrandKit(brand_preset or "default")
        self.layout_picker = LayoutPicker()
        self.reframer = SmartReframer()
        self.sub_gen = SubtitleGenerator(preset=self.brand_kit.get_preset())
        self.renderer = VideoRenderer()

    def run(
        self,
        source: str,
        target_clips: int = 3,
        enable_deep_clips: bool = True,
        enable_critic: bool = True,
        enable_honesty: bool = True,
        force_layout: Optional[str] = None,
    ) -> List[Path]:
        """Executes the full clipping workflow and exports finished 9:16 shorts."""
        logger.info("=== Starting VideoShorts Pipeline ===")
        logger.info("Source: %s", source)

        # Step 1: Ingestion & Audio Extraction
        logger.info("--- Step 1: Ingestion & Probing ---")
        meta = self.ingestor.process_source(source)
        video_path = Path(meta["video_path"])
        audio_path = Path(meta["audio_path"])

        # Step 2: Speech-to-Text Transcription
        logger.info("--- Step 2: Whisper Transcription ---")
        asr_res = self.transcriber.transcribe(audio_path)
        words = asr_res["words"]
        segments = asr_res["segments"]

        # Step 3: Speech Hygiene & Trimming
        logger.info("--- Step 3: Speech Trimming ---")
        cleaned_words = self.trimmer.clean_word_stream(words)

        # Step 4: Virality Scoring
        logger.info("--- Step 4: AI Virality Scoring ---")
        candidates = self.scorer.find_highlights(
            transcript_segments=segments,
            min_duration=config.MIN_CLIP_DURATION,
            max_duration=config.MAX_CLIP_DURATION,
            target_clips=target_clips * 2,
            fallback_total_duration=meta.get("duration", 0.0),
        )

        # Step 4B: Optional Deep Clips Synthesis
        if enable_deep_clips and meta["duration"] >= 180.0:
            logger.info("--- Step 4B: Deep Clips Narrative Synthesis ---")
            deep_clips = self.deep_engine.synthesize_deep_clips(segments, max_clips=2)
            if enable_honesty and deep_clips:
                logger.info("--- Step 4C: Honesty Gate Filtering ---")
                deep_clips = self.honesty_gate.filter_honest(deep_clips)
            candidates.extend(deep_clips)

        # Step 5: 3-Pass Statistical AI Critic
        if enable_critic and candidates:
            logger.info("--- Step 5: 3-Pass Statistical AI Critic ---")
            approved_clips = self.critic.evaluate_candidates(candidates, pass_threshold=65.0)
            final_selection = approved_clips[:target_clips] if approved_clips else candidates[:target_clips]
        else:
            final_selection = candidates[:target_clips]

        if not final_selection:
            logger.warning("No candidate highlights identified. Aborting render.")
            return []

        logger.info("Selected %d top highlights for rendering", len(final_selection))

        # Step 5B: Generate Hook headlines for each selected clip
        logger.info("--- Step 5B: Generating Hook Headlines ---")
        for clip in final_selection:
            clip_text = " ".join(s.get("text", "") for s in segments
                                  if s.get("start", 0) >= clip.get("start", 0) - 1
                                  and s.get("end", 0) <= clip.get("end", 0) + 1)
            self.hook_gen.enrich_clip(clip, clip_text)

        # Step 5C: Generate social posting copy
        logger.info("--- Step 5C: Generating Social Copy ---")
        final_selection = self.social_gen.generate_all(final_selection)

        # Step 6: Layout Selection
        if force_layout:
            chosen_layout = force_layout.upper()
        else:
            logger.info("--- Step 6: Determining 9:16 Video Layout ---")
            layout_res = self.layout_picker.determine_layout(video_path, meta["duration"])
            chosen_layout = layout_res["layout"]
        logger.info("Using layout: %s", chosen_layout)

        # Step 7 & 8: Subtitles & Hardware Render
        rendered_outputs: List[Path] = []
        for idx, clip in enumerate(final_selection, 1):
            logger.info("--- Rendering Short %d/%d: '%s' ---", idx, len(final_selection), clip.get("title", ""))

            # Calculate smoothed face tracking crop box if TRACK layout is active
            crop_box = None
            if chosen_layout == "TRACK":
                crop_box = self.reframer.calculate_crop_box(
                    video_path=video_path,
                    start_time=clip["start"],
                    end_time=clip["end"],
                    src_width=meta.get("width", 1920),
                    src_height=meta.get("height", 1080),
                    scene_cuts=meta.get("scene_cuts"),
                )

            # Generate word-level ASS subtitles
            sub_file = config.TEMP_DIR / f"sub_{video_path.stem}_{idx}.ass"
            self.sub_gen.generate_ass(
                words=cleaned_words,
                output_file=sub_file,
                clip_start=clip["start"],
                clip_end=clip["end"],
                hook_headline=clip.get("hook"),
            )

            # Render 9:16 short with NVENC
            out_clip = self.renderer.render_clip(
                video_path=video_path,
                clip_info=clip,
                subtitle_path=sub_file,
                layout=chosen_layout,
                crop_box=crop_box,
                output_filename=f"short_{idx:02d}_{clip.get('title', 'clip').replace(' ', '_')[:25]}.mp4",
            )
            rendered_outputs.append(out_clip)

            # Write per-clip JSON metadata (hook, social copy, timings) alongside the MP4
            meta_path = out_clip.with_suffix(".mp4.meta.json")
            import json as _json
            _json.dump(
                {
                    "source": source,
                    "clip_index": idx,
                    "start": clip.get("start"),
                    "end": clip.get("end"),
                    "title": clip.get("title"),
                    "hook": clip.get("hook"),
                    "viral_score": clip.get("viral_score"),
                    "reason": clip.get("reason"),
                    "layout": chosen_layout,
                    "brand": self.brand_kit.name,
                    "social": clip.get("social", {}),
                },
                meta_path.open("w", encoding="utf-8"),
                indent=2,
            )
            logger.info("Wrote clip metadata: %s", meta_path)

        logger.info("=== Pipeline Complete! Rendered %d shorts to: %s ===", len(rendered_outputs), config.OUTPUT_DIR)
        return rendered_outputs


def main():
    parser = argparse.ArgumentParser(description="VideoShorts: Unified AI Video Clipping Engine")
    parser.add_argument("source", help="YouTube URL or path to local video file")
    parser.add_argument("--clips", type=int, default=3, help="Number of viral shorts to generate (default: 3)")
    parser.add_argument("--no-deep", action="store_true", help="Disable Deep Clips multi-moment synthesis")
    parser.add_argument("--no-critic", action="store_true", help="Skip 3-pass statistical AI critic filter")
    parser.add_argument("--no-honesty", action="store_true", help="Skip deep-clip honesty gate")
    parser.add_argument("--brand", choices=BrandKit.available_presets(), default="default", help="Brand/preset style")
    parser.add_argument("--layout", choices=["TRACK", "SPLIT", "GENERAL", "SCREENCAST"], help="Force specific 9:16 layout")

    args = parser.parse_args()
    pipeline = VideoShortsPipeline(brand_preset=args.brand)
    pipeline.run(
        source=args.source,
        target_clips=args.clips,
        enable_deep_clips=not args.no_deep,
        enable_critic=not args.no_critic,
        enable_honesty=not args.no_honesty,
        force_layout=args.layout,
    )


if __name__ == "__main__":
    main()
