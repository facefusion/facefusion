# Patch 09: Video Region Selection

**Goal:**
Allow drawing arbitrary region polygons (e.g., shirts, hats) on video frames
and persist those masks across the entire frame sequence.

**Touchpoints:**
- Override `facefusion/face_masker.py` with `RegionTracker`.
- Add `RegionSelectorPanel` under `uis/components/region_selector.py`.
- Add tests under `tests/test_region_selection.py`.
