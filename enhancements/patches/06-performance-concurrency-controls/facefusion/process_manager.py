"""
Override ProcessManager to respect dynamic settings at runtime.
"""

from facefusion.process_manager import ProcessManager as BaseManager

class PerformanceProcessManager(BaseManager):
    """
    Exposes methods to update performance settings on the singleton instance.
    """

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
