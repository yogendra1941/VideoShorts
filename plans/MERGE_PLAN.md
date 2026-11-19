# VideoShorts — Full Reference Repo Merge Blueprint

**Goal:** Physically merge the useful code from all 5 reference repos into the standalone `VideoShorts` repo, adapt features to the unified architecture, and deliver a complete frontend + backend web studio with a proper product identity.

**Source repos (read-only references):**
- `reference_repos/studio_reference` — layout reframing, dashboards, hooks, caption styles, editor
- `reference_repos/ClipKaro` — deep clips, critic, honesty, brand/music/sound modules
- `reference_repos/claude-video-editor` — HyperFrames GSAP motion overlays, skill-based flow
- `reference_repos/AI-Youtube-Shorts-Generator` — CLI, virality scoring, overlap dedup, output JSON
- `reference_repos/ai-clipping-comfyui` — ComfyUI node bridge (optional; strip MuAPI cloud calls)

**Target repo:** `VideoShorts/` (existing). Do NOT copy wholesale — adapt features into the unified `core/` + `api/` + `web/` structure.

---

## 1. Repository Layout After Merge

```
VideoShorts/
├── core/                    # backend Python pipeline (unified)
│   ├── ingest.py            # yt-dlp + ffmpeg + scene cuts (studio_reference/ClipKaro adaptive scene detect)
│   ├── transcribe.py        # faster-whisper GPU + CPU fallback
│   ├── trim.py              # filler/pause trimming
│   ├── scoring.py           # virality framework + NMS dedup
│   ├── deep.py              # deep clips multi-stage
│   ├── critic.py            # 3-pass blind critic
│   ├── layout_picker.py     # layout classification
│   ├── reframer.py          # MediaPipe face tracking + EMA smoothing
│   ├── subtitles.py         # ASS karaoke captions
│   ├── renderer.py          # NVENC + loudnorm render
│   ├── hooks.py             # [NEW] hook/title headline generation (studio_reference hooks.py)
│   ├── translate.py         # [NEW] translation backend (studio_reference translate.py)
│   ├── sound.py             # [NEW] audio analysis: laughter/applause/silence (ClipKaro sound.py)
│   ├── honesty.py           # [NEW] deep-clip honesty gate (ClipKaro honesty.py)
│   ├── music.py             # [NEW] background music ducking (ClipKaro music.py)
│   ├── brand.py             # [NEW] brand kit styles (ClipKaro brand.py / brandkit.py)
│   ├── social.py            # [NEW] social platform titles/descriptions (studio_reference social_platforms.py)
│   ├── llm.py              # unified LLM client (Inception/Ollama/Gemini/OpenAI)
│   └── __init__.py
├── api/
│   └── server.py            # FastAPI backend (extend with new endpoints)
├── web/                     # React + Vite + Remotion frontend
│   ├── src/
│   │   ├── components/      # add: HookModal, TranslateModal, SubtitleModal, MusicModal,
│   │   │                   #       BrandKitPanel, SocialPostCard (port from studio_reference)
│   │   ├── lib/             # port: api.js, jobPoll.js, renderInBrowser.js
│   │   └── remotion/        # port: Subtitles.tsx, HookOverlay.tsx, VideoEffects.tsx
│   └── package.json
├── motion/                  # [NEW] HyperFrames GSAP overlays (claude-video-editor)
│   ├── templates/
│   ├── render_alpha.py      # render HTML+GSAP -> ProRes 4444 MOV w/ alpha
│   └── README.md
├── comfyui/                 # [OPTIONAL] ComfyUI node bridge (ai-clipping-comfyui)
│   └── nodes/videoshorts_nodes.py
├── output/                  # rendered shorts
├── plans/
└── main.py                  # CLI coordinator
```

---

## 2. Feature Adaptation Mapping

| Feature | Source | Target | Adaptation action |
|---|---|---|---|
| Adaptive scene-cut detection (dark footage fix) | ClipKaro `reframe.py` `scene_cuts()` | `core/ingest.py` | Replace scenedetect call with adaptive threshold logic |
| Hook/title headline generation | studio_reference `hooks.py`, `verify_hooks.py` | `core/hooks.py` | New module; add to pipeline before render |
| Translation | studio_reference `translate.py` | `core/translate.py` | Add `--translate <lang>` CLI + API param |
| Audio markers (laughter/applause/silence) | ClipKaro `sound.py` | `core/sound.py` | Feed into critic context + trim decisions |
| Honesty gate (deep clips) | ClipKaro `honesty.py` | `core/honesty.py` | Wire inside `deep.py` composer |
| Background music / ducking | ClipKaro `music.py` | `core/music.py` | Optional render stage (scene via config) |
| Brand kit / style presets | ClipKaro `brand.py`, `brandkit.py` | `core/brand.py` | Config-driven subtitle/caption/overlay styles |
| Social platform titles/descriptions | studio_reference `social_platforms.py` | `core/social.py` | Generate per-platform copy at render |
| Subtitle style presets | studio_reference `captions.py`/`burned_subtitles.py` | `core/subtitles.py` | Extend with style presets |
| HyperFrames GSAP overlays | claude-video-editor `skills/hyperframes` | `motion/` | Port templates + alpha render script |
| ComfyUI node bridge | ai-clipping-comfyui | `comfyui/` | Wrap `core/` pipeline as custom nodes (strip MuAPI) |
| Web editor components | studio_reference `dashboard/src/components` | `web/src/components` | Port HookModal, TranslateModal, SubtitleModal, BrandKitPanel, SocialPostCard |
| Browser rendering | studio_reference `lib/renderInBrowser.js` | `web/src/lib/` | Optional client-side render preview |

---

## 3. Web UI / Branding Work

1. **Product identity:** Name = **VideoShorts**. Set in:
   - `web/index.html` — `<title>VideoShorts</title>`, meta tags, favicon
   - `web/src/config.js` — brand name/logo/colors
   - Localapi/server.py` — API title/version
2. **Branding tokens:** define colors/font/logo (distinct from reference repos).
3. **Pages already present:** Landing, Legal, dashboard. Add: upload flow, job progress, clip cards, editor, settings/brand panel.
4. **Backend endpoints to add:** `POST /api/jobs` (exists), add `POST /api/translate`, `POST /api/render-layout`, `GET /api/brand`, `POST /api/social-copy`.

---

## 4. Execution Checklist (Code mode)

1. [ ] Copy adaptive scene-detection into `core/ingest.py`.
2. [ ] Create `core/hooks.py`, `core/translate.py`, `core/sound.py`, `core/honesty.py`, `core/music.py`, `core/brand.py`, `core/social.py` and wire into pipeline.
3. [ ] Extend `core/subtitles.py` with style presets.
4. [ ] Port HyperFrames templates + alpha renderer into `motion/`.
5. [ ] Build optional `comfyui/` node bridge.
6. [ ] Extend `api/server.py` with new endpoints + static serving.
7. [ ] Port new web components + branding into `web/`.
8. [ ] Rebuild `web/dist`; run end-to-end test.
9. [ ] Update `README.md` + commit.

---

## 5. Verification

- `python main.py <url> --clips 3` still produces output MP4s.
- `python -m uvicorn api.server:app --port 8000` serves rebranded UI.
- New features (hooks, brand presets, translation) appear in CLI flags and web editor.
