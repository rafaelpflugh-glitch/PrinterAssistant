@echo off
title Instalar Ambiente Python - Printer Assistant
cd /d "%~dp0"

echo ============================================================
echo   PRINTER ASSISTANT - INSTALADOR DE DEPENDENCIAS (MODO GIT)
echo ============================================================
echo.
echo DICA: Se este computador NAO precisa de Python/Git, voce pode
echo usar diretamente o pacote ZIP compilado (PrinterAssistant_v*.zip)
echo disponivel em GitHub Releases, que ja traz tudo pronto!
echo.

where python >NUL 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado neste computador!
    echo.
    echo Opcao 1 (Mais facil - Recomendado):
    echo   Baixe o arquivo PrinterAssistant_v*.zip em Releases do GitHub,
    echo   extraia e execute PrinterAssistant_Beta.exe (nao precisa de Python).
    echo.
    echo Opcao 2 (Modo desenvolvedor / Git):
    echo   Instale o Python 3.11+ marcando "Add Python to PATH" e rode este script novamente.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/2] Criando ambiente virtual local (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar .venv.
        pause
        exit /b 1
    )
)

echo [2/2] Instalando bibliotecas necessarias (requirements.txt)...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias. Verifique a conexao com a internet.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   AMBIENTE CONFIGURADO COM SUCESSO!
echo   Agora execute Iniciar_Printer_Assistant.bat
echo ============================================================
pause
