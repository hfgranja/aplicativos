@echo off
:: PEC Teacher Feedback — Launcher do Setup (Windows)
:: Execute com duplo clique — não requer PowerShell manual

title PEC Teacher Feedback — Setup

:: Verificar se PowerShell está disponível
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] PowerShell não encontrado. Instale o Windows PowerShell 5+ ou PowerShell 7+.
    pause
    exit /b 1
)

echo.
echo   Iniciando wizard de instalação...
echo   (Uma janela PowerShell será aberta)
echo.

:: Executar setup.ps1 com bypass de execution policy (sem alterar política global)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"

if %errorlevel% neq 0 (
    echo.
    echo   O setup foi encerrado com erros. Verifique as mensagens acima.
    pause
)
