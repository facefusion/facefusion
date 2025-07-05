import pytest
from facefusion.face_store import PersistentFaceStore

def test_interface():
    store = PersistentFaceStore()
    assert hasattr(store, "add_face")
    assert hasattr(store, "pin_favorite")
