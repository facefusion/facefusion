@echo off
REM Yuz Degistirme Uygulamasi Baslatma Script'i - Windows
REM Face Swap Application Startup Script - Windows

echo ======================================
echo    YUZ DEGISTIRME UYGULAMASI
echo    FACE SWAP APPLICATION
echo ======================================
echo.

REM Python kontrolu
echo Python surumu kontrol ediliyor...
echo Checking Python version...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    echo ERROR: Python not found!
    echo.
    echo Lutfen Python 3.10 veya uzerini yukleyin.
    echo Please install Python 3.10 or higher.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python bulundu: %PYTHON_VERSION%
echo.

REM Bagimliliklari kontrol et
echo Bagimliliklar kontrol ediliyor...
echo Checking dependencies...
echo.

python -c "import gradio" >nul 2>&1
if errorlevel 1 (
    echo Bazi bagimliliklar eksik
    echo Some dependencies are missing
    echo.
    echo Bagimliliklar yukleniyor...
    echo Installing dependencies...
    python -m pip install -r requirements.txt

    if errorlevel 1 (
        echo.
        echo HATA: Bagimliliklar yuklenemedi!
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
    echo Bagimliliklar basariyla yuklendi
    echo Dependencies installed successfully
) else (
    echo Tum bagimliliklar yuklu
    echo All dependencies are installed
)
echo.

REM Gecici klasor olustur
if not exist ".facefusion\temp" mkdir .facefusion\temp

REM Uygulamayi baslat
echo ======================================
echo Uygulama baslatiliyor...
echo Starting application...
echo ======================================
echo.
echo Tarayicinizda su adres acilacak:
echo The following address will open in your browser:
echo.
echo http://localhost:7860
echo.
echo Uygulamayi durdurmak icin Ctrl+C tuslayin.
echo Press Ctrl+C to stop the application.
echo ======================================
echo.

REM Uygulamayi calistir
python face_swap_app.py

REM Cikis mesaji
echo.
echo ======================================
echo Uygulama kapatildi.
echo Application closed.
echo ======================================
pause
