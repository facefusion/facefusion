#!/bin/bash

echo "🚨 緊急性能診断：なぜ0.358秒なのか？"
echo "============================================"

echo ""
echo "1️⃣ 実際に使用されているBLASライブラリ確認..."
pixi run -- python -c "
import numpy as np
print('=== BLAS Library Details ===')
print('NumPy version:', np.__version__)

# 実際に使用されているBLAS確認
config = np.__config__
print('Build info:', config.show())

# より詳細なBLAS情報
try:
    from numpy.distutils.system_info import get_info
    blas_info = get_info('blas')
    print('BLAS info:', blas_info)
except:
    print('Cannot get detailed BLAS info')

# ランタイムでのBLAS確認
try:
    import ctypes
    import ctypes.util
    accelerate_lib = ctypes.util.find_library('Accelerate')
    print('Accelerate framework path:', accelerate_lib)
except:
    print('Cannot check Accelerate framework')
"

echo ""
echo "2️⃣ スレッド数確認..."
pixi run -- python -c "
import numpy as np
import os

print('=== Threading Configuration ===')
print('CPU cores:', os.cpu_count())

# 各種スレッド設定確認
env_vars = ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']
for var in env_vars:
    print(f'{var}: {os.environ.get(var, \"Not set\")}')

# NumPyのスレッド数確認
try:
    from threadpoolctl import threadpool_info
    print('Active threadpools:')
    for info in threadpool_info():
        print(f'  {info}')
except ImportError:
    print('threadpoolctl not available - installing...')
"

echo ""
echo "3️⃣ 詳細GEMM性能テスト（複数サイズ・データ型）..."
pixi run -- python -c "
import numpy as np
import time

print('=== Detailed GEMM Performance Test ===')

# テスト設定
sizes = [1024, 2048, 4096]
dtypes = [np.float32, np.float64]

for dtype in dtypes:
    print(f'\\n--- Data type: {dtype.__name__} ---')
    for size in sizes:
        # メモリ事前割り当て
        A = np.random.rand(size, size).astype(dtype)
        B = np.random.rand(size, size).astype(dtype)
        
        # ウォームアップ
        _ = np.dot(A, B)
        
        # 実測定（3回平均）
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
echo "4️⃣ メモリレイアウト最適化テスト..."
pixi run -- python -c "
import numpy as np
import time

print('=== Memory Layout Optimization Test ===')

size = 4096
A = np.random.rand(size, size).astype(np.float32)

# C-contiguous (row major)
A_c = np.ascontiguousarray(A)
# Fortran-contiguous (column major) 
A_f = np.asfortranarray(A)

print('Array properties:')
print(f'C-contiguous: flags.c_contiguous={A_c.flags.c_contiguous}, flags.f_contiguous={A_c.flags.f_contiguous}')
print(f'F-contiguous: flags.c_contiguous={A_f.flags.c_contiguous}, flags.f_contiguous={A_f.flags.f_contiguous}')

# 性能比較
for name, arr in [('C-contiguous', A_c), ('F-contiguous', A_f)]:
    start = time.perf_counter()
    result = np.dot(arr, arr)
    elapsed = time.perf_counter() - start
    print(f'{name}: {elapsed:.3f}s')
"

echo ""
echo "5️⃣ 環境変数の問題確認..."
pixi run -- python -c "
import os
print('=== Environment Variables Check ===')

# BLAS関連環境変数
blas_vars = {
    'NPY_BLAS_ORDER': os.environ.get('NPY_BLAS_ORDER'),
    'OPENBLAS_NUM_THREADS': os.environ.get('OPENBLAS_NUM_THREADS'),
    'SCIPY_USE_ACCELERATE': os.environ.get('SCIPY_USE_ACCELERATE'),
    'NPY_LAPACK_ORDER': os.environ.get('NPY_LAPACK_ORDER')
}

for var, value in blas_vars.items():
    print(f'{var}: {value}')

# 問題の可能性
print('\\n=== Potential Issues ===')
if os.environ.get('OPENBLAS_NUM_THREADS') == '1':
    print('⚠️  OPENBLAS_NUM_THREADS=1 may limit performance')
if os.environ.get('NPY_BLAS_ORDER') != 'accelerate':
    print('⚠️  NPY_BLAS_ORDER is not set to accelerate')
"
