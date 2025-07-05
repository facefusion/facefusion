"""
Tests for Clothing Selection & Color-Editing UI overrides.
"""

import importlib

def test_region_masker_override_present():
    mod = importlib.import_module('facefusion.face_masker')
    assert 'RegionMasker' in dir(mod), "RegionMasker should be present in face_masker module"

def test_clothing_color_editor_panel_present():
    mod = importlib.import_module('facefusion.uis.components.mask_transformer_options')
    assert 'ClothingColorEditorPanel' in dir(mod), "ClothingColorEditorPanel should be present"
