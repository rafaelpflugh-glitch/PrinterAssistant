@echo off
title Gerar Release - Printer Assistant
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" tools\build_release.py
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" tools\build_release.py
) else (
    python tools\build_release.py
)

echo.
pause
