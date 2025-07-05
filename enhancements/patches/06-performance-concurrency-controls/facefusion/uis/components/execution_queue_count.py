"""
Override UI panel to adjust execution queue concurrency.
"""

from facefusion.uis.components.execution_queue_count import ExecutionQueueCountPanel as BasePanel
from facefusion.process_manager import ProcessManager

class PerformanceQueueCountPanel(BasePanel):
    """
    Adds slider for queue size and toggle for multiprocessing.
    """
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
