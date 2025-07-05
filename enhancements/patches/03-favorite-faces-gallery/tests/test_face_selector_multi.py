import importlib

def test_multi_present():
    mod = importlib.import_module("facefusion.uis.components.face_selector")
    assert "MultiFaceSelector" in dir(mod)
