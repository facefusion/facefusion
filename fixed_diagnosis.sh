#!/bin/bash

echo "🚨 緊急性能診断：なぜ0.358秒なのか？"
echo "============================================"

echo ""
echo "1️⃣ 実際に使用されているBLASライブラリ確認..."
pixi run -- python3 -c "
import numpy as np
print('=== BLAS Library Details ===')
print('NumPy version:', np.__version__)
print('Build info:')
print(np.__config__.show())
"

echo ""
echo "2️⃣ スレッド数確認..."
pixi run -- python3 -c "
import numpy as np
import os
print('=== Threading Configuration ===')
print('CPU cores:', os.cpu_count())
env_vars = ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']
for var in env_vars:
    value = os.environ.get(var, 'Not set')
    print(f'{var}: {value}')
"

echo ""
echo "3️⃣ 詳細GEMM性能テスト..."
pixi run -- python3 -c "
import numpy as np
import time
print('=== Detailed GEMM Performance Test ===')
sizes = [1024, 2048, 4096]
dtypes = [np.float32, np.float64]
for dtype in dtypes:
    print(f'--- Data type: {dtype.__name__} ---')
    for size in sizes:
        A = np.random.rand(size, size).astype(dtype)
        B = np.random.rand(size, size).astype(dtype)
        _ = np.dot(A, B)  # warmup
        times = []
        for _ in range(3):
            start = time.perf_counter()
            C = np.dot(A, B)
            end = time.perf_counter()
            times.append(end - start)
        avg_time = np.mean(times)
        gflops = (2 * size**3) / (avg_time * 1e9)
        print(f'Size {size}x{size}: {avg_time:.3f}s ({gflops:.1f} GFLOPS)')
"

echo ""
echo "4️⃣ 環境変数の問題確認..."
pixi run -- python3 -c "
import os
print('=== Environment Variables Check ===')
blas_vars = {
    'NPY_BLAS_ORDER': os.environ.get('NPY_BLAS_ORDER'),
    'OPENBLAS_NUM_THREADS': os.environ.get('OPENBLAS_NUM_THREADS'),
    'SCIPY_USE_ACCELERATE': os.environ.get('SCIPY_USE_ACCELERATE'),
    'NPY_LAPACK_ORDER': os.environ.get('NPY_LAPACK_ORDER')
}
for var, value in blas_vars.items():
    print(f'{var}: {value}')
print('=== Potential Issues ===')
if os.environ.get('OPENBLAS_NUM_THREADS') == '1':
    print('⚠️  OPENBLAS_NUM_THREADS=1 may limit performance')
if os.environ.get('NPY_BLAS_ORDER') != 'accelerate':
    print('⚠️  NPY_BLAS_ORDER is not set to accelerate')
"

echo ""
echo "5️⃣ 実際のBLASライブラリ動的確認..."
pixi run -- python3 -c "
import subprocess
import sys
try:
    result = subprocess.run([sys.executable, '-c', 'import numpy; numpy.show_config()'], 
                          capture_output=True, text=True)
    print('NumPy config output:', result.stdout)
except Exception as e:
    print('Error checking config:', e)
"
