#!/bin/bash

echo "🚀 FaceFusion M4最適化ベンチマーク開始"
echo "=================================="

# 既存の定義済みベンチマークタスクを実行
echo "📊 NumPy GEMM ベンチマーク..."
pixi run benchmark-numpy

echo ""
echo "🖼️ OpenCV ベンチマーク..."
pixi run benchmark-opencv

echo ""
echo "🧠 Core ML ベンチマーク..."
pixi run benchmark-coreml

echo ""
echo "🔄 全体統合ベンチマーク..."
pixi run benchmark-all

echo ""
echo "🔍 システム情報確認..."
pixi run debug-system

echo ""
echo "📚 ライブラリ詳細確認..."
pixi run debug-libs

echo ""
echo "🎯 環境変数確認..."
pixi run debug-env

echo ""
echo "✅ Accelerate BLAS詳細確認..."
pixi run check-accelerate-detailed
