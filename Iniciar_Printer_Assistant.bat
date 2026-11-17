@echo off
title Printer Assistant v1.0.0-beta
cd /d "%~dp0"

echo ============================================================
echo Iniciando Printer Assistant v1.0.0-beta...
echo ============================================================

REM Se houver ambiente virtual local (.venv ou venv), usa o Python dele
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" main.py
) else (
    python main.py
)

if errorlevel 1 (
    echo.
    echo ============================================================
    echo Ocorreu um erro ao executar o Printer Assistant.
    echo Verifique se o Python esta instalado e se as dependencias
    echo foram instaladas via: pip install -r requirements.txt
    echo ============================================================
    pause
)
