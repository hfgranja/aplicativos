#!/usr/bin/env bash
# Automações opcionais do Concierge. Ajuste TZ e o destino (canal) antes de rodar.
# Sem --channel/--to, o resultado fica na conversa/sessão padrão (app/WebChat).
set -euo pipefail
TZ_NAME="${TZ_NAME:-America/Sao_Paulo}"
DEST_ARGS=()   # ex.: DEST_ARGS=(--channel telegram --to "<seu-chat-id>")

# Resumo da manhã (seg–sex 7h47)
openclaw automations create "47 7 * * 1-5" \
  "Use a skill concierge. Me mande em português o resumo do dia: compromissos de hoje com horários e locais, conflitos, janelas livres, e se houver um evento de lazer hoje, lembre de reserva/ingresso. Máximo 10 linhas." \
  --name "Concierge: resumo da manhã" --tz "$TZ_NAME" --session isolated --announce "${DEST_ARGS[@]}"

# Sugestões de fim de semana (quinta 18h13)
openclaw automations create "13 18 * * 4" \
  "Use a skill concierge. Olhe minha agenda de sexta a domingo e sugira em português: 3 eventos/shows, 2 restaurantes e 1 vinho para o fim de semana, alinhados ao meu perfil e sem conflito com a agenda. Inclua links." \
  --name "Concierge: fim de semana" --tz "$TZ_NAME" --session isolated --announce "${DEST_ARGS[@]}"

# Radar de shows dos artistas favoritos (segunda 12h21)
openclaw automations create "21 12 * * 1" \
  "Use a skill concierge. Procure shows anunciados na minha cidade para os artistas e gêneros favoritos do meu perfil nos próximos 3 meses. Só me avise se houver novidade em relação ao histórico; caso contrário, responda apenas NADA NOVO." \
  --name "Concierge: radar de shows" --tz "$TZ_NAME" --session isolated --announce "${DEST_ARGS[@]}"

openclaw automations list
