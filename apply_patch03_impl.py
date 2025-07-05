#!/usr/bin/env python3
"""
apply_patch03_impl.py

Implements Patch 03: Persistent “Favorite Faces” Gallery & Multi-Person Toggle by:
  - Writing working methods into face_store.py and face_selector.py
  - Appending descriptive entries to patch_log.txt

Usage:
    python apply_patch03_impl.py --root "C:\\facefusion" [--verbose]
"""

import argparse
import logging
from pathlib import Path
from datetime import datetime

# Relative file paths and their new contents
FILES = {
    Path("enhancements/patches/03-favorite-faces-gallery/facefusion/face_store.py"): '''\
"""
Override for persistent face store to record usage history and favorites.
"""

from facefusion.face_store import FaceStore
from datetime import datetime


class PersistentFaceStore(FaceStore):
    """
    Extends FaceStore to add usage history and favorite faces.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history_max = 50
        # list of tuples: (face_id, timestamp, thumbnail_path)
        self.history: list[tuple[str, float, str]] = []
        # set of face_ids
        self.favorites: set[str] = set()

    def add_face(self, face_id: str, thumbnail_path: str) -> None:
        """
        Add a face to history with a thumbnail path, evicting oldest if needed.
        New entries are moved to the end; duplicates are removed first.
        """
        # Remove existing entry for this face
        self.history = [entry for entry in self.history if entry[0] != face_id]
        # Append new entry with current timestamp
        now_ts = datetime.now().timestamp()
        self.history.append((face_id, now_ts, thumbnail_path))
        # Evict oldest if exceeding max length
        while len(self.history) > self.history_max:
            self.history.pop(0)

    def pin_favorite(self, face_id: str) -> None:
        """
        Toggle a face in or out of the favorites set.
        """
        if face_id in self.favorites:
            self.favorites.remove(face_id)
        else:
            self.favorites.add(face_id)
''',

    Path("enhancements/patches/03-favorite-faces-gallery/facefusion/uis/components/face_selector.py"): '''\
"""
Override UI FaceSelector to add single/multi selection toggle.
"""

from facefusion.uis.components.face_selector import FaceSelector

class MultiFaceSelector(FaceSelector):
    """
    Adds a mode toggle between single and multi-face selection.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.multi_mode: bool = False  # start in single-face mode

    def toggle_mode(self) -> bool:
        """
        Switch between single and multi selection modes.
        Returns the new mode state.
        """
        self.multi_mode = not self.multi_mode
        # TODO: trigger UI refresh if needed
        return self.multi_mode
''',
}

# Lines to append to patch_log.txt
LOG_LINES = [
    "- Implemented add_face() with duplication removal, timestamping, and eviction in PersistentFaceStore.",
    "- Implemented pin_favorite() toggle in PersistentFaceStore.",
    "- Implemented toggle_mode() in MultiFaceSelector returning new mode state.",
]


def apply_patch(root: Path):
    # 1. Write updated code files
    for rel_path, content in FILES.items():
        file_path = root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logging.info(f"Wrote implementation to {file_path}")

    # 2. Append to patch_log.txt
    log_path = root / "enhancements/patches/03-favorite-faces-gallery/patch_log.txt"
    if not log_path.exists():
        logging.error("Could not find patch_log.txt at %s", log_path)
        return
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write("\n")
        for line in LOG_LINES:
            log_file.write(line + "\n")
    logging.info("Appended entries to %s", log_path)


def main():
    parser = argparse.ArgumentParser(
        description="Apply Patch 03 implementation for Favorite Faces Gallery & Multi-Person Toggle"
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

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    project_root = args.root.resolve()
    if not (project_root / "facefusion").is_dir():
        logging.error("Invalid FaceFusion root: %s", project_root)
        return

    apply_patch(project_root)
    logging.info("Patch 03 implementation complete.")


if __name__ == "__main__":
    main()
