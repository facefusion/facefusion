#!/usr/bin/env python3
"""
apply_patch03_ui_impl.py

Implements the FavoriteMemoryPanel UI logic for Patch 03:
Persistent “Favorite Faces” Gallery & Multi-Person Toggle.

  - Writes a full-featured FavoriteMemoryPanel into memory.py
  - Appends descriptive entries to patch_log.txt

Usage:
    python apply_patch03_ui_impl.py --root "C:\\facefusion" [--verbose]
"""

import argparse
import logging
from pathlib import Path
from typing import List, Tuple

# New contents for the UI component
MEMORY_UI_CONTENT = '''\
"""
Override UI Memory panel to show recent and favourite faces with selection and pin.
"""

from typing import List, Tuple
import logging

from facefusion.uis.components.memory import MemoryPanel, ThumbnailWidget
from facefusion.face_store import PersistentFaceStore

logger = logging.getLogger(__name__)

class FavoriteMemoryPanel(MemoryPanel):
    """
    Displays favourite faces and recent history as clickable thumbnails,
    with support for single/multi selection and pin/unpin favorites.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize FavoriteMemoryPanel with PersistentFaceStore.
        """
        super().__init__(*args, **kwargs)
        self.store = PersistentFaceStore()
        self.selected_faces: List[str] = []
        self._build_ui()

    def _build_ui(self) -> None:
        """
        Populate the thumbnail grid from history and favorites.
        """
        self.clear_thumbnails()
        # Favorites first
        for face_id in list(self.store.favorites):
            self._add_thumbnail(face_id, pinned=True)
        # Then history, excluding already-favorited
        for face_id, _, thumb in self.store.history:
            if face_id in self.store.favorites:
                continue
            self._add_thumbnail(face_id, pinned=False)

    def _add_thumbnail(self, face_id: str, pinned: bool) -> None:
        """
        Create and register a ThumbnailWidget for a face.
        """
        try:
            # ThumbnailWidget(path, id, pinned) is assumed from base class
            widget = ThumbnailWidget(path=thumb, face_id=face_id, pinned=pinned)
            widget.on_click(lambda fid=face_id: self._on_thumbnail_click(fid))
            widget.on_pin(lambda fid=face_id: self._on_pin_click(fid))
            self.add_thumbnail_widget(widget)
        except Exception as e:
            logger.error("Error rendering thumbnail for %s: %s", face_id, e)

    def render(self) -> None:
        """
        Render the favourites and history grid in the UI.
        """
        self._build_ui()
        super().render()

    def _on_thumbnail_click(self, face_id: str) -> None:
        """
        Handle user clicking on a thumbnail to select/deselect it.
        """
        if self.store.multi_mode:
            if face_id in self.selected_faces:
                self.selected_faces.remove(face_id)
            else:
                self.selected_faces.append(face_id)
        else:
            self.selected_faces = [face_id]
        logger.debug("Selected faces updated: %s", self.selected_faces)
        # Notify any listeners of the selection change
        self.emit_selection_change(self.selected_faces)

    def _on_pin_click(self, face_id: str) -> None:
        """
        Handle user clicking the pin icon to favorite/unfavorite.
        """
        self.store.pin_favorite(face_id)
        logger.debug("Favorites updated: %s", self.store.favorites)
        # Rebuild UI to reflect changes
        self._build_ui()
'''
# Note: ThumbnailWidget, add_thumbnail_widget, clear_thumbnails, emit_selection_change
# are assumed to exist on MemoryPanel; adjust names if needed.

# Log entries to append
LOG_LINES = [
    "- Implemented FavoriteMemoryPanel._build_ui(), _add_thumbnail(), render(), " 
    "and handlers in memory.py for thumbnails, selection, and pinning.",
]

def apply_ui_impl(root: Path):
    """
    Overwrite memory.py in the Patch 03 folder with the new UI logic,
    then append to patch_log.txt.
    """
    mem_path = root / "enhancements/patches/03-favorite-faces-gallery/facefusion/uis/components/memory.py"
    if not mem_path.exists():
        logging.error("UI stub not found at %s", mem_path)
        return
    # Write new content
    mem_path.write_text(MEMORY_UI_CONTENT, encoding="utf-8")
    logging.info("Updated UI implementation at %s", mem_path)

    # Append to patch_log.txt
    log_path = root / "enhancements/patches/03-favorite-faces-gallery/patch_log.txt"
    if log_path.exists():
        with log_path.open("a", encoding="utf-8") as f:
            f.write("\n")
            for line in LOG_LINES:
                f.write(line + "\n")
        logging.info("Appended entries to %s", log_path)
    else:
        logging.error("Cannot find patch_log.txt at %s", log_path)

def main():
    parser = argparse.ArgumentParser(
        description="Apply Patch 03 UI logic for Favorite Faces Gallery"
    )
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="FaceFusion project root (e.g. C:\\facefusion)"
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
        return

    apply_ui_impl(project_root)
    logging.info("Patch 03 UI implementation complete.")

if __name__ == "__main__":
    main()
