#!/usr/bin/env bash
# Instala a skill "concierge" no workspace do OpenClaw (rodar no host do Gateway).
set -euo pipefail
WS="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SRC="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$WS/skills" "$WS/memory"
rm -rf "$WS/skills/concierge"
cp -R "$SRC/skills/concierge" "$WS/skills/concierge"

if [ ! -f "$WS/memory/concierge.md" ]; then
  cp "$SRC/skills/concierge/references/perfil-modelo.md" "$WS/memory/concierge.md"
  echo "Perfil criado em $WS/memory/concierge.md (edite ou deixe o assistente preencher)."
fi

echo "Skill instalada em $WS/skills/concierge"
command -v openclaw >/dev/null && openclaw skills list | grep -i concierge || true
echo "Pronto. No chat do app, mande /new e depois: /concierge o que tenho hoje?"
