#!/bin/bash

echo "🔬 詳細ベンチマーク - 正しいpixi構文版"
echo "========================================="

echo "💻 CPU情報確認..."
pixi run -- python -c "
import numpy as np
import time
import os
print(f'CPU Count: {os.cpu_count()}')
print(f'NumPy Version: {np.__version__}')
print('NumPy Configuration:')
print(np.show_config())

# 異なるサイズでテスト
sizes = [1024, 2048, 4096, 8192]
for size in sizes:
    a = np.random.rand(size, size).astype(np.float32)
    start = time.time()
    np.dot(a, a)
    elapsed = time.time() - start
    print(f'Size {size}x{size}: {elapsed:.3f}s')
"

echo ""
echo "🧵 マルチスレッド設定確認..."
pixi run -- python -c "
import numpy as np
print('Threading layer info:')
print(np.show_config())
"

echo ""
echo "💾 メモリ最適化テスト..."
pixi run -- python -c "
import numpy as np
import time

print('=== Memory Layout Test ===')
a_c = np.random.rand(4096, 4096).astype(np.float32)  # C-contiguous
a_f = np.asfortranarray(a_c)  # F-contiguous

start = time.time()
np.dot(a_c, a_c)
c_time = time.time() - start

start = time.time()
np.dot(a_f, a_f)
f_time = time.time() - start

print(f'C-contiguous: {c_time:.3f}s')
print(f'F-contiguous: {f_time:.3f}s')
"

echo ""
echo "🔍 BLAS関連環境変数確認..."
pixi run -- python -c "
import os
print('=== BLAS Environment Variables ===')
for key in sorted(os.environ.keys()):
    if any(term in key.upper() for term in ['BLAS', 'OPENBLAS', 'MKL', 'ACCELERATE']):
        print(f'{key}: {os.environ[key]}')
"
