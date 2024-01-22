@echo off
setlocal enabledelayedexpansion

:: Define Python version
set "PYTHON_VERSION=3.10.11"

:: Default Python location
set "PYTHON_DIR="

:: Find Python 3.10 location
for %%d in ("%LOCALAPPDATA%\Programs\Python\Python310" "C:\ProgramData\Python310") do (
    if exist "%%~d\python.exe" (
        set "PYTHON_DIR=%%~d"
        goto FoundPython
    )
)

:: If Python is not found, download and extract it
if not defined PYTHON_DIR (
    echo Python 3.10 not found. Attempting to download...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip' -OutFile 'python-%PYTHON_VERSION%-embed-amd64.zip'"
    echo Extracting Python...
    powershell -Command "Expand-Archive -LiteralPath 'python-%PYTHON_VERSION%-embed-amd64.zip' -DestinationPath '.\py'"
    set "PYTHON_DIR=%CD%\py"
    set "PYTHONEXE=%PYTHON_DIR%\python.exe"
) else (
    set "PYTHONEXE=%PYTHON_DIR%\python.exe"
)

:FoundPython
:: Create virtual environment using located or downloaded Python
echo Creating a virtual environment...
"%PYTHONEXE%" -m venv "%PYTHON_DIR%\venv"

:: Activate virtual environment
call "%PYTHON_DIR%\venv\Scripts\activate.bat"

:: Install your python package with desired options
"%PYTHON_DIR%\python.exe" install.py --torch cuda --onnxruntime cuda

:: Run
"%PYTHON_DIR%\python.exe" run.py --torch cuda --onnxruntime cuda

:: Deactivate virtual environment
:: call "%PYTHON_DIR%\venv\Scripts\deactivate.bat"

echo Script completed.
