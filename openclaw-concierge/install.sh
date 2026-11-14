#!/usr/bin/env bash
# Instala as skills "concierge" e "casa" no workspace do OpenClaw (rodar no host do Gateway).
set -euo pipefail
WS="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SRC="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$WS/skills" "$WS/memory"
for skill in concierge casa; do
  rm -rf "$WS/skills/$skill"
  cp -R "$SRC/skills/$skill" "$WS/skills/$skill"
  echo "Skill instalada: $WS/skills/$skill"
done
[ -f "$WS/memory/casa.md" ] || printf '# Casa\n\n## Inventário\n<!-- cômodo | aparelho | entity_id | apelidos -->\n\n## Preferências\n' > "$WS/memory/casa.md"

if [ ! -f "$WS/memory/concierge.md" ]; then
  cp "$SRC/skills/concierge/references/perfil-modelo.md" "$WS/memory/concierge.md"
  echo "Perfil criado em $WS/memory/concierge.md (edite ou deixe o assistente preencher)."
fi

command -v openclaw >/dev/null && openclaw skills list | grep -iE 'concierge|casa' || true
echo "Pronto. No chat do app: /new, depois /concierge o que tenho hoje?  ou  /casa faz o inventário da casa"
[ -n "${HASS_URL:-}" ] || echo "Para a skill casa: configure HASS_URL e HASS_TOKEN (veja skills/casa/references/instalacao.md)."
