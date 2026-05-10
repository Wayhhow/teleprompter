@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Teleprompter Build Script
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

:: Clean old build artifacts
echo [INFO] Cleaning old build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: Install PyInstaller and dependencies
echo [INFO] Installing PyInstaller and dependencies...
pip install pyinstaller
pip install -r requirements.txt

echo.
echo [INFO] Starting build...

:: Build (use python -m to avoid PATH issues)
python -m PyInstaller --noconsole --onedir --name "Teleprompter" --add-data "models;models" --hidden-import sherpa_onnx main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build complete!
echo   Output: dist\Teleprompter\
echo   Run:    dist\Teleprompter\Teleprompter.exe
echo ========================================
echo.
pause
