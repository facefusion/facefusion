# Patch 10: Smart Swap Mapper

**Goal:**
Provide an advanced 2D→3D landmark mapping editor that auto-aligns
based on detected geometry, with fine-tune controls.

**Touchpoints:**
- Override `facefusion/uis/components/smart_swapper.py`.
- Extend `facefusion/face_landmarker.py` with a mapping helper.
- Add tests under `tests/test_smart_swap_mapper.py`.
