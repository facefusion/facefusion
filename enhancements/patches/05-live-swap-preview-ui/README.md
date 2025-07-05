# Patch 05: Live Swap Preview UI

**Goal:**
Embed a real-time video player with a scrub bar that shows the face-swap
result live as users adjust options.

**Touchpoints:**
- Override `facefusion/uis/components/video_preview.py` to implement
  a continuous playback widget that pulls frames from the swap pipeline.
- Optionally extend `facefusion/video_manager.py` with a `run_preview()`
  method to feed frames to the UI.
- Add tests under `tests/test_live_swap_preview_ui.py`.
