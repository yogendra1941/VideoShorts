"""FastAPI REST API server for VideoShorts."""

import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import config
from main import VideoShortsPipeline
from core.hooks import HookGenerator
from core.social import SocialCopyGenerator
from core.honesty import HonestyGate
from core.brand import BrandKit
from core.security import validate_source_url, sanitize_filename

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VideoShorts.API")

app = FastAPI(title="VideoShorts API", version="2.0")

# Enable CORS for Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job tracker
jobs: Dict[str, Dict[str, Any]] = {}
pipeline = VideoShortsPipeline()


class JobRequest(BaseModel):
    source: str
    clips: int = 3
    layout: Optional[str] = None
    brand: str = "default"
    enable_deep_clips: bool = True
    enable_critic: bool = True
    enable_honesty: bool = True
    generate_social: bool = True


def _run_pipeline_job(job_id: str, req: JobRequest):
    """Background task to run video processing."""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = "Ingesting video and extracting audio..."

        # SSRF guard: reject URL sources that target private/link-local/loopback.
        if req.source.strip().lower().startswith(("http://", "https://")):
            req.source = validate_source_url(req.source)

        # Step 1: Ingest
        meta = pipeline.ingestor.process_source(req.source)
        video_path = Path(meta["video_path"])
        audio_path = Path(meta["audio_path"])
        jobs[job_id]["title"] = meta["title"]
        jobs[job_id]["duration"] = meta["duration"]
        jobs[job_id]["progress"] = 30
        jobs[job_id]["step"] = "Transcribing audio with faster-whisper..."

        # Step 2: Transcribe
        asr_res = pipeline.transcriber.transcribe(audio_path)
        words = asr_res["words"]
        segments = asr_res["segments"]
        jobs[job_id]["progress"] = 50
        jobs[job_id]["step"] = "Cleaning speech and trimming silence..."

        # Step 3: Trim
        cleaned_words = pipeline.trimmer.clean_word_stream(words)
        jobs[job_id]["progress"] = 60
        jobs[job_id]["step"] = "AI finding viral highlights with Inception Labs (mercury-3)..."

        # Step 4: Scoring
        candidates = pipeline.scorer.find_highlights(
            transcript_segments=segments,
            min_duration=config.MIN_CLIP_DURATION,
            max_duration=config.MAX_CLIP_DURATION,
            target_clips=req.clips * 2,
            fallback_total_duration=meta.get("duration", 0.0),
        )

        # Deep clips (with honesty gate)
        if req.enable_deep_clips and meta["duration"] >= 180.0:
            deep_clips = pipeline.deep_engine.synthesize_deep_clips(segments, max_clips=2)
            if req.enable_honesty and deep_clips:
                deep_clips = pipeline.honesty_gate.filter_honest(deep_clips)
            candidates.extend(deep_clips)

        # Step 5: Critic
        if req.enable_critic and candidates:
            approved = pipeline.critic.evaluate_candidates(candidates)
            final_selection = approved[:req.clips] if approved else candidates[:req.clips]
        else:
            final_selection = candidates[:req.clips]

        # Generate hooks + social copy for the final selection
        hook_gen = HookGenerator()
        social_gen = SocialCopyGenerator()
        for clip in final_selection:
            clip_text = " ".join(s.get("text", "") for s in segments
                                  if s.get("start", 0) >= clip.get("start", 0) - 1
                                  and s.get("end", 0) <= clip.get("end", 0) + 1)
            hook_gen.enrich_clip(clip, clip_text)
            if req.generate_social:
                social_gen.generate(clip)

        jobs[job_id]["progress"] = 75
        jobs[job_id]["step"] = "Reframing and rendering vertical 9:16 shorts..."

        # Layout selection
        if req.layout:
            chosen_layout = req.layout.upper()
        else:
            layout_res = pipeline.layout_picker.determine_layout(video_path, meta["duration"])
            chosen_layout = layout_res["layout"]

        # Step 6: Render
        rendered_clips = []
        for idx, clip in enumerate(final_selection, 1):
            sub_file = config.TEMP_DIR / f"sub_{video_path.stem}_{idx}.ass"
            pipeline.sub_gen.generate_ass(
                words=cleaned_words,
                output_file=sub_file,
                clip_start=clip["start"],
                clip_end=clip["end"],
                hook_headline=clip.get("hook"),
            )

            crop_box = None
            if chosen_layout == "TRACK":
                crop_box = pipeline.reframer.calculate_crop_box(
                    video_path=video_path,
                    start_time=clip["start"],
                    end_time=clip["end"],
                    src_width=meta.get("width", 1920),
                    src_height=meta.get("height", 1080),
                )

            out_clip = pipeline.renderer.render_clip(
                video_path=video_path,
                clip_info=clip,
                subtitle_path=sub_file,
                layout=chosen_layout,
                crop_box=crop_box,
                output_filename=f"short_{job_id[:6]}_{idx:02d}.mp4",
            )

            rendered_clips.append({
                "id": idx,
                "title": clip.get("title", f"Short {idx}"),
                "hook": clip.get("hook", ""),
                "score": clip.get("viral_score", 85),
                "start": clip["start"],
                "end": clip["end"],
                "filename": out_clip.name,
                "url": f"/api/clips/{out_clip.name}",
                "social": clip.get("social", {}),
                "honesty": clip.get("honesty", {}),
            })

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["step"] = "Complete"
        jobs[job_id]["clips"] = rendered_clips
        logger.info("Job %s completed successfully with %d clips", job_id, len(rendered_clips))

    except Exception as e:
        logger.error("Job %s failed: %s", job_id, e, exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.post("/api/jobs")
def create_job(req: JobRequest, background_tasks: BackgroundTasks):
    """Enqueues a new video clipping job."""
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "id": job_id,
        "source": req.source,
        "status": "queued",
        "progress": 0,
        "step": "Queued",
        "clips": [],
        "error": None,
    }
    background_tasks.add_task(_run_pipeline_job, job_id, req)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Returns status and progress of a job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/brands")
def list_brands():
    """Returns available brand/preset styles."""
    return {"presets": BrandKit.available_presets(), "current": "default"}


class HookRequest(BaseModel):
    clip_text: str = ""
    clip_title: str = ""


@app.post("/api/hook")
def generate_hook(req: HookRequest):
    """Generates a hook headline for a clip transcript."""
    try:
        hook = HookGenerator().generate_hook(req.clip_text, req.clip_title)
        return {"hook": hook}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hook generation failed: {e}")


class SocialRequest(BaseModel):
    hook: str = ""
    title: str = ""
    reason: str = ""


@app.post("/api/social")
def generate_social(req: SocialRequest):
    """Generates per-platform posting metadata for a clip."""
    try:
        clip = SocialCopyGenerator().generate({
            "hook": req.hook,
            "title": req.title,
            "reason": req.reason,
        })
        return {"social": clip.get("social", {})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Social copy generation failed: {e}")


@app.get("/api/clips/{filename}")
def stream_clip(filename: str):
    """Serves rendered video file (sanitized to prevent path traversal)."""
    safe = sanitize_filename(filename)
    clip_path = config.OUTPUT_DIR / safe
    if not clip_path.exists():
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(clip_path, media_type="video/mp4")


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": config.LLM_PROVIDER, "asr": config.ASR_DEVICE}


@app.get("/api/config")
def app_config():
    """Application config for the web dashboard.

    billingEnabled=false puts the UI in full free self-hosted mode: no plan
    gates, no checkout, no watermark/top-up prompts, no trials. Everything is
    unlocked. localLlm=true tells the frontend no external Gemini key is needed
    (the Inception/Ollama backend serves the LLM for free).
    """
    return {
        "billingEnabled": False,
        "googleAuthEnabled": False,
        "localLlm": True,
        "jobRetentionSeconds": None,
        "provider": config.LLM_PROVIDER,
    }


# Serve built Web UI if present
web_dist = config.PROJECT_ROOT / "web" / "dist"
if web_dist.exists():
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
