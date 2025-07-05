#!/usr/bin/env python3
"""
apply_patch06_full.py

Scaffolds and implements Patch 06: Performance & Concurrency Controls.

This single script will:
  1. Create the patch directory and README.
  2. Write override implementations for:
     - ExecutionThreadCountPanel
     - ExecutionQueueCountPanel
     - CommonOptionsPanel
     - ProcessManager
  3. Create the pytest suite.
  4. Append descriptive entries to patch_log.txt.

Usage:
    python apply_patch06_full.py --root "C:\\facefusion" [--verbose]
"""

import argparse
import logging
from pathlib import Path
import textwrap

# Files to scaffold and their complete contents
FILES = {
    # README
    "enhancements/patches/06-performance-concurrency-controls/README.md": textwrap.dedent("""\
        # Patch 06: Performance & Concurrency Controls

        **Goal:**
        Expose thread-pool size, multi-process toggle, GPU/CPU device chooser,
        and auto-throttling settings in both the UI and core pipeline.

        **Touchpoints:**
        - Override `facefusion/uis/components/execution_thread_count.py`
        - Override `facefusion/uis/components/execution_queue_count.py`
        - Override `facefusion/uis/components/common_options.py`
        - Override `facefusion/process_manager.py`
        - Add tests under `tests/test_performance_controls.py`
    """),

    # Initial patch log stub
    "enhancements/patches/06-performance-concurrency-controls/patch_log.txt": textwrap.dedent("""\
        Patch 06:
        - Scaffolded Performance & Concurrency Controls patch directory.
        - Wrote override implementations for execution_thread_count, execution_queue_count, common_options, and process_manager.
        - Added tests for override modules.
    """),

    # UI override: ExecutionThreadCountPanel
    "enhancements/patches/06-performance-concurrency-controls/facefusion/uis/components/execution_thread_count.py": textwrap.dedent("""\
        \"\"\"
        Override UI panel to adjust execution thread count at runtime.
        \"\"\"

        from facefusion.uis.components.execution_thread_count import ExecutionThreadCountPanel as BasePanel
        from facefusion.process_manager import ProcessManager

        class PerformanceThreadCountPanel(BasePanel):
            \"\"\"
            Adds slider and auto-throttle toggle for thread-pool size.
            \"\"\"
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.thread_slider = self.create_slider(
                    "Threads",
                    min_value=1,
                    max_value=ProcessManager.max_threads(),
                    default=ProcessManager.thread_count()
                )
                self.thread_slider.on_change(self._on_thread_change)

                self.auto_toggle = self.create_toggle(
                    "Auto-Throttle", 
                    default=ProcessManager.auto_throttle_enabled()
                )
                self.auto_toggle.on_change(self._on_auto_toggle)

            def _on_thread_change(self, value: int) -> None:
                ProcessManager.set_thread_count(value)

            def _on_auto_toggle(self, enabled: bool) -> None:
                ProcessManager.enable_auto_throttle(enabled)
    """),

    # UI override: ExecutionQueueCountPanel
    "enhancements/patches/06-performance-concurrency-controls/facefusion/uis/components/execution_queue_count.py": textwrap.dedent("""\
        \"\"\"
        Override UI panel to adjust execution queue concurrency.
        \"\"\"

        from facefusion.uis.components.execution_queue_count import ExecutionQueueCountPanel as BasePanel
        from facefusion.process_manager import ProcessManager

        class PerformanceQueueCountPanel(BasePanel):
            \"\"\"
            Adds slider for queue size and toggle for multiprocessing.
            \"\"\"
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.queue_slider = self.create_slider(
                    "Queue Size",
                    min_value=1,
                    max_value=ProcessManager.max_queue(),
                    default=ProcessManager.queue_size()
                )
                self.queue_slider.on_change(self._on_queue_change)

                self.mp_toggle = self.create_toggle(
                    "Multiprocessing",
                    default=ProcessManager.is_multiprocessing_enabled()
                )
                self.mp_toggle.on_change(self._on_mp_toggle)

            def _on_queue_change(self, value: int) -> None:
                ProcessManager.set_queue_size(value)

            def _on_mp_toggle(self, enabled: bool) -> None:
                ProcessManager.enable_multiprocessing(enabled)
    """),

    # UI override: CommonOptionsPanel
    "enhancements/patches/06-performance-concurrency-controls/facefusion/uis/components/common_options.py": textwrap.dedent("""\
        \"\"\"
        Override common options panel to include device chooser (GPU/CPU)
        and auto-throttle threshold.
        \"\"\"

        from facefusion.uis.components.common_options import CommonOptionsPanel as BasePanel
        from facefusion.process_manager import ProcessManager

        class PerformanceCommonOptionsPanel(BasePanel):
            \"\"\"
            Adds device dropdown and throttle threshold slider.
            \"\"\"
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.device_dropdown = self.create_dropdown(
                    "Device", 
                    options=["GPU", "CPU"], 
                    default=ProcessManager.default_device()
                )
                self.device_dropdown.on_change(self._on_device_change)

                self.throttle_slider = self.create_slider(
                    "Auto-Throttle Threshold",
                    min_value=0,
                    max_value=100,
                    default=ProcessManager.auto_throttle_threshold()
                )
                self.throttle_slider.on_change(self._on_threshold_change)

            def _on_device_change(self, device: str) -> None:
                ProcessManager.set_device(device)

            def _on_threshold_change(self, value: int) -> None:
                ProcessManager.set_auto_throttle_threshold(value)
    """),

    # Core override: ProcessManager
    "enhancements/patches/06-performance-concurrency-controls/facefusion/process_manager.py": textwrap.dedent("""\
        \"\"\"
        Override ProcessManager to respect dynamic settings at runtime.
        \"\"\"

        from facefusion.process_manager import ProcessManager as BaseManager

        class PerformanceProcessManager(BaseManager):
            \"\"\"
            Exposes methods to update performance settings on the singleton instance.
            \"\"\"

            @classmethod
            def set_thread_count(cls, count: int) -> None:
                cls._instance.thread_count = count

            @classmethod
            def enable_auto_throttle(cls, enabled: bool) -> None:
                cls._instance.auto_throttle = enabled

            @classmethod
            def set_queue_size(cls, size: int) -> None:
                cls._instance.queue_size = size

            @classmethod
            def enable_multiprocessing(cls, enabled: bool) -> None:
                cls._instance.use_multiprocessing = enabled

            @classmethod
            def set_device(cls, device: str) -> None:
                cls._instance.device = device

            @classmethod
            def auto_throttle_threshold(cls) -> int:
                return cls._instance.auto_throttle_threshold
    """),

    # Test suite
    "enhancements/patches/06-performance-concurrency-controls/tests/test_performance_controls.py": textwrap.dedent("""\
        \"\"\"
        Tests for Performance & Concurrency Controls override modules.
        \"\"\"

        import importlib

        def test_execution_thread_count_override():
            mod = importlib.import_module('facefusion.uis.components.execution_thread_count')
            assert 'PerformanceThreadCountPanel' in dir(mod)

        def test_execution_queue_count_override():
            mod = importlib.import_module('facefusion.uis.components.execution_queue_count')
            assert 'PerformanceQueueCountPanel' in dir(mod)

        def test_common_options_override():
            mod = importlib.import_module('facefusion.uis.components.common_options')
            assert 'PerformanceCommonOptionsPanel' in dir(mod)

        def test_process_manager_override():
            mod = importlib.import_module('facefusion.process_manager')
            assert 'PerformanceProcessManager' in dir(mod)
    """),
}

# No need to append extra lines: our full patch_log.txt already includes both scaffold and impl entries.


def apply_patch(root: Path):
    """Create all files and directories for Patch 06."""
    for rel, content in FILES.items():
        path = root / Path(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logging.info("Wrote %s", path)


def main():
    parser = argparse.ArgumentParser(
        description="Apply Patch 06 full scaffold and implementation."
    )
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Path to FaceFusion project root, e.g., C:\\facefusion"
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

    apply_patch(project_root)
    logging.info("Patch 06 full implementation complete.")


if __name__ == "__main__":
    main()
