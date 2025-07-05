"""
Tests for Smart Swap Mapper overrides.
"""

import importlib

def test_ui_override_present():
    mod = importlib.import_module('facefusion.uis.components.smart_swapper')
    assert 'SmartSwapMapper' in dir(mod)

def test_helper_override_present():
    mod = importlib.import_module('facefusion.face_landmarker')
    assert 'LandmarkMappingHelper' in dir(mod)
