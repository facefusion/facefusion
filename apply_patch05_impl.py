#!/usr/bin/env python3
"""
apply_patch05_impl.py

Implements Patch 05: Live Swap Preview UI by:
  - Overwriting the LiveSwapPreview stub in video_preview.py with full playback & scrubber logic.
  - Appending descriptive entries to patch_log.txt.

Usage:
    python apply_patch05_impl.py --root "C:\\facefusion" [--verbose]
"""

import argparse
import logging
from pathlib import Path

# New implementation for LiveSwapPreview
VIDEO_PREVIEW_IMPL = '''"""
Override for VideoPreview component to embed a live swap preview
with scrub-bar and playback controls.
"""

import threading
from facefusion.uis.components.video_preview import VideoPreview as BasePreview

class LiveSwapPreview(BasePreview):
    """
    Embeds a player that streams swapped frames in real time.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._preview_running = False
        # Slider to scrub through frames
        self.scrub_slider = self.create_slider("Frame", min_value=0, max_value=self.video_manager.total_frames)
        self.scrub_slider.on_change(self.on_slider_move)
        # Play/Pause button
        self.play_button = self.create_button("Play")
        self.play_button.on_click(self.toggle_playback)

    def start_preview(self):
        """
        Begin streaming swapped frames to the UI widget.
        Runs in a background thread to avoid blocking the UI.
        """
        if self._preview_running:
            return
        self._preview_running = True

        def _loop():
            for frame_idx, frame in self.video_manager.run_preview():
                if not self._preview_running:
                    break
                self.update_frame_display(frame)
                # Update slider without triggering event
                self.scrub_slider.set_value(frame_idx, silent=True)

        threading.Thread(target=_loop, daemon=True).start()

    def toggle_playback(self):
        """
        Toggle preview on/off.
        """
        if self._preview_running:
            self._preview_running = False
            self.play_button.set_label("Play")
        else:
            self.play_button.set_label("Pause")
            self.start_preview()

    def on_slider_move(self, frame_index: int):
        """
        Seek to a particular frame in the preview.
        """
        frame = self.video_manager.get_frame(frame_index)
        self.update_frame_display(frame)
"""'''

# Log entries to append to patch_log.txt
LOG_LINES = [
    "- Implemented LiveSwapPreview with scrub-slider and Play/Pause controls.",
    "- Added start_preview() with background thread consuming video_manager.run_preview().",
    "- Implemented toggle_playback() and on_slider_move() for seeking.",
]

def apply_patch(root: Path):
    """
    Overwrite the video_preview override and append to patch_log.txt.
    """
    # Paths relative to project root
    vp_path = root / "enhancements/patches/05-live-swap-preview-ui/facefusion/uis/components/video_preview.py"
    log_path = root / "enhancements/patches/05-live-swap-preview-ui/patch_log.txt"

    # Write the new LiveSwapPreview implementation
    vp_path.parent.mkdir(parents=True, exist_ok=True)
    vp_path.write_text(VIDEO_PREVIEW_IMPL, encoding="utf-8")
    logging.info(f"Wrote LiveSwapPreview implementation to {vp_path}")

    # Append entries to patch_log.txt
    if log_path.exists():
        with log_path.open("a", encoding="utf-8") as f:
            f.write("\n")
            for line in LOG_LINES:
                f.write(line + "\n")
        logging.info(f"Appended entries to {log_path}")
    else:
        logging.error("Could not find patch_log.txt at %s", log_path)

def main():
    parser = argparse.ArgumentParser(
        description="Apply Patch 05 implementation for Live Swap Preview UI"
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
    logging.info("Patch 05 implementation complete.")

if __name__ == "__main__":
    main()
