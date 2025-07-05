# Patch 08: Clothing Selection & Color-Editing UI

**Goal:**
Allow users to draw and select clothing regions via semantic segmentation overlay
and adjust their color using HSL sliders and presets with real-time preview.

**Touchpoints:**
- Override `facefusion/face_masker.py` to handle arbitrary polygon regions.
- Override `facefusion/uis/components/mask_transformer_options.py` to add segmentation overlay toggle and HSL sliders.
- Add tests under `tests/test_clothing_color_editor.py`.
