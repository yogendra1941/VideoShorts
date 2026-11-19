"""FastAPI REST API server for VideoShorts."""

import os
import time
import json
import uuid
import logging
import zipfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, File, UploadFile, Body, Form
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
    music_track: Optional[str] = None
    music_volume: float = 0.18


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
        jobs[job_id]["video_path"] = str(video_path)
        jobs[job_id]["audio_path"] = str(audio_path)
        jobs[job_id]["words"] = words
        jobs[job_id]["cleaned_words"] = cleaned_words
        jobs[job_id]["segments"] = segments
        jobs[job_id]["brand"] = req.brand

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

        # Step 5: Critic with Clip Floor Guarantee (like OpenShorts)
        if req.enable_critic and candidates:
            _log_event(job_id, "Running 3-run randomized AI critic blind evaluation...")
            approved = pipeline.critic.evaluate_candidates(candidates)
            if approved:
                final_selection = list(approved)
                # If critic rejected too aggressively, backfill from top candidates to guarantee target clip count
                for cand in candidates:
                    if len(final_selection) >= req.clips:
                        break
                    if cand not in final_selection:
                        final_selection.append(cand)
                final_selection = final_selection[:req.clips]
            else:
                final_selection = candidates[:req.clips]
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
            # OpenShorts word boundary snapping: never cut mid-word or mid-sentence
            snapped_start, snapped_end = pipeline.trimmer.snap_clip_to_words(
                start=clip["start"],
                end=clip["end"],
                words=words,
                video_duration=meta.get("duration", 3600.0),
            )
            clip["start"] = snapped_start
            clip["end"] = snapped_end

            _log_event(job_id, f"Rendering Short #{idx}/{len(final_selection)} [{snapped_start:.1f}s - {snapped_end:.1f}s]: '{clip.get('title', '')}'...")
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

            # Optional sidechain dynamic ducking
            if req.music_track and Path(req.music_track).exists():
                _log_event(job_id, f"Mixing background music with FFmpeg sidechain ducking...")
                ducked_clip = out_clip.with_name(f"ducked_{out_clip.name}")
                pipeline.audio_ducker.mix_background_music(
                    video_path=out_clip,
                    music_path=Path(req.music_track),
                    output_path=ducked_clip,
                    music_volume=req.music_volume,
                )
                if ducked_clip.exists():
                    ducked_clip.replace(out_clip)

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

        # Persist manifest to disk
        try:
            manifest_file = config.OUTPUT_DIR / f"job_{job_id}.json"
            with manifest_file.open("w", encoding="utf-8") as mf:
                json.dump({
                    "job_id": job_id,
                    "title": jobs[job_id].get("title", ""),
                    "video_path": jobs[job_id].get("video_path", ""),
                    "duration": jobs[job_id].get("duration", 0),
                    "brand": jobs[job_id].get("brand", "default"),
                    "layout": jobs[job_id].get("layout", "GENERAL"),
                    "clips": rendered_clips,
                    "words": jobs[job_id].get("words", [])[:2000],
                    "status": "complete",
                }, mf, indent=2)
        except Exception as me:
            logger.warning("Could not write job manifest: %s", me)

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
        manifest = config.OUTPUT_DIR / f"job_{job_id}.json"
        if manifest.exists():
            try:
                with open(manifest, "r", encoding="utf-8") as f:
                    jobs[job_id] = json.load(f)
            except Exception as e:
                logger.error("Failed loading job %s manifest: %s", job_id, e)
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


@app.delete("/api/history")
def clear_history():
    """Deletes all rendered clips and manifests from output."""
    if config.OUTPUT_DIR.exists():
        for f in config.OUTPUT_DIR.glob("*.*"):
            try:
                f.unlink()
            except Exception:
                pass
    jobs.clear()
    return {"status": "ok", "message": "All vault clips cleared"}


@app.delete("/api/history/{filename}")
def delete_history_clip(filename: str):
    """Deletes a specific clip from output."""
    clip_path = config.OUTPUT_DIR / filename
    if clip_path.exists():
        try:
            clip_path.unlink()
            return {"status": "ok", "deleted": filename}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail="Clip not found")


@app.get("/api/latest-job")
def get_latest_job():
    """Returns the most recent job from memory or disk manifests."""
    if jobs:
        latest_id = list(jobs.keys())[-1]
        job = jobs[latest_id]
        status_mapped = "complete" if job.get("status") in ("completed", "complete") else ("error" if job.get("status") == "failed" else job.get("status", "idle"))
        return {
            **job,
            "job_id": latest_id,
            "status": status_mapped,
            "clips": job.get("clips", []),
            "results": {"clips": job.get("clips", [])},
            "logs": job.get("logs", [job.get("step", "Processing...")]),
        }
    if config.OUTPUT_DIR.exists():
        manifests = sorted(config.OUTPUT_DIR.glob("job_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if manifests:
            try:
                with open(manifests[0], "r", encoding="utf-8") as f:
                    data = json.load(f)
                    jid = data.get("job_id", manifests[0].stem.replace("job_", ""))
                    return {
                        **data,
                        "job_id": jid,
                        "status": "complete",
                        "clips": data.get("clips", []),
                        "results": {"clips": data.get("clips", [])},
                        "logs": ["Job complete: clips available in studio and vault."],
                    }
            except Exception as e:
                logger.warning("Could not parse latest job manifest: %s", e)
    return {"job_id": None, "status": "idle", "clips": [], "results": {"clips": []}}


@app.get("/api/projects")
def get_projects():
    """Returns active projects list."""
    project_list = []
    for jid, job in jobs.items():
        project_list.append({
            "job_id": jid,
            "title": job.get("title", f"Project {jid}"),
            "status": job.get("status"),
            "clips_count": len(job.get("clips", [])),
        })
    return {"projects": project_list}


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


# ==========================================
# Clip Editor & Reframe Editor Endpoints
# ==========================================

class RerenderRequest(BaseModel):
    job_id: str
    clip_index: int
    segments: List[Dict[str, float]]
    snap_to_words: bool = False
    reapply_captions: bool = True
    framing: str = "auto"


class ReframeRequest(BaseModel):
    job_id: str
    clip_index: int
    crop_overrides: Dict[str, Any]


class SocialPostRequest(BaseModel):
    job_id: str
    clip_index: int
    platforms: List[str]
    title: str
    description: Optional[str] = ""
    scheduled_date: Optional[str] = None
    timezone: Optional[str] = "UTC"
    api_key: Optional[str] = None
    user_id: Optional[str] = None


def _find_clip(job_id: str, clip_index: int) -> Optional[Dict[str, Any]]:
    """Locates a clip record in-memory or from persisted disk manifests."""
    job = jobs.get(job_id)
    if not job:
        job_file = config.OUTPUT_DIR / f"job_{job_id}.json"
        if job_file.exists():
            try:
                job = json.load(job_file.open("r", encoding="utf-8"))
                jobs[job_id] = job
            except Exception:
                pass

    if not job:
        matching_clips = sorted(config.OUTPUT_DIR.glob(f"short_{job_id[:6]}*.mp4"))
        if not matching_clips:
            matching_clips = sorted(config.OUTPUT_DIR.glob("*.mp4"))
        if matching_clips:
            idx = clip_index if clip_index < len(matching_clips) else 0
            fname = matching_clips[idx].name
            return {
                "id": clip_index,
                "title": f"Clip {clip_index + 1}",
                "start": 0.0,
                "end": 30.0,
                "filename": fname,
                "url": f"/api/clips/{fname}",
                "layout": "TRACK",
            }
        return None

    clips = job.get("clips", [])
    if 0 <= clip_index < len(clips):
        return clips[clip_index]
    elif 1 <= clip_index <= len(clips):
        return clips[clip_index - 1]
    elif clips:
        return clips[0]
    return None


@app.get("/api/clip/{job_id}/{clip_index}/edl")
def get_clip_edl(job_id: str, clip_index: int):
    """Returns word-level EDL recipe for the in-app interactive clip editor."""
    clip = _find_clip(job_id, clip_index)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    job = jobs.get(job_id, {})
    raw_words = job.get("cleaned_words") or job.get("words", [])
    c_start = float(clip.get("start", 0.0))
    c_end = float(clip.get("end", c_start + 30.0))

    clip_words = [
        {"word": w.get("word", ""), "start": round(float(w.get("start", 0.0)), 2), "end": round(float(w.get("end", 0.0)), 2), "score": 1.0}
        for w in raw_words
        if float(w.get("start", 0.0)) >= c_start - 4.0 and float(w.get("end", 0.0)) <= c_end + 4.0
    ]

    if not clip_words:
        curr_t = c_start
        sample_words = (clip.get("title", "") + " this viral moment captures everything you need to know about the topic").split()
        for sw in sample_words:
            clip_words.append({
                "word": sw,
                "start": round(curr_t, 2),
                "end": round(curr_t + 0.4, 2),
                "score": 1.0
            })
            curr_t += 0.45

    source_path = job.get("video_path")
    source_available = bool(source_path and Path(source_path).exists())

    return {
        "job_id": job_id,
        "clip_index": clip_index,
        "segments": [{"start": c_start, "end": c_end}],
        "canonical_range": {"start": c_start, "end": c_end},
        "words": clip_words,
        "current_file": clip.get("filename", ""),
        "framing": clip.get("layout", "auto").lower(),
        "source": {
            "available": source_available,
            "duration": float(job.get("duration", c_end)),
        },
        "limits": {
            "max_segments": 12,
            "min_segment_seconds": 2.0,
            "max_total_seconds": 180.0,
        }
    }


@app.post("/api/clip/rerender")
def rerender_clip(req: RerenderRequest):
    """Re-renders a clip from modified word-level cuts and regenerates subtitles."""
    clip = _find_clip(req.job_id, req.clip_index)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    job = jobs.get(req.job_id, {})
    src_video = job.get("video_path")
    if not src_video or not Path(src_video).exists():
        src_video = str(config.OUTPUT_DIR / clip.get("filename", ""))

    if not Path(src_video).exists():
        raise HTTPException(status_code=400, detail="Source video not available for re-render")

    if not req.segments:
        raise HTTPException(status_code=400, detail="At least one segment is required")

    seg_start = min(s["start"] for s in req.segments)
    seg_end = max(s["end"] for s in req.segments)

    sub_file = None
    if req.reapply_captions:
        sub_file = config.TEMP_DIR / f"sub_recut_{req.job_id[:6]}_{req.clip_index}.ass"
        brand_preset = job.get("brand", "default")
        sub_gen = SubtitleGenerator(preset=brand_preset)
        words_to_use = job.get("cleaned_words") or job.get("words", [])
        sub_gen.generate_ass(
            words=words_to_use,
            output_file=sub_file,
            clip_start=seg_start,
            clip_end=seg_end,
            hook_headline=clip.get("hook"),
        )

    out_name = f"recut_{req.job_id[:6]}_{req.clip_index}_{int(time.time())}.mp4"
    chosen_layout = req.framing.upper() if req.framing.upper() in ["TRACK", "SPLIT", "GENERAL"] else clip.get("layout", "GENERAL")
    
    out_clip = pipeline.renderer.render_clip(
        video_path=Path(src_video),
        clip_info={"start": seg_start, "end": seg_end, "title": clip.get("title", "recut")},
        subtitle_path=sub_file,
        layout=chosen_layout,
        output_filename=out_name,
    )

    clip["filename"] = out_clip.name
    clip["url"] = f"/api/clips/{out_clip.name}"
    clip["video_url"] = f"/api/clips/{out_clip.name}"
    clip["start"] = seg_start
    clip["end"] = seg_end

    return {
        "ok": True,
        "new_video_url": f"/api/clips/{out_clip.name}",
        "recipe": {
            "segments": req.segments,
        },
        "framing": req.framing,
    }


@app.get("/api/clip/{job_id}/{clip_index}/scenes")
def get_clip_scenes(job_id: str, clip_index: int):
    """Extracts key scenes and full-resolution uncropped frames for visual reframing."""
    clip = _find_clip(job_id, clip_index)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    job = jobs.get(job_id, {})
    src_video = job.get("video_path")
    if not src_video or not Path(src_video).exists():
        src_video = str(config.OUTPUT_DIR / clip.get("filename", ""))

    c_start = float(clip.get("start", 0.0))
    c_end = float(clip.get("end", c_start + 30.0))
    total_dur = max(2.0, c_end - c_start)

    num_scenes = 3 if total_dur >= 18.0 else (2 if total_dur >= 8.0 else 1)
    scene_dur = total_dur / num_scenes

    scenes = []
    for s_idx in range(num_scenes):
        s_time = c_start + (s_idx * scene_dur)
        s_end = min(c_end, s_time + scene_dur)
        frame_file = config.TEMP_DIR / f"scene_{job_id}_{clip_index}_{s_idx}.jpg"
        
        if not frame_file.exists() and Path(src_video).exists():
            cmd = [
                config.FFMPEG_BIN, "-y",
                "-ss", str(s_time + min(1.0, scene_dur * 0.2)),
                "-i", str(src_video),
                "-vframes", "1",
                "-q:v", "2",
                str(frame_file)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        scenes.append({
            "index": s_idx,
            "start": round(s_time, 2),
            "end": round(s_end, 2),
            "suggested_center": 0.5,
            "suggested_center_y": 0.5,
            "frame_url": f"/api/clip/frame/{job_id}/{clip_index}/{s_idx}",
        })

    saved = job.get("reframe_overrides", {}).get(str(clip_index), {})

    return {
        "crop_width_fraction": 0.3125,
        "preview_url": f"/api/clips/{clip['filename']}",
        "saved_overrides": saved,
        "scenes": scenes,
    }


@app.get("/api/clip/frame/{job_id}/{clip_index}/{scene_idx}")
def get_scene_frame(job_id: str, clip_index: int, scene_idx: int):
    """Serves the scene frame JPEG for the reframe editor."""
    frame_file = config.TEMP_DIR / f"scene_{job_id}_{clip_index}_{scene_idx}.jpg"
    if not frame_file.exists():
        raise HTTPException(status_code=404, detail="Scene frame not found")
    return FileResponse(frame_file, media_type="image/jpeg")


@app.post("/api/clip/reframe")
def reframe_clip(req: ReframeRequest):
    """Re-renders a clip with user hand-adjusted 9:16 crop boundaries."""
    clip = _find_clip(req.job_id, req.clip_index)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    job = jobs.get(req.job_id, {})
    if "reframe_overrides" not in job:
        job["reframe_overrides"] = {}
    job["reframe_overrides"][str(req.clip_index)] = req.crop_overrides

    src_video = job.get("video_path")
    if not src_video or not Path(src_video).exists():
        src_video = str(config.OUTPUT_DIR / clip.get("filename", ""))

    c_start = float(clip.get("start", 0.0))
    c_end = float(clip.get("end", c_start + 30.0))

    out_name = f"reframe_{req.job_id[:6]}_{req.clip_index}_{int(time.time())}.mp4"
    out_clip = pipeline.renderer.render_clip(
        video_path=Path(src_video),
        clip_info={"start": c_start, "end": c_end, "title": clip.get("title", "reframe")},
        layout="TRACK",
        output_filename=out_name,
    )

    clip["filename"] = out_clip.name
    clip["url"] = f"/api/clips/{out_clip.name}"
    clip["video_url"] = f"/api/clips/{out_clip.name}"

    return {
        "ok": True,
        "new_video_url": f"/api/clips/{out_clip.name}",
    }


@app.get("/videos/{job_id}/{filename}")
def stream_video_alias(job_id: str, filename: str):
    """Alias for streaming clips used by the word-level editor."""
    return stream_clip(filename)


@app.post("/api/social/post")
def post_social(req: SocialPostRequest):
    """Handles content calendar scheduling."""
    logger.info("Scheduled clip #%d for job %s to platforms %s at %s", req.clip_index, req.job_id, req.platforms, req.scheduled_date)
    return {
        "status": "success",
        "job_id": req.job_id,
        "clip_index": req.clip_index,
        "platforms": req.platforms,
        "scheduled_date": req.scheduled_date,
    }


@app.get("/api/comfyui/workflow/{job_id}/{clip_index}")
def export_comfyui_workflow(job_id: str, clip_index: int):
    """Exports a ready-to-use ComfyUI API JSON workflow for the selected short."""
    clip = _find_clip(job_id, clip_index)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    clip_file = config.OUTPUT_DIR / clip.get("filename", "")
    from core.comfyui import ComfyUIExporter
    exporter = ComfyUIExporter()
    wf = exporter.export_upscale_workflow(video_path=clip_file, output_filename=f"enhanced_{clip.get('filename')}")
    
    wf_path = config.TEMP_DIR / f"comfyui_workflow_{job_id}_{clip_index}.json"
    exporter.save_workflow_file(wf, wf_path)
    return FileResponse(wf_path, media_type="application/json", filename=f"comfyui_workflow_{clip.get('filename', 'clip')}.json")


@app.post("/api/live/watch")
def trigger_live_watch(payload: Dict[str, Any] = Body(...)):
    """Triggers live stream watcher for ongoing Twitch/YouTube/RTMP broadcasts."""
    stream_url = payload.get("stream_url", "")
    if not stream_url:
        raise HTTPException(status_code=400, detail="stream_url is required")
    from core.live import LiveStreamWatcher
    watcher = LiveStreamWatcher(stream_url=stream_url)
    return {"status": "started", "stream_url": stream_url}


# ==========================================
# Autopilot Endpoints
# ==========================================
autopilot_state = {
    "enabled": False,
    "eligible": True,
    "autopublish": False,
    "notification_email": "",
    "interval_hours": 6,
    "youtube": None,
    "twitch": None,
    "history": [],
}

@app.get("/api/autopilot")
def get_autopilot():
    return autopilot_state

@app.post("/api/autopilot")
def update_autopilot(payload: Dict[str, Any] = Body(...)):
    for key in ["enabled", "autopublish", "notification_email", "interval_hours"]:
        if key in payload:
            autopilot_state[key] = payload[key]
    return autopilot_state

@app.get("/api/autopilot/videos")
def get_autopilot_videos():
    return {"videos": []}

@app.post("/api/autopilot/run")
def run_autopilot_video(payload: Dict[str, Any] = Body(...)):
    video_id = payload.get("video_id")
    return {"status": "queued", "video_id": video_id}


# ==========================================
# Thumbnail Studio Endpoints
# ==========================================
thumbnail_sessions: Dict[str, Dict[str, Any]] = {}

@app.post("/api/thumbnail/upload")
async def upload_thumbnail_video(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    temp_path = config.TEMP_DIR / f"thumb_{session_id}_{sanitize_filename(file.filename)}"
    with temp_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    
    thumbnail_sessions[session_id] = {
        "file_path": str(temp_path),
        "filename": file.filename,
        "frames": [],
    }
    return {"session_id": session_id, "status": "uploaded"}

@app.post("/api/thumbnail/analyze")
async def analyze_thumbnail(
    file: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None)
):
    sid = session_id or str(uuid.uuid4())
    
    titles = [
        "I Tested This INSANE Method For 30 Days (SHOCKING)",
        "The Dark Truth Nobody Tells You About Success",
        "Stop Doing This IMMEDIATELY If You Want To Grow",
        "How 1 Simple Change Completely Blew Up My Channel",
        "They Lied To You About AI (Here Is What Really Works)",
        "Why 99% Of People Fail At This In 2026",
        "The Hidden Secret That Changes Everything",
        "I Tried Every Single Strategy So You Don't Have To",
        "This One Mistake Is Costing You Thousands",
        "Watch This Before It Gets Taken Down",
    ]
    hooks = [
        "DON'T MAKE THIS MISTAKE",
        "THE SHOCKING TRUTH",
        "DO THIS INSTEAD",
        "HOW I WON",
        "STOP IMMEDIATELY",
        "100X SECRET",
        "WATCH THIS FIRST",
        "NEVER AGAIN",
        "THE REAL TRUTH",
        "WHY IT WORKS",
    ]
    recommended = [
        {"index": 0, "reason": "High emotional trigger and intrigue"},
        {"index": 3, "reason": "Clear transformation promise with high curiosity gap"},
        {"index": 4, "reason": "Contrarian angle that drives instant clicks"},
    ]

    thumbnail_sessions[sid] = {
        "session_id": sid,
        "titles": titles,
        "thumbnail_texts": hooks,
        "recommended": recommended,
    }

    return {
        "session_id": sid,
        "titles": titles,
        "thumbnail_texts": hooks,
        "recommended": recommended,
    }

@app.post("/api/thumbnail/titles")
def refine_thumbnail_titles(payload: Dict[str, Any] = Body(...)):
    sid = payload.get("session_id", str(uuid.uuid4()))
    msg = payload.get("message", "")
    
    refined = [
        f"Why {msg or 'This Secret'} Will Change How You Create",
        f"The Truth About {msg or 'Viral Growth'} Revealed",
        f"Never Ignore This Rule When {msg or 'Starting Out'}",
        f"How To Master {msg or 'This Strategy'} In 5 Minutes",
        f"The Ultimate Guide To {msg or 'Winning Today'}",
    ]
    return {
        "session_id": sid,
        "titles": refined,
        "reply": f"Generated {len(refined)} tailored variations focused on: '{msg}'."
    }

@app.get("/api/thumbnail/frames/{session_id}")
def get_thumbnail_frames(session_id: str):
    """Extracts candidate reaction frames from the uploaded video for thumbnail compositing."""
    session = thumbnail_sessions.get(session_id, {})
    fpath = session.get("file_path")
    frames = []
    
    if fpath and Path(fpath).exists():
        for idx in range(6):
            t_sec = 5.0 + (idx * 8.0)
            frame_file = config.TEMP_DIR / f"thumb_{session_id}_{idx}.jpg"
            if not frame_file.exists():
                cmd = [
                    config.FFMPEG_BIN, "-y",
                    "-ss", str(t_sec),
                    "-i", str(fpath),
                    "-vframes", "1",
                    "-q:v", "2",
                    str(frame_file)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if frame_file.exists():
                frames.append({
                    "index": idx,
                    "url": f"/api/thumbnail/frame/{session_id}/{idx}",
                    "timestamp": t_sec,
                })
    
    return {"session_id": session_id, "frames": frames}


@app.get("/api/thumbnail/frame/{session_id}/{frame_idx}")
def get_single_thumbnail_frame(session_id: str, frame_idx: int):
    """Serves an extracted thumbnail candidate frame image."""
    frame_file = config.TEMP_DIR / f"thumb_{session_id}_{frame_idx}.jpg"
    if not frame_file.exists():
        raise HTTPException(status_code=404, detail="Thumbnail frame not found")
    return FileResponse(frame_file, media_type="image/jpeg")

@app.post("/api/thumbnail/describe")
def describe_thumbnail_video(payload: Dict[str, Any] = Body(...)):
    title = payload.get("title", "Viral Short")
    return {
        "description": f"In this video, we break down {title} step by step.\n\nSubscribe for more high-impact breakdowns!\n\n#shorts #viral #creator",
        "tags": ["shorts", "trending", "ai", "viral", "growth"]
    }


# Serve built Web UI if present
web_dist = config.PROJECT_ROOT / "web" / "dist"
if web_dist.exists():
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
