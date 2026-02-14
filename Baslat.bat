@echo off
chcp 65001 >nul 2>&1
title WHIXPI V1.0 - Professional Studio

echo ==================================================
echo   WHIXPI Pro V1.0 - Baslatiliyor...
echo ==================================================
echo.

call "venv_whisperx\Scripts\python.exe" main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Bir sorun olustu!
    echo.
    echo Kontrol edilecekler:
    echo   - Python yuklu mu?
    echo   - pip install -r requirements.txt yapildi mi?
    echo.
)

pause
