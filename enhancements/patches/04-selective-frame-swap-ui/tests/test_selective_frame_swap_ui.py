"""
Tests for the selective frame swap & trim UI override.
"""

import importlib

def test_trim_frame_panel_override():
    mod = importlib.import_module('facefusion.uis.components.trim_frame')
    assert 'TrimFramePanel' in dir(mod), "TrimFramePanel override should be present"
