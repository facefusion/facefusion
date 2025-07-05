# Patch 07: Model & Metadata Viewer Enhancements

**Goal:**
Provide UI panels to inspect ML model graphs, layers, input/output shapes,
and to view file-embedded metadata side-by-side.

**Touchpoints:**
- Override `facefusion/uis/components/model_viewer.py`
- Override `facefusion/uis/components/metadata_viewer.py`
- Override `facefusion/model_helper.py`
- Add tests under `tests/test_model_metadata_viewer.py`
