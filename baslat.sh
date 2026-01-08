#!/bin/bash

# Yüz Değiştirme Uygulaması Başlatma Script'i
# Face Swap Application Startup Script

echo "======================================"
echo "   YÜZ DEĞİŞTİRME UYGULAMASI"
echo "   FACE SWAP APPLICATION"
echo "======================================"
echo ""

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python kontrolü
echo "Python sürümü kontrol ediliyor..."
echo "Checking Python version..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}HATA: Python bulunamadı!${NC}"
    echo -e "${RED}ERROR: Python not found!${NC}"
    echo ""
    echo "Lütfen Python 3.10 veya üzerini yükleyin."
    echo "Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python bulundu: $PYTHON_VERSION${NC}"
echo ""

# Bağımlılık kontrolü
echo "Bağımlılıklar kontrol ediliyor..."
echo "Checking dependencies..."

if $PYTHON_CMD -c "import gradio" &> /dev/null; then
    echo -e "${GREEN}✓ Tüm bağımlılıklar yüklü${NC}"
else
    echo -e "${YELLOW}⚠ Bazı bağımlılıklar eksik${NC}"
    echo ""
    echo "Bağımlılıklar yükleniyor..."
    echo "Installing dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt

    if [ $? -ne 0 ]; then
        echo -e "${RED}HATA: Bağımlılıklar yüklenemedi!${NC}"
        echo -e "${RED}ERROR: Failed to install dependencies!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Bağımlılıklar başarıyla yüklendi${NC}"
fi
echo ""

# Geçici klasör oluştur
mkdir -p .facefusion/temp

# Uygulamayı başlat
echo "======================================"
echo "Uygulama başlatılıyor..."
echo "Starting application..."
echo "======================================"
echo ""
echo -e "${GREEN}Tarayıcınızda şu adres açılacak:${NC}"
echo -e "${GREEN}The following address will open in your browser:${NC}"
echo ""
echo -e "${YELLOW}http://localhost:7860${NC}"
echo ""
echo "Uygulamayı durdurmak için Ctrl+C tuşlayın."
echo "Press Ctrl+C to stop the application."
echo "======================================"
echo ""

# Uygulamayı çalıştır
$PYTHON_CMD face_swap_app.py

# Çıkış mesajı
echo ""
echo "======================================"
echo "Uygulama kapatıldı."
echo "Application closed."
echo "======================================"
