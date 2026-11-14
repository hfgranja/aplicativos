#!/usr/bin/env bash
# Inventário (somente leitura) dos dispositivos na SUA rede local.
# Rode no host do Gateway, que deve estar na mesma rede da casa.
set -uo pipefail
iface=$(ip route show default 2>/dev/null | awk '{print $5; exit}')
cidr=$(ip -o -f inet addr show "$iface" 2>/dev/null | awk '{print $4; exit}')
echo "Interface: ${iface:-?}  Rede: ${cidr:-?}"
echo
if command -v nmap >/dev/null && [ -n "${cidr:-}" ]; then
  echo "== Dispositivos ativos (nmap -sn) =="
  nmap -sn "$cidr" -oG - 2>/dev/null | awk '/Up$/{print $2, $3}'
else
  echo "== Vizinhos conhecidos (ARP) — instale nmap para varredura completa =="
fi
echo; ip neigh 2>/dev/null | awk '$NF!="FAILED"{print $1, $5}'
if command -v avahi-browse >/dev/null; then
  echo; echo "== Serviços mDNS (Chromecast, AirPlay, Hue, HomeKit, impressoras, Home Assistant) =="
  timeout 8 avahi-browse -art 2>/dev/null | awk -F';' '/^=/{print $4" | "$3" | "$7" | "$8}' | sort -u
fi
for h in homeassistant.local:8123; do
  curl -fsS -m 3 -o /dev/null "http://$h" 2>/dev/null && echo && echo "✅ Home Assistant encontrado em http://$h"
done
