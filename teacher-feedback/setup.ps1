#Requires -Version 5.0
# ================================================================
#  PEC Teacher Feedback — Setup Wizard para Windows
#  Compatível com: Windows 10 (21H2+) e Windows 11
#  PowerShell 5.1+ ou PowerShell 7+
# ================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Helpers de saída ─────────────────────────────────────────
function Write-OK    { param($msg) Write-Host "  " -NoNewline; Write-Host "✓" -ForegroundColor Green -NoNewline;  Write-Host " $msg" }
function Write-Warn  { param($msg) Write-Host "  " -NoNewline; Write-Host "⚠" -ForegroundColor Yellow -NoNewline; Write-Host " $msg" }
function Write-Err   { param($msg) Write-Host "  " -NoNewline; Write-Host "✗" -ForegroundColor Red -NoNewline;    Write-Host " $msg" }
function Write-Info  { param($msg) Write-Host "  " -NoNewline; Write-Host "→" -ForegroundColor Cyan -NoNewline;   Write-Host " $msg" }
function Write-Step  { param($msg) Write-Host ""; Write-Host $msg -ForegroundColor White -BackgroundColor DarkGray }
function Write-Sep   { Write-Host "  ────────────────────────────────────────────────────" -ForegroundColor DarkGray }
function Ask-Yes     { param($prompt) $ans = Read-Host "  $prompt [S/n]"; return ($ans -eq "" -or $ans -match "^[Ss]$") }

$script:Errors   = [System.Collections.Generic.List[string]]::new()
$script:Warnings = [System.Collections.Generic.List[string]]::new()
$script:PythonExe = "python"
$script:HasWinget = $false

# ── Verificar winget ─────────────────────────────────────────
function Test-Winget {
    try {
        $null = Get-Command winget -ErrorAction Stop
        $script:HasWinget = $true
        return $true
    } catch {
        return $false
    }
}

# ── Banner ───────────────────────────────────────────────────
function Show-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║                                                      ║" -ForegroundColor Cyan
    Write-Host "  ║      PEC Teacher Feedback — Setup Wizard             ║" -ForegroundColor Cyan
    Write-Host "  ║      Feedback Formativo com IA Local (Windows)       ║" -ForegroundColor Cyan
    Write-Host "  ║                                                      ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Secretaria da Educação do Estado de São Paulo" -ForegroundColor DarkGray
    Write-Host "  Backend: FastAPI + SQLite  |  Frontend: React + Vite" -ForegroundColor DarkGray
    Write-Host "  LLM: Ollama (llama3.2)     |  Transcrição: faster-whisper" -ForegroundColor DarkGray
    Write-Host ""
}

# ── 1. Python ────────────────────────────────────────────────
function Check-Python {
    Write-Step "[ 1/6 ] Python 3.10+"
    Write-Sep

    $found = $false
    $candidates = @("py", "python3", "python")

    foreach ($cmd in $candidates) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if ($major -ge 3 -and $minor -ge 10) {
                    # Para o py launcher, usar -3.xx flag
                    if ($cmd -eq "py") {
                        $script:PythonExe = "py"
                    } else {
                        $script:PythonExe = $cmd
                    }
                    Write-OK "Python $major.$minor encontrado ($cmd)"
                    $found = $true
                    break
                } else {
                    Write-Warn "Python $major.$minor encontrado ($cmd) — versão muito antiga"
                }
            }
        } catch { continue }
    }

    if (-not $found) {
        Write-Err "Python 3.10+ não encontrado."
        Write-Host ""
        if ($script:HasWinget) {
            if (Ask-Yes "Instalar Python 3.12 via winget agora?") {
                Write-Info "Instalando Python 3.12..."
                winget install --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
                # Atualizar PATH
                $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
                $script:PythonExe = "py"
                Write-OK "Python instalado. Reinicie o setup se necessário."
            }
        } else {
            Write-Info "Baixe em: https://www.python.org/downloads/"
            Write-Info "Marque 'Add Python to PATH' durante a instalação."
        }
        $script:Errors.Add("Python 3.10+ não instalado")
    }
}

# ── 2. Node.js ───────────────────────────────────────────────
function Check-Node {
    Write-Step "[ 2/6 ] Node.js 18+"
    Write-Sep

    try {
        $ver = node --version 2>&1
        if ($ver -match "v(\d+)") {
            $major = [int]$Matches[1]
            if ($major -ge 18) {
                Write-OK "Node.js $ver encontrado"
            } else {
                Write-Warn "Node.js $ver encontrado (recomendado >= 18)"
                $script:Warnings.Add("Node.js versão antiga ($ver)")
            }
        }
    } catch {
        Write-Err "Node.js não encontrado."
        Write-Host ""
        if ($script:HasWinget) {
            if (Ask-Yes "Instalar Node.js LTS via winget agora?") {
                Write-Info "Instalando Node.js LTS..."
                winget install --id OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
                $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
                Write-OK "Node.js instalado."
            }
        } else {
            Write-Info "Baixe em: https://nodejs.org/en/download"
        }
        $script:Errors.Add("Node.js não instalado")
        return
    }

    try {
        $npmVer = npm --version 2>&1
        Write-OK "npm $npmVer encontrado"
    } catch {
        Write-Err "npm não encontrado."
        $script:Errors.Add("npm não encontrado")
    }
}

# ── 3. FFmpeg ────────────────────────────────────────────────
function Check-FFmpeg {
    Write-Step "[ 3/6 ] FFmpeg (transcrição de áudio/vídeo)"
    Write-Sep

    try {
        $ver = ffmpeg -version 2>&1 | Select-String "version" | Select-Object -First 1
        Write-OK "FFmpeg encontrado: $($ver.ToString().Trim().Substring(0, [Math]::Min(50, $ver.ToString().Trim().Length)))"
    } catch {
        Write-Warn "FFmpeg não encontrado. A transcrição de aulas ficará indisponível."
        Write-Host ""
        if ($script:HasWinget) {
            if (Ask-Yes "Instalar FFmpeg via winget agora?") {
                Write-Info "Instalando FFmpeg..."
                winget install --id Gyan.FFmpeg --silent --accept-source-agreements --accept-package-agreements
                $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
                Write-OK "FFmpeg instalado."
                return
            }
        } else {
            Write-Info "Baixe em: https://www.gyan.dev/ffmpeg/builds/ (ffmpeg-release-essentials.zip)"
            Write-Info "Extraia e adicione a pasta 'bin' ao PATH do Windows."
        }
        $script:Warnings.Add("FFmpeg não instalado — transcrição indisponível")
    }
}

# ── 4. Ollama + llama3.2 ─────────────────────────────────────
function Check-Ollama {
    Write-Step "[ 4/6 ] Ollama + modelo llama3.2"
    Write-Sep

    $ollamaFound = $false
    try {
        $ver = ollama --version 2>&1
        Write-OK "Ollama encontrado: $ver"
        $ollamaFound = $true
    } catch {
        Write-Warn "Ollama não encontrado."
        Write-Host ""
        if (Ask-Yes "Instalar Ollama agora?") {
            if ($script:HasWinget) {
                Write-Info "Instalando Ollama via winget..."
                winget install --id Ollama.Ollama --silent --accept-source-agreements --accept-package-agreements
                $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
            } else {
                Write-Info "Abrindo página de download do Ollama..."
                Start-Process "https://ollama.com/download/windows"
                Write-Host ""
                Write-Host "  Instale o Ollama e pressione Enter para continuar..." -ForegroundColor Yellow
                Read-Host
            }
            try {
                $null = Get-Command ollama -ErrorAction Stop
                Write-OK "Ollama instalado com sucesso."
                $ollamaFound = $true
            } catch {
                Write-Warn "Ollama ainda não está no PATH. Reinicie o computador e execute o setup novamente."
                $script:Errors.Add("Ollama não encontrado no PATH após instalação")
                return
            }
        } else {
            $script:Errors.Add("Ollama não instalado")
            return
        }
    }

    if ($ollamaFound) {
        # Verificar modelo llama3.2
        Write-Info "Verificando modelo llama3.2..."
        try {
            $models = ollama list 2>&1
            if ($models -match "llama3\.2") {
                Write-OK "Modelo llama3.2 já disponível"
            } else {
                Write-Host ""
                Write-Host "  O modelo llama3.2 (~2 GB) ainda não foi baixado." -ForegroundColor Yellow
                if (Ask-Yes "Baixar llama3.2 agora? (pode demorar alguns minutos)") {
                    # Iniciar servidor Ollama se não estiver rodando
                    try {
                        $null = Invoke-WebRequest "http://localhost:11434" -TimeoutSec 2 -ErrorAction Stop
                    } catch {
                        Write-Info "Iniciando servidor Ollama..."
                        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
                        Start-Sleep -Seconds 3
                    }
                    Write-Info "Baixando llama3.2..."
                    ollama pull llama3.2
                    Write-OK "Modelo llama3.2 pronto"
                } else {
                    $script:Warnings.Add("Modelo llama3.2 não baixado — execute 'ollama pull llama3.2' antes de usar")
                }
            }
        } catch {
            Write-Warn "Não foi possível verificar os modelos. Certifique-se de executar 'ollama pull llama3.2'."
            $script:Warnings.Add("Verificação de modelo llama3.2 falhou")
        }
    }
}

# ── 5. Backend Python ────────────────────────────────────────
function Setup-Backend {
    Write-Step "[ 5/6 ] Backend Python (FastAPI)"
    Write-Sep

    $backendDir = Join-Path $PSScriptRoot "backend"

    if (-not (Test-Path $backendDir)) {
        Write-Err "Diretório backend não encontrado: $backendDir"
        $script:Errors.Add("Diretório backend ausente")
        return
    }

    $venvDir = Join-Path $backendDir "venv"
    $venvPip = Join-Path $venvDir "Scripts\pip.exe"
    $reqFile = Join-Path $backendDir "requirements.txt"

    # Criar venv
    if (Test-Path $venvDir) {
        Write-OK "Ambiente virtual já existe"
    } else {
        Write-Info "Criando ambiente virtual Python..."
        & $script:PythonExe -m venv $venvDir
        Write-OK "Ambiente virtual criado em: $venvDir"
    }

    # Atualizar pip
    Write-Info "Atualizando pip..."
    & $venvPip install --upgrade pip --quiet

    # Instalar dependências
    Write-Info "Instalando dependências Python..."
    & $venvPip install -r $reqFile --quiet
    Write-OK "Dependências Python instaladas"

    # Criar pasta data
    $dataDir = Join-Path $backendDir "data\uploads"
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    }
    Write-OK "Diretório data\uploads criado"

    # Criar .env
    $envFile = Join-Path $backendDir ".env"
    if (-not (Test-Path $envFile)) {
        $envContent = @"
# PEC Teacher Feedback — Configuração
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
WHISPER_MODEL=base
DATABASE_URL=sqlite:///./data/feedback.db
UPLOAD_DIR=./data/uploads
"@
        Set-Content -Path $envFile -Value $envContent -Encoding UTF8
        Write-OK ".env criado com configurações padrão"
    } else {
        Write-OK ".env já existe"
    }
}

# ── 6. Frontend ──────────────────────────────────────────────
function Setup-Frontend {
    Write-Step "[ 6/6 ] Frontend React (Vite)"
    Write-Sep

    $frontendDir = Join-Path $PSScriptRoot "frontend"

    if (-not (Test-Path $frontendDir)) {
        Write-Err "Diretório frontend não encontrado: $frontendDir"
        $script:Errors.Add("Diretório frontend ausente")
        return
    }

    Write-Info "Instalando dependências npm..."
    Push-Location $frontendDir
    try {
        npm install --silent
        Write-OK "Dependências npm instaladas"
    } finally {
        Pop-Location
    }
}

# ── Gerar start.bat ──────────────────────────────────────────
function Create-StartScript {
    $startPath = Join-Path $PSScriptRoot "start.bat"

    $content = @'
@echo off
:: PEC Teacher Feedback — Iniciar aplicação (Windows)
title PEC Teacher Feedback

SET ROOT=%~dp0
SET BACKEND=%ROOT%backend
SET FRONTEND=%ROOT%frontend

echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║    PEC Teacher Feedback — Iniciando...       ║
echo   ╚══════════════════════════════════════════════╝
echo.

:: Criar pasta de logs
if not exist "%BACKEND%\data\logs" mkdir "%BACKEND%\data\logs"

:: Verificar se Ollama está rodando
curl -sf http://localhost:11434 >nul 2>&1
if %errorlevel% neq 0 (
    echo   [→] Iniciando Ollama em background...
    start /b "" ollama serve >nul 2>&1
    timeout /t 3 /nobreak >nul
    echo   [✓] Ollama iniciado
)

:: Iniciar backend em nova janela
echo   [→] Iniciando backend (FastAPI - porta 8000)...
start "PEC Backend" cmd /k "cd /d "%BACKEND%" && venv\Scripts\uvicorn.exe main:app --reload --port 8000"

:: Aguardar backend subir
timeout /t 3 /nobreak >nul

:: Iniciar frontend em nova janela
echo   [→] Iniciando frontend (Vite - porta 5173)...
start "PEC Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"

:: Aguardar frontend subir
timeout /t 4 /nobreak >nul

echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║   Aplicação iniciada com sucesso!            ║
echo   ║                                              ║
echo   ║   App:       http://localhost:5173           ║
echo   ║   API:       http://localhost:8000           ║
echo   ║   API Docs:  http://localhost:8000/docs      ║
echo   ╚══════════════════════════════════════════════╝
echo.
echo   Duas janelas foram abertas (Backend e Frontend).
echo   Feche-as para encerrar a aplicação.
echo.

:: Abrir browser automaticamente
timeout /t 2 /nobreak >nul
start "" http://localhost:5173

pause
'@
    Set-Content -Path $startPath -Value $content -Encoding UTF8
    Write-OK "start.bat criado"
}

# ── Gerar stop.bat ───────────────────────────────────────────
function Create-StopScript {
    $stopPath = Join-Path $PSScriptRoot "stop.bat"

    $content = @'
@echo off
:: PEC Teacher Feedback — Encerrar aplicação (Windows)
title PEC Teacher Feedback — Encerrar

echo.
echo   Encerrando PEC Teacher Feedback...
echo.

:: Encerrar uvicorn (backend)
taskkill /FI "WINDOWTITLE eq PEC Backend*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo   [✓] Backend encerrado
) else (
    echo   [-] Backend nao estava rodando
)

:: Encerrar vite (frontend)
taskkill /FI "WINDOWTITLE eq PEC Frontend*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo   [✓] Frontend encerrado
) else (
    echo   [-] Frontend nao estava rodando
)

:: Encerrar processos node que usam porta 5173 (fallback)
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":5173 " 2^>nul') do (
    taskkill /PID %%p /F >nul 2>&1
)

:: Encerrar processos que usam porta 8000 (fallback)
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":8000 " 2^>nul') do (
    taskkill /PID %%p /F >nul 2>&1
)

echo.
echo   Pronto. Ollama continua rodando em background.
echo   Para encerrá-lo: taskkill /IM ollama.exe /F
echo.
pause
'@
    Set-Content -Path $stopPath -Value $content -Encoding UTF8
    Write-OK "stop.bat criado"
}

# ── Relatório final ──────────────────────────────────────────
function Show-Summary {
    Write-Host ""
    Write-Sep
    Write-Host ""

    if ($script:Errors.Count -gt 0) {
        Write-Host "  Erros encontrados (necessitam correção):" -ForegroundColor Red
        foreach ($e in $script:Errors) { Write-Err $e }
        Write-Host ""
    }

    if ($script:Warnings.Count -gt 0) {
        Write-Host "  Avisos:" -ForegroundColor Yellow
        foreach ($w in $script:Warnings) { Write-Warn $w }
        Write-Host ""
    }

    if ($script:Errors.Count -eq 0) {
        Write-Host "  ✓ Instalação concluída com sucesso!" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Para iniciar a aplicação:" -ForegroundColor White
        Write-Host ""
        Write-Host "    → Duplo clique em:  start.bat" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Ou manualmente (3 janelas separadas):" -ForegroundColor White
        Write-Host ""
        Write-Host "    # Janela 1 — LLM" -ForegroundColor DarkGray
        Write-Host "    ollama serve" -ForegroundColor DarkCyan
        Write-Host ""
        Write-Host "    # Janela 2 — Backend" -ForegroundColor DarkGray
        Write-Host "    cd backend" -ForegroundColor DarkCyan
        Write-Host "    venv\Scripts\uvicorn main:app --reload --port 8000" -ForegroundColor DarkCyan
        Write-Host ""
        Write-Host "    # Janela 3 — Frontend" -ForegroundColor DarkGray
        Write-Host "    cd frontend" -ForegroundColor DarkCyan
        Write-Host "    npm run dev" -ForegroundColor DarkCyan
        Write-Host ""
        Write-Host "  Acesso:" -ForegroundColor White
        Write-Host "    http://localhost:5173" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host "  Resolva os erros acima e execute setup.bat novamente." -ForegroundColor Yellow
        Write-Host ""
    }
    Write-Sep
    Write-Host ""
}

# ── Main ─────────────────────────────────────────────────────
function Main {
    Show-Banner
    Test-Winget | Out-Null

    Write-Host "  Este script irá:"
    Write-Host "    1. Verificar pré-requisitos (Python, Node.js, FFmpeg, Ollama)" -ForegroundColor DarkGray
    Write-Host "    2. Criar ambiente virtual Python e instalar dependências" -ForegroundColor DarkGray
    Write-Host "    3. Instalar pacotes npm do frontend" -ForegroundColor DarkGray
    Write-Host "    4. Criar scripts start.bat e stop.bat" -ForegroundColor DarkGray
    Write-Host ""

    if ($script:HasWinget) {
        Write-OK "winget disponível — instalação automática de dependências habilitada"
    } else {
        Write-Warn "winget não encontrado — instalações serão manuais"
        Write-Info "Para obter winget: https://aka.ms/getwinget"
    }
    Write-Host ""

    if (-not (Ask-Yes "Continuar?")) {
        Write-Host "  Cancelado." -ForegroundColor Yellow
        exit 0
    }

    Check-Python
    Check-Node
    Check-FFmpeg
    Check-Ollama

    if ($script:Errors.Count -gt 0) {
        Write-Host ""
        Write-Host "  Há erros críticos pendentes. Alguns passos podem falhar." -ForegroundColor Red
        Write-Host ""
        if (-not (Ask-Yes "Continuar mesmo assim?")) {
            Show-Summary
            exit 1
        }
        $script:Errors.Clear()
    }

    Setup-Backend
    Setup-Frontend
    Create-StartScript
    Create-StopScript

    Show-Summary

    Write-Host "  Pressione qualquer tecla para sair..." -ForegroundColor DarkGray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Main
