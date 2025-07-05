"""
Tests for the BatchSwapMapper mapping-load logic.
"""

import json
import csv
import pytest
from pathlib import Path
from facefusion.uis.components.swap_mapper import BatchSwapMapper

@pytest.mark.parametrize("data, ext", [
    ([["a.png", "b.png"], ["c.jpg", "d.jpg"]], ".json"),
    ([["x.png", "y.png"], ["u.jpg", "v.jpg"]], ".csv"),
])
def test_load_and_get_mappings(tmp_path, data, ext):
    # Create a mapping file (JSON or CSV)
    file_path = tmp_path / f"mappings{ext}"
    if ext == ".json":
        file_path.write_text(json.dumps(data), encoding="utf-8")
    else:
        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)

    mapper = BatchSwapMapper()
    mapper.load_mappings(str(file_path))
    assert mapper.get_mappings() == [(src, tgt) for src, tgt in data]

def test_load_invalid_extension(tmp_path):
    bad_file = tmp_path / "mappings.txt"
    bad_file.write_text("not valid", encoding="utf-8")
    mapper = BatchSwapMapper()
    with pytest.raises(ValueError):
        mapper.load_mappings(str(bad_file))
