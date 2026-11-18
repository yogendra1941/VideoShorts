"""FastAPI REST API server for VideoShorts."""

import os
import uuid
import logging
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, File, UploadFile
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
from core.subtitles import SubtitleGenerator
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


def _log_event(job_id: str, msg: str):
    """Appends an event to the job log history."""
    logger.info("[%s] %s", job_id, msg)
    if job_id in jobs:
        jobs[job_id]["logs"].append(msg)
        jobs[job_id]["step"] = msg


def _run_pipeline_job(job_id: str, req: JobRequest):
    """Background task to run video processing."""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 5
        _log_event(job_id, "Initializing VideoShorts AI pipeline...")

        # SSRF guard: reject URL sources that target private/link-local/loopback.
        if req.source.strip().lower().startswith(("http://", "https://")):
            _log_event(job_id, f"Validating source URL security: {req.source}")
            req.source = validate_source_url(req.source)

        # Step 1: Ingest
        _log_event(job_id, "Ingesting video source and extracting 16kHz mono audio...")
        jobs[job_id]["progress"] = 15
        meta = pipeline.ingestor.process_source(req.source)
        video_path = Path(meta["video_path"])
        audio_path = Path(meta["audio_path"])
        jobs[job_id]["title"] = meta["title"]
        jobs[job_id]["duration"] = meta["duration"]
        jobs[job_id]["progress"] = 30

        # Step 2: Transcribe
        _log_event(job_id, f"Transcribing speech with Faster-Whisper ({config.ASR_DEVICE})...")
        asr_res = pipeline.transcriber.transcribe(audio_path)
        words = asr_res["words"]
        segments = asr_res["segments"]
        jobs[job_id]["progress"] = 50
        _log_event(job_id, f"Transcription finished: {len(words)} words in {len(segments)} segments.")

        # Step 3: Trim
        _log_event(job_id, "Cleaning filler tics ('um', 'uh') and trimming long pauses...")
        cleaned_words = pipeline.trimmer.clean_word_stream(words)
        jobs[job_id]["progress"] = 60

        # Step 4: Scoring
        _log_event(job_id, f"Evaluating virality dimensions with {config.LLM_PROVIDER.upper()}...")
        candidates = pipeline.scorer.find_highlights(
            transcript_segments=segments,
            min_duration=config.MIN_CLIP_DURATION,
            max_duration=config.MAX_CLIP_DURATION,
            target_clips=req.clips * 2,
            fallback_total_duration=meta.get("duration", 0.0),
        )

        # Deep clips (with honesty gate)
        if req.enable_deep_clips and meta["duration"] >= 180.0:
            _log_event(job_id, "Synthesizing deep thematic threads across video scenes...")
            deep_clips = pipeline.deep_engine.synthesize_deep_clips(segments, max_clips=2)
            if req.enable_honesty and deep_clips:
                _log_event(job_id, "Filtering candidates through Honesty Gate verification...")
                deep_clips = pipeline.honesty_gate.filter_honest(deep_clips)
            candidates.extend(deep_clips)

        # Step 5: Critic
        if req.enable_critic and candidates:
            _log_event(job_id, "Running 3-run randomized AI critic blind evaluation...")
            approved = pipeline.critic.evaluate_candidates(candidates)
            final_selection = approved[:req.clips] if approved else candidates[:req.clips]
        else:
            final_selection = candidates[:req.clips]

        # Generate hooks + social copy for the final selection
        hook_gen = HookGenerator()
        social_gen = SocialCopyGenerator()
        _log_event(job_id, f"Enriching top {len(final_selection)} clips with viral hooks and social copy...")
        for clip in final_selection:
            clip_text = " ".join(s.get("text", "") for s in segments
                                  if s.get("start", 0) >= clip.get("start", 0) - 1
                                  and s.get("end", 0) <= clip.get("end", 0) + 1)
            hook_gen.enrich_clip(clip, clip_text)
            if req.generate_social:
                social_gen.generate(clip)

        jobs[job_id]["progress"] = 75

        # Layout selection
        if req.layout:
            chosen_layout = req.layout.upper()
        else:
            layout_res = pipeline.layout_picker.determine_layout(video_path, meta["duration"])
            chosen_layout = layout_res["layout"]
        _log_event(job_id, f"Selected 9:16 layout: {chosen_layout}")

        # Subtitle generator with chosen style preset
        brand_preset = BrandKit(req.brand).get_preset()
        sub_generator = SubtitleGenerator(preset=brand_preset)
        _log_event(job_id, f"Applying ASS subtitle karaoke preset: {req.brand}")

        # Step 6: Render
        rendered_clips = []
        for idx, clip in enumerate(final_selection, 1):
            _log_event(job_id, f"Rendering Short #{idx}/{len(final_selection)}: '{clip.get('title', '')}'...")
            sub_file = config.TEMP_DIR / f"sub_{video_path.stem}_{idx}.ass"
            sub_generator.generate_ass(
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

            clip_text = " ".join(s.get("text", "") for s in segments
                                 if s.get("start", 0) >= clip.get("start", 0)
                                 and s.get("end", 0) <= clip.get("end", 0))

            rendered_clips.append({
                "id": idx,
                "title": clip.get("title", f"Short {idx}"),
                "video_title_for_youtube_short": clip.get("title", f"Short {idx}"),
                "hook": clip.get("hook", ""),
                "score": clip.get("viral_score", 85),
                "predicted_score": clip.get("viral_score", 85),
                "start": clip["start"],
                "end": clip["end"],
                "filename": out_clip.name,
                "url": f"/api/clips/{out_clip.name}",
                "video_url": f"/api/clips/{out_clip.name}",
                "social": clip.get("social", {}),
                "honesty": clip.get("honesty", {}),
                "text": clip_text,
            })

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["progress"] = 100
        _log_event(job_id, f"Pipeline complete: {len(rendered_clips)} shorts generated successfully!")
        jobs[job_id]["clips"] = rendered_clips
        jobs[job_id]["results"] = {"clips": rendered_clips}
        logger.info("Job %s completed successfully with %d clips", job_id, len(rendered_clips))

    except Exception as e:
        logger.error("Job %s failed: %s", job_id, e, exc_info=True)
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        _log_event(job_id, f"Error: {e}")


@app.post("/api/jobs")
@app.post("/api/process")
async def create_job(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None)
):
    """Enqueues a new video clipping job (accepts JSON URL or multipart file upload)."""
    job_id = str(uuid.uuid4())[:8]
    content_type = request.headers.get("content-type", "")

    source = ""
    clips = 3
    layout = None
    brand = "default"
    enable_deep_clips = True
    enable_critic = True
    enable_honesty = True

    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if uploaded_file and hasattr(uploaded_file, "filename"):
            safe_name = sanitize_filename(uploaded_file.filename)
            save_path = config.INPUT_DIR / f"{job_id}_{safe_name}"
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(uploaded_file.file, buffer)
            source = str(save_path)
        clips = int(form.get("target_clips") or form.get("clips") or 3)
        layout = form.get("layouts") or form.get("layout") or None
        brand = form.get("brand") or "default"
        enable_honesty = form.get("enableHonesty") != "false"
        enable_deep_clips = form.get("enableDeepClips") != "false"
    else:
        try:
            body = await request.json()
            source = body.get("url") or body.get("source") or ""
            clips = int(body.get("target_clips") or body.get("clips") or 3)
            layout = body.get("layouts") or body.get("layout") or None
            brand = body.get("brand") or "default"
            enable_honesty = body.get("enableHonesty", True)
            enable_deep_clips = body.get("enableDeepClips", True)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request body")

    if not source:
        raise HTTPException(status_code=400, detail="Missing source URL or uploaded file")

    req = JobRequest(
        source=source,
        clips=clips,
        layout=layout,
        brand=brand,
        enable_deep_clips=enable_deep_clips,
        enable_critic=enable_critic,
        enable_honesty=enable_honesty,
    )

    jobs[job_id] = {
        "id": job_id,
        "job_id": job_id,
        "source": source,
        "status": "processing",
        "progress": 0,
        "step": "Queued",
        "logs": ["Job enqueued. Initializing pipeline..."],
        "clips": [],
        "results": {"clips": []},
        "error": None,
    }

    background_tasks.add_task(_run_pipeline_job, job_id, req)
    return {"job_id": job_id, "id": job_id, "status": "processing"}


@app.get("/api/jobs/{job_id}")
@app.get("/api/status/{job_id}")
def get_job_status(job_id: str):
    """Returns status, logs, and clips of a job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    status_mapped = "complete" if job["status"] in ("completed", "complete") else ("error" if job["status"] == "failed" else job["status"])
    return {
        **job,
        "status": status_mapped,
        "logs": job.get("logs", [job.get("step", "Processing...")]),
        "clips": job.get("clips", []),
        "results": {"clips": job.get("clips", [])},
    }


@app.get("/api/brands")
def list_brands():
    """Returns available brand/preset styles."""
    return {"presets": BrandKit.available_presets(), "current": "cyber_neon"}


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


@app.get("/api/history")
def get_history():
    """Returns past rendered clips from the output directory."""
    videos = []
    if config.OUTPUT_DIR.exists():
        for f in sorted(config.OUTPUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
            videos.append({
                "id": f.stem,
                "job_id": f.stem.split("_")[1] if "_" in f.stem else "local",
                "filename": f.name,
                "url": f"/api/clips/{f.name}",
                "created_at": f.stat().st_mtime,
                "size": f.stat().st_size,
            })
    return {"videos": videos}


@app.get("/api/clips/{filename}")
def stream_clip(filename: str):
    """Serves rendered video file (sanitized to prevent path traversal)."""
    safe = sanitize_filename(filename)
    clip_path = config.OUTPUT_DIR / safe
    if not clip_path.exists():
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(clip_path, media_type="video/mp4")


@app.get("/api/download-all/{job_id}")
def download_all_zip(job_id: str):
    """Creates a zip archive of all clips for a job and returns it."""
    if job_id not in jobs or not jobs[job_id].get("clips"):
        raise HTTPException(status_code=404, detail="No clips available for download")

    zip_path = config.OUTPUT_DIR / f"videoshorts_{job_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for clip in jobs[job_id]["clips"]:
            fname = clip["filename"]
            fpath = config.OUTPUT_DIR / fname
            if fpath.exists():
                zipf.write(fpath, arcname=fname)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"videoshorts_{job_id}.zip"
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": config.LLM_PROVIDER, "asr": config.ASR_DEVICE}


@app.get("/api/config")
def app_config():
    """Application config for the web dashboard."""
    return {
        "billingEnabled": False,
        "googleAuthEnabled": False,
        "localLlm": True,
        "jobRetentionSeconds": None,
        "provider": config.LLM_PROVIDER,
        "brand": "cyber_neon",
    }


# Serve built Web UI if present
web_dist = config.PROJECT_ROOT / "web" / "dist"
if web_dist.exists():
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
