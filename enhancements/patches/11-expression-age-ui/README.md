# Patch 11: Expression Restorer & Age Modifier UI Improvements

**Goal:**
Add live sliders (smile boost, eyebrow raise) and before/after toggles for
expression restorer and age modifier models with real-time preview.

**Touchpoints:**
- Override `facefusion/uis/components/expression_restorer_options.py`
- Override `facefusion/uis/components/age_modifier_options.py`
- Add tests under `tests/test_expression_age_ui.py`
