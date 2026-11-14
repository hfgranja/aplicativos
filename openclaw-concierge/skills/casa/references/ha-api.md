# Referência rápida — `ha.sh` (API REST do Home Assistant)

Script: `bash {baseDir}/scripts/ha.sh <comando>` (usa `HASS_URL` e `HASS_TOKEN`).

| Comando | Uso |
| --- | --- |
| `ping` | Testa conexão e token |
| `states [filtro]` | Lista `entity_id | estado | nome` (filtro opcional, ex.: `sala`, `light.`) |
| `state <entity_id>` | Estado completo + atributos (brilho, temperatura, volume...) |
| `areas` | Cômodos e suas entidades |
| `services [domínio]` | Serviços disponíveis |
| `call <domínio> <serviço> '<json>'` | Executa uma ação |
| `template '<jinja>'` | Consulta avançada (ex.: `{{ states.light | selectattr('state','eq','on') | map(attribute='name') | list }}`) |
| `history <entity_id> [horas]` | Histórico (padrão 24 h) |

## Ações comuns

```bash
ha.sh call light turn_on  '{"entity_id":"light.sala","brightness_pct":40,"color_temp_kelvin":2700}'
ha.sh call light turn_off '{"entity_id":"all"}'
ha.sh call switch turn_off '{"entity_id":"switch.tomada_tv"}'
ha.sh call climate set_temperature '{"entity_id":"climate.quarto","temperature":23,"hvac_mode":"cool"}'
ha.sh call media_player turn_on '{"entity_id":"media_player.tv_sala"}'
ha.sh call media_player volume_set '{"entity_id":"media_player.sonos","volume_level":0.25}'
ha.sh call media_player play_media '{"entity_id":"media_player.sonos","media_content_type":"music","media_content_id":"<uri>"}'
ha.sh call cover close_cover '{"entity_id":"cover.persiana_sala"}'
ha.sh call vacuum start '{"entity_id":"vacuum.robo"}'
ha.sh call lock lock '{"entity_id":"lock.porta"}'                 # destrancar = pedir confirmação
ha.sh call scene turn_on '{"entity_id":"scene.cinema"}'
ha.sh call scene create '{"scene_id":"jantar","snapshot_entities":["light.sala_jantar","media_player.sonos"]}'
ha.sh call notify mobile_app_<celular> '{"title":"Casa","message":"Porta aberta há 10 min"}'
```

Domínios: `light`, `switch`, `fan`, `climate`, `media_player`, `cover`, `lock`,
`vacuum`, `camera`, `alarm_control_panel`, `sensor`, `binary_sensor`, `scene`, `script`.

Estado `unavailable` = aparelho desligado da tomada/rede ou fora do alcance.
