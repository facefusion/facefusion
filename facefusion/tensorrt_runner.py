"""Thin TensorRT wrapper for face swapper acceleration."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import tensorrt as trt  # type: ignore
    _HAS_TRT = True
except Exception:
    trt = None  # type: ignore
    _HAS_TRT = False

try:
    import cupy as cp  # type: ignore
except Exception:
    cp = None  # type: ignore

LOGGER = trt.Logger(trt.Logger.WARNING) if _HAS_TRT else None
_ENGINE_CACHE: Dict[Tuple[str, Tuple[int, ...], Tuple[int, ...], int], "TensorRTRunner"] = {}
_CACHE_DIR = Path('.caches/trt')
_MAX_BATCH_LIMIT = 64


def is_available() -> bool:
    return _HAS_TRT and cp is not None


def set_max_batch_limit(limit: int) -> None:
    global _MAX_BATCH_LIMIT
    _MAX_BATCH_LIMIT = max(1, int(limit))


def get_max_batch_limit() -> int:
    return _MAX_BATCH_LIMIT


def canonicalize_batch_size(batch: int) -> int:
    if batch <= 0:
        return 1
    size = 1
    while size < batch:
        size <<= 1
    return min(size, _MAX_BATCH_LIMIT)


def get_runner(model_path: str, source_shape: Tuple[int, ...], target_shape: Tuple[int, ...], max_batch: int, enable_fp16: bool = True) -> Optional["TensorRTRunner"]:
    if not is_available():
        return None
    max_batch = canonicalize_batch_size(max_batch)
    key = (model_path, tuple(source_shape[1:]), tuple(target_shape[1:]), max_batch)
    runner = _ENGINE_CACHE.get(key)
    if runner and runner.max_batch >= source_shape[0]:
        return runner
    try:
        engine = _load_or_build_engine(model_path, source_shape, target_shape, max_batch, enable_fp16)
    except Exception:
        return None
    runner = TensorRTRunner(engine, max_batch)
    _ENGINE_CACHE[key] = runner
    return runner


class TensorRTRunner:
    def __init__(self, engine: "trt.ICudaEngine", max_batch: int) -> None:
        self.engine = engine
        self.context = engine.create_execution_context()
        self.binding_names = [self.engine.get_binding_name(i) for i in range(self.engine.num_bindings)]
        self.binding_indices = {name: i for i, name in enumerate(self.binding_names)}
        self.input_indices = [i for i in range(self.engine.num_bindings) if self.engine.binding_is_input(i)]
        self.output_indices = [i for i in range(self.engine.num_bindings) if not self.engine.binding_is_input(i)]
        self.max_batch = max_batch

    def run(self, source_tensor: "cp.ndarray", target_tensor: "cp.ndarray", stream: Optional["cp.cuda.Stream"] = None) -> "cp.ndarray":
        stream = stream or cp.cuda.get_current_stream()
        bindings: list[int] = [0] * self.engine.num_bindings

        # Bind inputs
        for idx in self.input_indices:
            name = self.binding_names[idx]
            if 'source' in name:
                arr = source_tensor
            else:
                arr = target_tensor
            self.context.set_binding_shape(idx, tuple(arr.shape))
            bindings[idx] = arr.data.ptr  # type: ignore[attr-defined]

        # Determine output shapes after input binding
        output_shapes = []
        for idx in self.output_indices:
            out_shape = tuple(self.context.get_binding_shape(idx))
            output_shapes.append(out_shape)

        if not output_shapes:
            raise RuntimeError('TensorRT engine returned no outputs')

        output_shape = output_shapes[0]
        output_tensor = cp.empty(output_shape, dtype=cp.float32)
        bindings[self.output_indices[0]] = output_tensor.data.ptr  # type: ignore[attr-defined]

        self.context.execute_async_v2(bindings, stream.ptr)  # type: ignore[attr-defined]
        stream.synchronize()
        return output_tensor


def _load_or_build_engine(model_path: str, source_shape: Tuple[int, ...], target_shape: Tuple[int, ...], max_batch: int, enable_fp16: bool) -> "trt.ICudaEngine":
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    engine_path = _resolve_engine_path(model_path, max_batch)

    if engine_path.exists():
        runtime = trt.Runtime(LOGGER)
        with engine_path.open('rb') as f:
            engine_bytes = f.read()
        engine = runtime.deserialize_cuda_engine(engine_bytes)
        if engine is not None:
            return engine

    runtime = trt.Runtime(LOGGER)
    with trt.Builder(LOGGER) as builder:
        network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
        parser = trt.OnnxParser(network, LOGGER)

        with open(model_path, 'rb') as model_file:
            if not parser.parse(model_file.read()):
                raise RuntimeError('Failed to parse ONNX for TensorRT')

        config = builder.create_builder_config()
        config.max_workspace_size = 1 << 29  # 512 MB
        if enable_fp16 and builder.platform_has_fast_fp16:
            config.set_flag(trt.BuilderFlag.FP16)

        profile = builder.create_optimization_profile()
        src_min, src_opt, src_max = _profile_bounds(source_shape, max_batch)
        tgt_min, tgt_opt, tgt_max = _profile_bounds(target_shape, max_batch)

        inputs = [network.get_input(i) for i in range(network.num_inputs)]
        source_input = next((inp for inp in inputs if 'source' in inp.name.lower()), inputs[0])
        target_input = next((inp for inp in inputs if 'target' in inp.name.lower()), inputs[min(1, len(inputs) - 1)])

        profile.set_shape(source_input.name, src_min, src_opt, src_max)
        profile.set_shape(target_input.name, tgt_min, tgt_opt, tgt_max)
        config.add_optimization_profile(profile)

        engine = builder.build_engine(network, config)
        if engine is None:
            raise RuntimeError('Failed to build TensorRT engine')

    with engine_path.open('wb') as f:
        f.write(engine.serialize())
    return engine


def _profile_bounds(shape: Tuple[int, ...], max_batch: int) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
    batch = max(1, shape[0])
    min_shape = (1, *shape[1:])
    opt_batch = min(max_batch, max(batch, 4))
    opt_shape = (opt_batch, *shape[1:])
    max_shape = (max_batch, *shape[1:])
    return min_shape, opt_shape, max_shape


def _resolve_engine_path(model_path: str, max_batch: int) -> Path:
    onnx_path = Path(model_path)
    with open(onnx_path, 'rb') as f:
        digest = hashlib.sha1(f.read()).hexdigest()[:12]
    engine_name = f"{onnx_path.stem}_b{max_batch}_{digest}.engine"
    return _CACHE_DIR / engine_name
