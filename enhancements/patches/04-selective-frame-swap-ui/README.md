# Patch 04: Selective Frame Swap & Trim UI

**Goal:**
Allow users to select exact frames or time ranges for swapping, 
and preview the trimmed segment in the UI.

**Touchpoints:**
- Override `facefusion/video_manager.py` to accept per-frame indices.
- Extend `facefusion/uis/components/trim_frame.py` to add range sliders and preview button.
- Add tests under `tests/test_selective_frame_swap_ui.py`.
