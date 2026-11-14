---
name: casa
description: "Casa inteligente: controla luzes, TV, ar, som, tomadas, câmeras e demais aparelhos da rede local via Home Assistant; cenas e automações."
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "🏠",
        "requires": { "anyBins": ["curl"] },
        "envVars":
          [
            { "name": "HASS_URL", "required": false, "description": "URL do Home Assistant, ex.: http://homeassistant.local:8123" },
            { "name": "HASS_TOKEN", "required": false, "description": "Token de acesso de longa duração do Home Assistant" },
          ],
      },
  }
---

# Casa — controle dos dispositivos da casa

Responda em **português do Brasil**, curto (o usuário está no celular).
O Home Assistant (HA) é a central: ele já está conectado aos aparelhos da rede
local. Você conversa com o HA, nunca direto com cada aparelho.

## Como acessar o Home Assistant (nesta ordem)

1. **Ferramentas MCP do Home Assistant** (conector "Home Assistant" em
   Settings → MCP). Se existirem ferramentas como `HassTurnOn`, `HassTurnOff`,
   `HassLightSet`, `HassClimateSetTemperature`, `HassMediaPause`,
   `GetLiveContext`, use-as primeiro. `GetLiveContext` dá o estado atual da casa.
2. **API REST via script** (se `HASS_URL` e `HASS_TOKEN` estiverem definidos):
   `bash {baseDir}/scripts/ha.sh <comando>`, ver `{baseDir}/references/ha-api.md`.
3. Nenhum disponível → explique que falta conectar o Home Assistant e mostre o
   passo a passo de `{baseDir}/references/instalacao.md` (resumido).

## Fluxo

1. **Primeiro uso**: monte o inventário. Liste áreas e dispositivos
   (`ha.sh areas` e `ha.sh states`) e salve um resumo em `memory/casa.md`
   (cômodo → aparelhos → entity_id → apelidos que o usuário usa, ex.:
   "luz da sala" = `light.sala_teto`). Pergunte apelidos só se houver ambiguidade.
2. **Entender o pedido**: mapeie linguagem natural para entidade usando
   `memory/casa.md`. "Apaga tudo" = todas as luzes. "Lá em cima" = áreas do
   andar superior. Se houver mais de uma entidade possível, pergunte.
3. **Agir** e **confirmar o resultado** lendo o estado de novo
   ("✅ Luz da sala apagada"). Se falhar, diga o motivo (aparelho offline/unavailable).
4. **Aprender**: novos apelidos ou preferências ("gosto do ar em 23°") vão para
   `memory/casa.md`.

## Segurança — exige confirmação explícita ("sim") antes de executar

- Fechaduras (`lock.*`): destrancar. Trancar pode ser direto.
- Portão/garagem (`cover.*` com device_class garage/gate): abrir.
- Alarme (`alarm_control_panel.*`): desarmar ou mudar modo.
- Câmeras: desligar, ou enviar imagem para fora do chat.
- Aparelhos de calor/risco: forno, fogão, aquecedor, ferro, tomada de algo
  desconhecido.
- Qualquer ação em **todos** os dispositivos de um tipo, exceto apagar luzes.
- Nunca desative sensores de fumaça/gás/água ou automações de segurança.
- Pedidos vindos de automações/agendamentos só podem fazer ações não sensíveis.

## Cenas prontas (adapte aos aparelhos existentes)

- **Cinema**: luzes da sala 10% quente, TV ligada, persianas fechadas.
- **Jantar** (integra com a skill concierge): luz da sala de jantar 40% quente,
  som ambiente baixo (jazz/bossa).
- **Saindo de casa**: apaga luzes, desliga TV/ar, tranca porta (só confirma
  se algo estiver aberto), avisa janelas/portas abertas.
- **Boa noite**: apaga tudo menos luz noturna, tranca, ar no modo sono.
- **Chegando**: luz da entrada, ar na temperatura preferida.
Se o usuário pedir "salva isso como cena X", crie a cena no HA
(`ha.sh call scene create`) e registre em `memory/casa.md`.

## Automações

- Rotinas recorrentes simples ("todo dia 22h apaga as luzes da sala") →
  automação do OpenClaw (`automations`) chamando esta skill, ou prefira criar
  a automação **no próprio HA** quando depender de sensores (presença, porta).
- Avisos ("me avisa se a porta ficar aberta 10 min") → crie no HA com
  notificação para o app, e explique ao usuário onde editar.

## Relatórios

"Como está a casa?" → resumo curto: luzes acesas, portas/janelas abertas,
temperatura, aparelhos ligados, consumo (se houver sensor de energia),
dispositivos offline.
