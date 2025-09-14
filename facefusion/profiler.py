import threading
from typing import Dict

from facefusion import logger

_LOCK = threading.Lock()
_METRICS: Dict[str, float] = {
    'frames': 0.0,
    'detector_ms': 0.0,
    'landmarker_ms': 0.0,
    'recognizer_ms': 0.0,
    'classifier_ms': 0.0,
    'swapper_onnx_ms': 0.0,
    'swapper_paste_ms': 0.0,
    'swapper_seq_ms': 0.0,
}

def add(name: str, ms: float) -> None:
    with _LOCK:
        _METRICS[name] = _METRICS.get(name, 0.0) + float(ms)

def inc_frames(n: int = 1) -> None:
    add('frames', float(n))

def get_and_reset() -> Dict[str, float]:
    with _LOCK:
        snapshot = dict(_METRICS)
        for k in _METRICS.keys():
            _METRICS[k] = 0.0
        return snapshot

def log_summary(context: str = 'job') -> None:
    m = get_and_reset()
    frames = max(1.0, m.get('frames', 0.0))
    def pf(key: str) -> float:
        return m.get(key, 0.0)
    logger.info(
        f"[profiler] context={context} frames={int(frames)} "
        f"detector_total_ms={pf('detector_ms'):.1f} per_frame={pf('detector_ms')/frames:.2f} "
        f"landmarker_total_ms={pf('landmarker_ms'):.1f} per_frame={pf('landmarker_ms')/frames:.2f} "
        f"recognizer_total_ms={pf('recognizer_ms'):.1f} per_frame={pf('recognizer_ms')/frames:.2f} "
        f"classifier_total_ms={pf('classifier_ms'):.1f} per_frame={pf('classifier_ms')/frames:.2f} "
        f"swapper_onnx_total_ms={pf('swapper_onnx_ms'):.1f} per_frame={pf('swapper_onnx_ms')/frames:.2f} "
        f"swapper_paste_total_ms={pf('swapper_paste_ms'):.1f} per_frame={pf('swapper_paste_ms')/frames:.2f} "
        f"swapper_seq_total_ms={pf('swapper_seq_ms'):.1f} per_frame={pf('swapper_seq_ms')/frames:.2f}",
        __name__
    )

