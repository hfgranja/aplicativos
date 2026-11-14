# Agenda

Use a primeira opção disponível, nesta ordem:

## A) Agenda do celular (node Android/iOS) — recomendado

Ferramenta `nodes` no node do celular pareado:

- Ler: comando `calendar.events` (ex.: params com intervalo de datas ISO
  do dia/semana pedida). Se não souber os parâmetros, descreva o node
  (`nodes` → describe) para ver o schema do comando.
- Criar: comando `calendar.add` (título, início, fim, local, notas).
  `calendar.add` é "perigoso" por padrão: se der erro
  `requires explicit gateway.nodes.commands.allow opt-in`, explique ao
  usuário que precisa liberar uma vez (ver README do concierge) e, enquanto
  isso, use o fallback C.
- Lembretes nativos: `reminders.list` / `reminders.add` (mesma regra de opt-in).

## B) Google Calendar via skill `gog` (se instalada e autenticada)

- Listar: `gog calendar events primary --from <iso> --to <iso>`
- Criar: `gog calendar create primary --summary "Título" --from <iso> --to <iso>`
- Atualizar: `gog calendar update primary <eventId> ...`
- Cores sugeridas: restaurante = 6 (laranja), show/evento = 3 (roxo),
  trabalho = 9 (azul), lazer ao ar livre = 10 (verde).

## C) Fallback sem acesso de escrita

Gere um link do Google Calendar pré-preenchido para o usuário tocar:
`https://calendar.google.com/calendar/render?action=TEMPLATE&text=<título>&dates=<YYYYMMDDTHHMMSS>/<YYYYMMDDTHHMMSS>&ctz=<fuso>&location=<local>&details=<notas>`
(URL-encode os campos).

## Comportamentos

- "O que tenho hoje/amanhã/essa semana?" → liste por horário, com local e
  tempo livre entre compromissos. Destaque conflitos.
- "Acha um horário para X" → procure janelas livres respeitando horário
  comercial do perfil; proponha 2–3 opções.
- Ao criar evento de lazer, inclua no campo notas: endereço, link da
  reserva/ingresso, código de confirmação (se houver) e um lembrete
  (padrão: 2h antes para jantar, 1 dia + 3h antes para show).
- Lembretes pontuais pedidos no chat ("me lembra às 18h de comprar o vinho"):
  crie uma automação one-shot (`automations`/cron, `--at`) entregando no
  canal atual, ou `reminders.add` no celular.
- Nunca apague eventos sem confirmação explícita mostrando o evento exato.
