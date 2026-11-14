# Conectar a casa ao OpenClaw

## Arquitetura

```
Celular (app OpenClaw) ──► Gateway OpenClaw ──► Home Assistant ──► aparelhos da rede local
                                                  (Wi-Fi, Zigbee, Matter, Bluetooth, nuvem dos fabricantes)
```

O Home Assistant (HA) descobre e integra milhares de marcas: Smart Life/Tuya,
Positivo Casa Inteligente, Xiaomi/Mi Home, Philips Hue, Samsung/LG TVs (SmartThings/webOS),
Chromecast/Google, Alexa, Sonos, Roku, ar-condicionados (LG ThinQ, Samsung, Midea),
robôs aspiradores, câmeras (Intelbras, TP-Link Tapo, Ezviz), interfones, Matter etc.

## Passos

1. **Instale o Home Assistant** num computador sempre ligado na rede de casa
   (Raspberry Pi, mini-PC, Home Assistant Green, ou Docker no mesmo PC do OpenClaw).
   Acesse `http://homeassistant.local:8123`.
2. **Adicione os aparelhos**: Configurações → Dispositivos e serviços. O HA mostra
   automaticamente o que encontrou na rede ("Descobertos"). Clique em
   *Configurar* em cada um e adicione as integrações das marcas que usam nuvem.
   Organize por **Áreas** (Sala, Quarto, Cozinha...) — o assistente usa isso.
3. **Crie um token**: no HA, seu perfil → Segurança → *Tokens de acesso de longa
   duração* → Criar. Copie.
4. **Conecte ao OpenClaw** (escolha uma ou as duas):
   - **MCP (recomendado)**: no HA, adicione a integração *Model Context Protocol Server*.
     No OpenClaw: Control UI → Plugins → conector **Home Assistant**, ou
     Settings → MCP → Add server → Streamable HTTP →
     `http://homeassistant.local:8123/api/mcp` com header
     `Authorization: Bearer <token>`. Teste: `openclaw mcp doctor homeassistant --probe`.
   - **API REST (usado pelo script `ha.sh`)**: defina `HASS_URL` e `HASS_TOKEN`
     no ambiente do Gateway ou em `openclaw.json`:
     ```json5
     { skills: { entries: { casa: { env: {
         HASS_URL: "http://homeassistant.local:8123",
         HASS_TOKEN: "<token>" } } } } }
     ```
5. **Fora de casa**: se o Gateway roda em outra rede (VPS/nuvem), use
   Tailscale (HA e Gateway na mesma tailnet) ou Home Assistant Cloud (Nabu Casa).
   Nunca exponha a porta 8123 direto na internet.
6. No chat: `/new` e `/casa faz o inventário da casa`.

## Descobrir o que há na rede (opcional)

`bash {baseDir}/scripts/descobrir-rede.sh` lista IPs, fabricantes (via nmap) e
serviços mDNS (Chromecast, AirPlay, Hue, impressoras) — útil para saber o que
ainda falta integrar no HA. Somente leitura; use apenas na sua própria rede.
