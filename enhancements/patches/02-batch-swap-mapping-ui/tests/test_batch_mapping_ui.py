"""
Tests for BatchSwapMapper override.
"""

import importlib

def test_override_present():
    mod = importlib.import_module("facefusion.uis.components.swap_mapper")
    assert "BatchSwapMapper" in dir(mod)
