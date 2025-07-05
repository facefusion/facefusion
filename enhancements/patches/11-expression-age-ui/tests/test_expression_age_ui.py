"""
Tests for Expression Restorer & Age Modifier UI overrides.
"""

import importlib

def test_expression_panel_override():
    mod = importlib.import_module('facefusion.uis.components.expression_restorer_options')
    assert 'ExpressionRestorerOptionsPanel' in dir(mod)

def test_age_panel_override():
    mod = importlib.import_module('facefusion.uis.components.age_modifier_options')
    assert 'AgeModifierOptionsPanel' in dir(mod)
