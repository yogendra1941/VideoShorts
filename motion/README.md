# VideoShorts Motion (HyperFrames) Overlays

This directory hosts motion-graphics overlays rendered with **HTML + GSAP** and
encoded to transparent **ProRes 4444 MOV** files (with alpha), which are then
composited over the finished 9:16 clips.

This is adapted from the `claude-video-editor` repo's HyperFrames concept.

## Contents

- `render_alpha.py` — the renderer. Converts an HTML/GSAP template into a
  transparent overlay MOV, or falls back to a static title-card RGBA sequence via
  Pillow when Playwright is unavailable.
- `templates/` — (intended) GSAP HTML templates: kinetic title cards, progress
  bars, speaker tags.

## Usage

```python
from motion.render_alpha import MotionOverlayRenderer

r = MotionOverlayRenderer()
ov = r.build_static_overlay("Why scrolling makes life dull", output=out_mov)
r.overlay_onto(base_clip, ov, final_clip)
```

## Notes

- Full GSAP playback requires Playwright + headless Chromium
  (`pip install playwright && playwright install chromium`).
- Without it, the static fallback renders a branded top-banner title card — the
  same visual role as a hook headline, but without animation.
- This is an optional post-processing stage; the core clipping pipeline does not
  depend on it.
