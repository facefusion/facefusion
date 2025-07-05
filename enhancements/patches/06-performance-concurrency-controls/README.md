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
