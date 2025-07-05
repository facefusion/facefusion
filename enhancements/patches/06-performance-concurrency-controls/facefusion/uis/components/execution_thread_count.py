"""
Override UI panel to adjust execution thread count at runtime.
"""

from facefusion.uis.components.execution_thread_count import ExecutionThreadCountPanel as BasePanel
from facefusion.process_manager import ProcessManager

class PerformanceThreadCountPanel(BasePanel):
    """
    Adds slider and auto-throttle toggle for thread-pool size.
    """
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
