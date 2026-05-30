@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Teleprompter Model Downloader
echo ========================================
echo.

set MODEL_URL=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20.tar.bz2
set DOWNLOAD_FILE=model_download.tar.bz2
set EXTRACT_DIR=model_extract
set MODELS_DIR=models

echo [INFO] Downloading voice model (approx 350MB)...
echo [INFO] URL: %MODEL_URL%
echo.

:: Check if curl is available
curl --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] curl not found. Please install curl or download manually.
    echo [INFO] Manual download: %MODEL_URL%
    pause
    exit /b 1
)

:: Download
curl -L -o %DOWNLOAD_FILE% %MODEL_URL%
if errorlevel 1 (
    echo [ERROR] Download failed!
    pause
    exit /b 1
)

echo.
echo [INFO] Extracting model...

:: Check if tar is available (Windows 10+ has built-in tar)
tar --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] tar not found. Please install tar or extract manually.
    echo [INFO] The downloaded file is: %DOWNLOAD_FILE%
    pause
    exit /b 1
)

:: Extract
tar -xjf %DOWNLOAD_FILE%
if errorlevel 1 (
    echo [ERROR] Extraction failed!
    pause
    exit /b 1
)

:: Move model files
echo [INFO] Moving model files to models/ directory...
if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"

move "sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20\tokens.txt" "%MODELS_DIR%\" >nul
move "sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20\encoder-epoch-99-avg-1.onnx" "%MODELS_DIR%\" >nul
move "sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20\decoder-epoch-99-avg-1.onnx" "%MODELS_DIR%\" >nul
move "sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20\joiner-epoch-99-avg-1.onnx" "%MODELS_DIR%\" >nul

:: Cleanup
echo [INFO] Cleaning up...
del /f /q %DOWNLOAD_FILE%
rmdir /s /q "sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20"

echo.
echo ========================================
echo   Model download complete!
echo   Files saved to: models/
echo ========================================
echo.
pause
