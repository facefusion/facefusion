"""
Tests for Model & Metadata Viewer Enhancements overrides.
"""

import importlib

def test_model_viewer_override():
    mod = importlib.import_module('facefusion.uis.components.model_viewer')
    assert 'EnhancedModelViewerPanel' in dir(mod)

def test_metadata_viewer_override():
    mod = importlib.import_module('facefusion.uis.components.metadata_viewer')
    assert 'EnhancedMetadataViewerPanel' in dir(mod)

def test_model_helper_override():
    mod = importlib.import_module('facefusion.model_helper')
    assert 'EnhancedModelHelper' in dir(mod)
