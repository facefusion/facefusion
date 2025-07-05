"""
Tests for the LiveSwapPreview override presence.
"""

import importlib

def test_live_swap_preview_override_present():
    mod = importlib.import_module('facefusion.uis.components.video_preview')
    assert 'LiveSwapPreview' in dir(mod), (
        "LiveSwapPreview class should be present in video_preview module"
    )
