# 🍷 Concierge — assistente pessoal dentro do OpenClaw

Skill do OpenClaw que transforma seu agente num assistente pessoal para:

- 📅 **Agenda** — "o que tenho amanhã?", "marca jantar sexta 20h", "acha um horário livre", lembretes
- 🍽️ **Restaurantes** — busca por ocasião, bairro, cozinha e preço; confirma horário; link de reserva
- 🍷 **Vinhos** — indicação, harmonização, foto de rótulo/carta, preços, sua "adega" de notas
- 🎤 **Shows, teatro, cinema, exposições, passeios** — agenda cultural, ingressos, conflitos com sua agenda
- 🗺️ **Roteiros** — "planeja meu sábado": evento + jantar + bar, com horários encadeados

Tudo funciona **pelo chat do app OpenClaw** no celular. O assistente aprende suas
preferências e guarda histórico em `memory/concierge.md` no workspace.

## Estrutura

```
skills/concierge/
  SKILL.md                 # instruções principais + roteamento
  references/
    agenda.md              # agenda do celular (node), gog/Google Calendar, fallback por link
    restaurantes.md
    vinhos.md
    eventos.md
    roteiro.md
    perfil-modelo.md       # modelo do seu perfil/preferências
install.sh                 # copia a skill para ~/.openclaw/workspace/skills
automations/criar-automacoes.sh  # resumo da manhã, fim de semana, radar de shows
```

## Instalação

O app do celular é um *node*; a skill fica no **host do Gateway** (o computador/servidor
onde o OpenClaw roda — ou no próprio celular se você usa Gateway via Termux).

**Opção 1 — terminal no host do Gateway**

```bash
git clone https://github.com/hfgranja/aplicativos.git
cd aplicativos/openclaw-concierge
./install.sh
```

**Opção 2 — pelo próprio chat do OpenClaw** (sem terminal)

Em *Plugins → Skills → My skills*, importe a pasta `skills/concierge`
(ou peça ao agente: "crie uma skill pessoal a partir deste SKILL.md" e cole o conteúdo).

Depois, no chat: `/new` e teste `/concierge o que tenho hoje?`.

## Configuração recomendada

1. **Busca na web** (obrigatório para pesquisar): `openclaw configure --section web`
   (Brave, Perplexity, DuckDuckGo etc.).
2. **Agenda do celular**: no app Android/iOS, dê permissão de *Calendário*.
   Leitura (`calendar.events`) já vem liberada. Para o assistente **criar** eventos,
   libere uma vez no Gateway (`openclaw.json`):
   ```json5
   { gateway: { nodes: { commands: { allow: ["calendar.add", "reminders.add"] } } } }
   ```
   Alternativa: skill `gog` com Google Calendar (`gog auth add voce@gmail.com --services calendar`).
   Sem nenhuma das duas, o assistente envia um link "Adicionar ao Google Agenda".
3. **Restaurantes (opcional, melhor qualidade)**: skill `goplaces` + `GOOGLE_PLACES_API_KEY`.
4. **Localização (opcional)**: permissão de localização no app, para "perto de mim".
5. **Automações (opcional)**: `TZ_NAME=America/Sao_Paulo ./automations/criar-automacoes.sh`
   — ou simplesmente peça no chat: "todo dia útil às 7h45 me manda o resumo da agenda".

## Exemplos de uso

- "O que tenho essa semana? Tem algum buraco na quinta à noite?"
- "Jantar romântico sábado, 2 pessoas, Pinheiros ou Jardins, até R$ 250 por pessoa."
- "Que vinho levo para um risoto de cogumelos? Até R$ 120."
- *(foto da carta de vinhos)* "Qual desses vale a pena com picanha?"
- "Tem show bom de MPB ou jazz em SP nas próximas duas semanas?"
- "Planeja meu domingo: algo ao ar livre de manhã e um almoço legal."
- "Gostei muito do Barolo de ontem, nota 5." → vai para sua adega pessoal.

## Segurança

- O assistente **sempre pede confirmação** antes de criar/alterar/apagar eventos,
  reservar ou comprar.
- Nunca pede nem armazena senhas ou cartão; pagamentos são feitos por você no link oficial.
