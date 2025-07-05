"""
Tests for Video Region Selection overrides.
"""

import importlib

def test_region_tracker_override():
    mod = importlib.import_module('facefusion.face_masker')
    assert 'RegionTracker' in dir(mod), "RegionTracker should be present"

def test_region_selector_panel_override():
    mod = importlib.import_module('facefusion.uis.components.region_selector')
    assert 'RegionSelectorPanel' in dir(mod), "RegionSelectorPanel should be present"
