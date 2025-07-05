import importlib

def test_memory_panel():
    mod = importlib.import_module("facefusion.uis.components.memory")
    assert "FavoriteMemoryPanel" in dir(mod)
