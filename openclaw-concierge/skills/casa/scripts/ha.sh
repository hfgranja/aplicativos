#!/usr/bin/env bash
# Cliente mínimo da API REST do Home Assistant.
# Requer: HASS_URL (ex.: http://homeassistant.local:8123) e HASS_TOKEN.
set -euo pipefail
: "${HASS_URL:?Defina HASS_URL}"; : "${HASS_TOKEN:?Defina HASS_TOKEN}"
URL="${HASS_URL%/}"
req() { curl -fsS -m 20 -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" "$@"; }
tpl() { req -X POST "$URL/api/template" -d "$(python3 -c 'import json,sys;print(json.dumps({"template":sys.argv[1]}))' "$1")"; }

cmd="${1:-help}"; shift || true
case "$cmd" in
  ping)     req "$URL/api/" ;;
  states)   # [filtro] — lista entity_id | estado | nome amigável
            req "$URL/api/states" | python3 -c '
import json,sys
f=(sys.argv[1] if len(sys.argv)>1 else "").lower()
for s in json.load(sys.stdin):
    n=s["attributes"].get("friendly_name","")
    line=s["entity_id"]+" | "+s["state"]+" | "+n
    if f in line.lower(): print(line)' "${1:-}" ;;
  state)    req "$URL/api/states/${1:?entity_id}" ;;
  areas)    tpl '{% for a in areas() %}{{ area_name(a) }}: {{ area_entities(a) | join(", ") }}
{% endfor %}' ;;
  services) req "$URL/api/services" | python3 -c '
import json,sys
f=sys.argv[1] if len(sys.argv)>1 else ""
for d in json.load(sys.stdin):
    if not f or d["domain"]==f: print(d["domain"]+": "+", ".join(d["services"]))' "${1:-}" ;;
  call)     [ -n "${3:-}" ] || set -- "${1:-}" "${2:-}" '{}'
            # call <domínio> <serviço> '<json>'  ex.: call light turn_on '{"entity_id":"light.sala","brightness_pct":40}'
            req -X POST "$URL/api/services/${1:?dominio}/${2:?servico}" -d "${3:-}" ;;
  template) tpl "${1:?template}" ;;
  history)  # history <entity_id> [horas]
            since=$(date -u -d "-${2:-24} hours" +%Y-%m-%dT%H:%M:%SZ)
            req "$URL/api/history/period/$since?filter_entity_id=${1:?entity_id}&minimal_response" ;;
  *) echo "uso: ha.sh ping|states [filtro]|state <id>|areas|services [dominio]|call <dominio> <servico> '<json>'|template '<tpl>'|history <id> [horas]"; exit 1 ;;
esac
