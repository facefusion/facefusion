"""
Override common options panel to include device chooser (GPU/CPU)
and auto-throttle threshold.
"""

from facefusion.uis.components.common_options import CommonOptionsPanel as BasePanel
from facefusion.process_manager import ProcessManager

class PerformanceCommonOptionsPanel(BasePanel):
    """
    Adds device dropdown and throttle threshold slider.
    """
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
