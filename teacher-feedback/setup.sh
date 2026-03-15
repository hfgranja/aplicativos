#!/usr/bin/env bash
# ============================================================
#  PEC Teacher Feedback — Setup Wizard
#  Suporta: Ubuntu/Debian, macOS (Homebrew), WSL (Ubuntu)
# ============================================================

set -euo pipefail

# ── Cores ────────────────────────────────────────────────────
RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
CYAN="\033[36m"
WHITE="\033[97m"
BG_DARK="\033[48;5;234m"

ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
err()  { echo -e "  ${RED}✗${RESET}  $1"; }
info() { echo -e "  ${CYAN}→${RESET} $1"; }
step() { echo -e "\n${BOLD}${WHITE}$1${RESET}"; }
sep()  { echo -e "${DIM}────────────────────────────────────────────────────${RESET}"; }

ERRORS=()
WARNINGS=()

# ── Detectar SO ─────────────────────────────────────────────
detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
  elif grep -qi microsoft /proc/version 2>/dev/null; then
    OS="wsl"
  elif [[ -f /etc/debian_version ]]; then
    OS="debian"
  elif [[ -f /etc/fedora-release ]]; then
    OS="fedora"
  else
    OS="unknown"
  fi
}

# ── Helpers de instalação ────────────────────────────────────
pkg_install() {
  local pkg="$1"
  case "$OS" in
    macos)   brew install "$pkg" ;;
    debian|wsl) sudo apt-get install -y "$pkg" ;;
    fedora)  sudo dnf install -y "$pkg" ;;
    *)       warn "Instale manualmente: $pkg"; return 1 ;;
  esac
}

# ── Banner ───────────────────────────────────────────────────
print_banner() {
  clear
  echo -e "${BOLD}"
  echo "  ╔══════════════════════════════════════════════════════╗"
  echo "  ║                                                      ║"
  echo "  ║      PEC Teacher Feedback — Setup Wizard             ║"
  echo "  ║      Feedback Formativo com IA Local                 ║"
  echo "  ║                                                      ║"
  echo "  ╚══════════════════════════════════════════════════════╝"
  echo -e "${RESET}"
  echo -e "  ${DIM}Secretaria da Educação do Estado de São Paulo${RESET}"
  echo -e "  ${DIM}Backend: FastAPI + SQLite | Frontend: React + Vite${RESET}"
  echo -e "  ${DIM}LLM: Ollama (llama3.2) | Transcrição: faster-whisper${RESET}"
  echo ""
}

# ── Verificar Python ─────────────────────────────────────────
check_python() {
  step "[ 1/6 ] Python 3.10+"
  sep

  local py_cmd=""
  for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
      local ver
      ver=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
      local major minor
      major=$(echo "$ver" | cut -d. -f1)
      minor=$(echo "$ver" | cut -d. -f2)
      if [[ "$major" -ge 3 && "$minor" -ge 10 ]]; then
        py_cmd="$cmd"
        ok "Python $ver encontrado ($cmd)"
        break
      fi
    fi
  done

  if [[ -z "$py_cmd" ]]; then
    err "Python 3.10+ não encontrado."
    if [[ "$OS" == "macos" ]]; then
      info "Instale via: brew install python@3.12"
    elif [[ "$OS" == "debian" || "$OS" == "wsl" ]]; then
      info "Instale via: sudo apt install python3.12 python3.12-venv python3-pip"
    fi
    ERRORS+=("Python 3.10+ não instalado")
    PYTHON_CMD="python3"
  else
    PYTHON_CMD="$py_cmd"
    # Verificar venv
    if ! "$PYTHON_CMD" -m venv --help &>/dev/null 2>&1; then
      warn "módulo venv não encontrado."
      if [[ "$OS" == "debian" || "$OS" == "wsl" ]]; then
        info "Tentando instalar python3-venv..."
        sudo apt-get install -y python3-venv python3-pip || true
      fi
    else
      ok "módulo venv disponível"
    fi
  fi
}

# ── Verificar Node.js ────────────────────────────────────────
check_node() {
  step "[ 2/6 ] Node.js 18+"
  sep

  if command -v node &>/dev/null; then
    local ver
    ver=$(node --version | grep -oP '\d+' | head -1)
    if [[ "$ver" -ge 18 ]]; then
      ok "Node.js v$ver encontrado"
    else
      warn "Node.js v$ver encontrado (recomendado ≥ 18)"
      WARNINGS+=("Node.js versão antiga (v$ver)")
    fi
  else
    err "Node.js não encontrado."
    if [[ "$OS" == "macos" ]]; then
      info "Instale via: brew install node"
    else
      info "Instale via: https://nodejs.org  ou  nvm install 20"
    fi
    ERRORS+=("Node.js não instalado")
  fi

  if command -v npm &>/dev/null; then
    ok "npm $(npm --version) encontrado"
  else
    err "npm não encontrado."
    ERRORS+=("npm não instalado")
  fi
}

# ── Verificar FFmpeg ─────────────────────────────────────────
check_ffmpeg() {
  step "[ 3/6 ] FFmpeg (transcrição de áudio/vídeo)"
  sep

  if command -v ffmpeg &>/dev/null; then
    ok "FFmpeg $(ffmpeg -version 2>&1 | grep -oP 'version \S+' | head -1) encontrado"
  else
    warn "FFmpeg não encontrado. A transcrição de aulas ficará indisponível."
    echo ""
    read -rp "  Instalar FFmpeg agora? [S/n] " ans
    ans=${ans:-S}
    if [[ "$ans" =~ ^[Ss]$ ]]; then
      info "Instalando FFmpeg..."
      if [[ "$OS" == "macos" ]]; then
        brew install ffmpeg
      elif [[ "$OS" == "debian" || "$OS" == "wsl" ]]; then
        sudo apt-get update -qq && sudo apt-get install -y ffmpeg
      elif [[ "$OS" == "fedora" ]]; then
        sudo dnf install -y ffmpeg
      else
        err "Não foi possível instalar automaticamente."
        info "Baixe em: https://ffmpeg.org/download.html"
        WARNINGS+=("FFmpeg não instalado — transcrição indisponível")
      fi
    else
      WARNINGS+=("FFmpeg não instalado — transcrição indisponível")
    fi
  fi
}

# ── Verificar Ollama ─────────────────────────────────────────
check_ollama() {
  step "[ 4/6 ] Ollama + modelo llama3.2"
  sep

  if command -v ollama &>/dev/null; then
    ok "Ollama encontrado ($(ollama --version 2>/dev/null | head -1 || echo 'versão desconhecida'))"
  else
    warn "Ollama não encontrado."
    echo ""
    read -rp "  Instalar Ollama agora? [S/n] " ans
    ans=${ans:-S}
    if [[ "$ans" =~ ^[Ss]$ ]]; then
      info "Instalando Ollama via script oficial..."
      curl -fsSL https://ollama.com/install.sh | sh
      ok "Ollama instalado"
    else
      err "Ollama é obrigatório para geração de feedback com IA."
      ERRORS+=("Ollama não instalado")
      return
    fi
  fi

  # Verificar se o modelo llama3.2 está disponível
  info "Verificando modelo llama3.2..."
  if ollama list 2>/dev/null | grep -q "llama3.2"; then
    ok "Modelo llama3.2 já disponível"
  else
    echo ""
    echo -e "  ${YELLOW}O modelo llama3.2 (~2 GB) ainda não foi baixado.${RESET}"
    read -rp "  Baixar agora? [S/n] " ans
    ans=${ans:-S}
    if [[ "$ans" =~ ^[Ss]$ ]]; then
      info "Iniciando download do llama3.2 (pode demorar alguns minutos)..."
      # Iniciar ollama serve em background se não estiver rodando
      if ! curl -sf http://localhost:11434 &>/dev/null; then
        info "Iniciando servidor Ollama em background..."
        ollama serve &>/dev/null &
        sleep 3
      fi
      ollama pull llama3.2
      ok "Modelo llama3.2 pronto"
    else
      WARNINGS+=("Modelo llama3.2 não baixado — execute 'ollama pull llama3.2' antes de usar")
    fi
  fi
}

# ── Instalar backend ─────────────────────────────────────────
setup_backend() {
  step "[ 5/6 ] Backend Python (FastAPI)"
  sep

  local backend_dir
  backend_dir="$(cd "$(dirname "$0")" && pwd)/backend"

  if [[ ! -d "$backend_dir" ]]; then
    err "Diretório backend não encontrado: $backend_dir"
    ERRORS+=("Diretório backend ausente")
    return
  fi

  info "Criando ambiente virtual Python..."
  if [[ -d "$backend_dir/venv" ]]; then
    ok "Ambiente virtual já existe"
  else
    "$PYTHON_CMD" -m venv "$backend_dir/venv"
    ok "Ambiente virtual criado"
  fi

  local pip="$backend_dir/venv/bin/pip"

  info "Atualizando pip..."
  "$pip" install --upgrade pip --quiet

  info "Instalando dependências Python..."
  "$pip" install -r "$backend_dir/requirements.txt" --quiet
  ok "Dependências Python instaladas"

  # Criar diretório de dados
  mkdir -p "$backend_dir/data/uploads"
  ok "Diretório data/uploads criado"

  # Criar arquivo .env se não existir
  local env_file="$backend_dir/.env"
  if [[ ! -f "$env_file" ]]; then
    cat > "$env_file" << 'ENVEOF'
# PEC Teacher Feedback — Configuração
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
WHISPER_MODEL=base
DATABASE_URL=sqlite:///./data/feedback.db
UPLOAD_DIR=./data/uploads
ENVEOF
    ok ".env criado com configurações padrão"
  else
    ok ".env já existe"
  fi
}

# ── Instalar frontend ────────────────────────────────────────
setup_frontend() {
  step "[ 6/6 ] Frontend React (Vite)"
  sep

  local frontend_dir
  frontend_dir="$(cd "$(dirname "$0")" && pwd)/frontend"

  if [[ ! -d "$frontend_dir" ]]; then
    err "Diretório frontend não encontrado: $frontend_dir"
    ERRORS+=("Diretório frontend ausente")
    return
  fi

  info "Instalando dependências npm..."
  (cd "$frontend_dir" && npm install --silent)
  ok "Dependências npm instaladas"
}

# ── Criar script de start ────────────────────────────────────
create_start_script() {
  local root_dir
  root_dir="$(cd "$(dirname "$0")" && pwd)"

  cat > "$root_dir/start.sh" << 'STARTEOF'
#!/usr/bin/env bash
# PEC Teacher Feedback — Iniciar aplicação

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
LOG_DIR="$ROOT/data/logs"

mkdir -p "$LOG_DIR"

GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
BOLD="\033[1m"
RESET="\033[0m"

cleanup() {
  echo -e "\n${YELLOW}  Encerrando serviços...${RESET}"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  echo -e "  ✓ Encerrado"
  exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║    PEC Teacher Feedback — Iniciando...       ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${RESET}"

# Verificar Ollama
if ! curl -sf http://localhost:11434 &>/dev/null; then
  echo -e "  ${YELLOW}→ Iniciando Ollama em background...${RESET}"
  ollama serve &>/dev/null &
  sleep 2
  echo -e "  ${GREEN}✓ Ollama iniciado${RESET}"
fi

# Backend
echo -e "  ${CYAN}→ Iniciando backend (FastAPI na porta 8000)...${RESET}"
(cd "$BACKEND" && "./venv/bin/uvicorn" main:app \
  --reload \
  --port 8000 \
  --log-level warning \
  >> "$LOG_DIR/backend.log" 2>&1) &
BACKEND_PID=$!
sleep 2

# Frontend
echo -e "  ${CYAN}→ Iniciando frontend (Vite na porta 5173)...${RESET}"
(cd "$FRONTEND" && npm run dev -- --port 5173 \
  >> "$LOG_DIR/frontend.log" 2>&1) &
FRONTEND_PID=$!
sleep 3

echo ""
echo -e "  ${GREEN}${BOLD}✓ Aplicação pronta!${RESET}"
echo ""
echo -e "  ${BOLD}Acesse:${RESET}"
echo -e "  ${CYAN}→ App:     http://localhost:5173${RESET}"
echo -e "  ${CYAN}→ API:     http://localhost:8000${RESET}"
echo -e "  ${CYAN}→ API Docs: http://localhost:8000/docs${RESET}"
echo ""
echo -e "  ${DIM}Logs: $LOG_DIR/${RESET}"
echo -e "  ${DIM}Pressione Ctrl+C para encerrar${RESET}"
echo ""

wait
STARTEOF
  chmod +x "$root_dir/start.sh"
  ok "start.sh criado"
}

# ── Criar script stop ────────────────────────────────────────
create_stop_script() {
  local root_dir
  root_dir="$(cd "$(dirname "$0")" && pwd)"

  cat > "$root_dir/stop.sh" << 'STOPEOF'
#!/usr/bin/env bash
echo "Encerrando PEC Teacher Feedback..."
pkill -f "uvicorn backend.main" 2>/dev/null && echo "  ✓ Backend encerrado" || echo "  - Backend não estava rodando"
pkill -f "vite.*5173" 2>/dev/null && echo "  ✓ Frontend encerrado" || echo "  - Frontend não estava rodando"
echo "Pronto."
STOPEOF
  chmod +x "$root_dir/stop.sh"
  ok "stop.sh criado"
}

# ── Relatório final ──────────────────────────────────────────
print_summary() {
  echo ""
  sep
  echo ""

  if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo -e "  ${RED}${BOLD}Erros encontrados (necessitam correção):${RESET}"
    for e in "${ERRORS[@]}"; do
      err "$e"
    done
    echo ""
  fi

  if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo -e "  ${YELLOW}${BOLD}Avisos:${RESET}"
    for w in "${WARNINGS[@]}"; do
      warn "$w"
    done
    echo ""
  fi

  if [[ ${#ERRORS[@]} -eq 0 ]]; then
    echo -e "  ${GREEN}${BOLD}✓ Instalação concluída com sucesso!${RESET}"
    echo ""
    echo -e "  ${BOLD}Para iniciar a aplicação:${RESET}"
    echo ""
    echo -e "    ${CYAN}./start.sh${RESET}"
    echo ""
    echo -e "  ${BOLD}Ou manualmente:${RESET}"
    echo ""
    echo -e "    ${DIM}# Terminal 1 — Backend${RESET}"
    echo -e "    cd backend && ../venv/bin/uvicorn main:app --reload --port 8000"
    echo ""
    echo -e "    ${DIM}# Terminal 2 — Frontend${RESET}"
    echo -e "    cd frontend && npm run dev"
    echo ""
    echo -e "    ${DIM}# LLM (em background)${RESET}"
    echo -e "    ollama serve"
    echo ""
    echo -e "  ${BOLD}Acesso:${RESET}  ${CYAN}http://localhost:5173${RESET}"
    echo ""
  else
    echo -e "  ${YELLOW}Resolva os erros acima e execute novamente: ${CYAN}./setup.sh${RESET}"
    echo ""
  fi
  sep
  echo ""
}

# ── Main ─────────────────────────────────────────────────────
main() {
  print_banner

  echo -e "  Este script irá:"
  echo -e "  ${DIM}  1. Verificar pré-requisitos (Python, Node, FFmpeg, Ollama)${RESET}"
  echo -e "  ${DIM}  2. Criar ambiente virtual Python e instalar dependências${RESET}"
  echo -e "  ${DIM}  3. Instalar pacotes npm do frontend${RESET}"
  echo -e "  ${DIM}  4. Criar scripts start.sh e stop.sh${RESET}"
  echo ""
  read -rp "  Continuar? [S/n] " ans
  ans=${ans:-S}
  if [[ ! "$ans" =~ ^[Ss]$ ]]; then
    echo "  Cancelado."
    exit 0
  fi

  detect_os
  echo -e "\n  ${DIM}Sistema detectado: ${OS}${RESET}"

  check_python
  check_node
  check_ffmpeg
  check_ollama

  if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo ""
    echo -e "  ${RED}${BOLD}Há erros críticos pendentes. Alguns passos podem falhar.${RESET}"
    echo ""
    read -rp "  Continuar mesmo assim? [s/N] " ans
    ans=${ans:-N}
    if [[ ! "$ans" =~ ^[Ss]$ ]]; then
      print_summary
      exit 1
    fi
    ERRORS=()
  fi

  setup_backend
  setup_frontend
  create_start_script
  create_stop_script

  print_summary
}

main "$@"
