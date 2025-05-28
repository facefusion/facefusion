#!/bin/bash

echo "🍺 Brew Install による Accelerate BLAS 最適化"
echo "============================================="

echo "📝 現在の問題："
echo "- 0.358秒は異常に遅い（期待値: 0.1-0.2秒）"
echo "- CondaのNumPy/SciPyがAccelerateを正しく使用していない可能性"
echo ""

echo "💡 解決策："
echo "1. Homebrewでシステム全体のBLAS最適化"
echo "2. または、Accelerate強制ビルドのNumPy"
echo ""

echo "🔧 オプション1: システム全体最適化"
echo "brew install openblas"
echo "brew install numpy --with-openblas"
echo "brew install scipy --with-openblas"
echo ""

echo "🔧 オプション2: Accelerate強制"
echo "# macOSのAccelerateフレームワークを強制使用"
echo "export CPPFLAGS='-I/System/Library/Frameworks/Accelerate.framework/Versions/A/Frameworks/vecLib.framework/Versions/A/Headers'"
echo "export LDFLAGS='-L/System/Library/Frameworks/Accelerate.framework/Versions/A/Frameworks/vecLib.framework/Versions/A'"
echo "pip install --no-binary numpy,scipy --force-reinstall numpy scipy"
echo ""

echo "🔧 オプション3: conda-forge最適化版"
echo "conda install -c conda-forge 'blas=*=accelerate' numpy scipy"
echo ""

echo "実行するには以下のコマンドを選択："
echo "chmod +x brew_optimization.sh"
echo "./brew_optimization.sh [1|2|3]"
