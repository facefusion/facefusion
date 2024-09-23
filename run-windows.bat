@echo off
call conda activate facefusion

:menu
cls
echo =========================================
echo            FaceFusion Menu
echo =========================================
echo.
echo Please choose an option:
echo 1. Run FaceFusion (Normal Mode)
echo 2. Run FaceFusion (Webcam Mode)
echo 3. Exit
echo.
set /p choice=Enter your choice (1-3): 

if %choice%==1 (
    python facefusion.py run
) else if %choice%==2 (
    python facefusion.py run --ui-layouts webcam
) else if %choice%==3 (
    echo Exiting...
    exit /b
) else (
    echo Invalid choice. Please try again.
    pause
    goto menu
)

pause
