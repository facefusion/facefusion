#!/usr/bin/env python3
"""
apply_patch02_impl.py

Implements Patch 02: Batch Swap Mapping UI override by:
  - Writing the full `BatchSwapMapper` class into swap_mapper.py
  - Creating the logic tests in test_batch_mapping_logic.py
  - Appending entries to patch_log.txt

Usage:
    python apply_patch02_impl.py --root "C:\\facefusion"
"""

import argparse
import logging
from pathlib import Path
from typing import Dict


# File paths (relative to project root) and their contents
FILES: Dict[Path, str] = {
    Path("enhancements/patches/02-batch-swap-mapping-ui/facefusion/uis/components/swap_mapper.py"): """\
\"\"\"
Batch Swap Mapping UI override.

Enhances the original SwapMapper to support bulk mapping of multiple
source and target face files.
\"\"\"

import json
import csv
from pathlib import Path
from facefusion.uis.components.swap_mapper import SwapMapper

class BatchSwapMapper(SwapMapper):
    \"\"\"
    Extended SwapMapper supporting batch source→target assignment.
    \"\"\"
    def __init__(self, *args, **kwargs):
        \"\"\"
        Initialize the batch mapper, preserving the original SwapMapper behavior.
        \"\"\"
        super().__init__(*args, **kwargs)
        self.mappings: list[tuple[str, str]] = []

    def load_mappings(self, mapping_file: str) -> None:
        \"\"\"
        Load source→target mappings from a JSON or CSV file.

        Args:
            mapping_file: Path to a .json (list of [src, tgt]) or .csv (src,tgt per row).
        \"\"\"
        path = Path(mapping_file)
        suffix = path.suffix.lower()
        if suffix == ".json":
            self.mappings = [
                (str(src), str(tgt))
                for src, tgt in json.loads(path.read_text(encoding="utf-8"))
            ]
        elif suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                self.mappings = [(row[0], row[1]) for row in reader]
        else:
            raise ValueError(f"Unsupported mapping file type: {path.suffix}")

    def get_mappings(self) -> list[tuple[str, str]]:
        \"\"\"
        Return the list of loaded source→target mappings.
        \"\"\"
        return self.mappings
""",
    Path("enhancements/patches/02-batch-swap-mapping-ui/tests/test_batch_mapping_logic.py"): """\
\"\"\"
Tests for the BatchSwapMapper mapping-load logic.
\"\"\"

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
""",
}

# Lines to append to patch_log.txt
LOG_LINES = [
    "- Implemented load_mappings() and get_mappings() methods in BatchSwapMapper.",
    "- Added JSON/CSV parsing and error handling.",
    "- Created test_batch_mapping_logic.py for positive and negative cases.",
]


def main(root: Path) -> None:
    """
    Create or overwrite the implementation files and append to patch_log.txt.
    """
    # 1. Write each implementation file
    for rel_path, content in FILES.items():
        file_path = root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logging.info("Wrote %s", file_path)

    # 2. Append to patch_log.txt
    log_path = root / "enhancements/patches/02-batch-swap-mapping-ui/patch_log.txt"
    if not log_path.exists():
        logging.error("patch_log.txt not found at %s", log_path)
        return
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write("\n")
        for line in LOG_LINES:
            log_file.write(line + "\n")
    logging.info("Appended patch_log.txt entries")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply Patch 02 implementation for Batch Swap Mapping UI"
    )
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Path to FaceFusion project root (e.g., C:\\facefusion)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    project_root = args.root.resolve()
    if not (project_root / "facefusion").is_dir():
        logging.error("Invalid FaceFusion root: %s", project_root)
        exit(1)

    main(project_root)
