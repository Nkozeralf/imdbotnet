#!/bin/bash

# ===== CONFIGURACIÓN =====
CRED_FILE="config/credentials.json"
SESSION_ID=$(openssl rand -hex 4)  # por si quieres usarlo más adelante

# ===== DESCONECTAR VPN DE SURFSHARK (opcional, seguro) =====
echo "🔌 Desconectando Surfshark VPN si está activa..."
sudo killall openvpn 2>/dev/null
sleep 1

# ===== EXTRAER CREDENCIALES DESDE JSON =====
LOGIN=$(jq -r '.dataimpulse.login' "$CRED_FILE")
PASSWORD=$(jq -r '.dataimpulse.password' "$CRED_FILE")
HOST=$(jq -r '.dataimpulse.host' "$CRED_FILE")
PORT=$(jq -r '.dataimpulse.port' "$CRED_FILE")

# ===== CONSTRUIR PROXY URL =====
PROXY_URL="http://${LOGIN}:${PASSWORD}@${HOST}:${PORT}"

# ===== MOSTRAR Y PROBAR =====
echo "🌐 Probando proxy plano: $PROXY_URL"
IP=$(curl -s -x "$PROXY_URL" http://ip-api.com/line | tail -n 1)

if [[ -n "$IP" ]]; then
  echo "✅ Proxy funcionando. IP pública: $IP"
  exit 0
else
  echo "❌ Proxy falló. No se recibió IP."
  exit 1
fi
