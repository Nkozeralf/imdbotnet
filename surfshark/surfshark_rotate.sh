#!/bin/bash

# Configuración básica
VPN_DIR="/etc/openvpn"
AUTH_FILE="/home/botexecutor/surfshark/auth.txt"
REGION="${1:-global}"
MAX_ATTEMPTS=10
CONNECTION_TIMEOUT=15
LOG_FILE="/var/log/vpn_rotator.log"

# Función para logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Obtener IP pública
get_public_ip() {
    curl -4 -s --connect-timeout 5 "api.ipify.org" || \
    curl -4 -s --connect-timeout 5 "icanhazip.com"
}

# Verificar acceso a Shopify
test_shopify() {
    local status=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout 8 \
        --max-time 10 \
        "https://www.shopify.com")
    [[ "$status" =~ ^(200|301|302|403)$ ]]
}

# Seleccionar servidor VPN
select_server() {
    case "$REGION" in
        "co") find "$VPN_DIR" -type f -iname "co-*.ovpn" ;;
        "latam") find "$VPN_DIR" -type f \( -iname "co-*.ovpn" -o -iname "ar-*.ovpn" -o -iname "cl-*.ovpn" -o -iname "pe-*.ovpn" -o -iname "mx-*.ovpn" -o -iname "uy-*.ovpn" -o -iname "br-*.ovpn" \) ;;
        "global") find "$VPN_DIR" -type f -iname "*.ovpn" ;;
        *) find "$VPN_DIR" -type f -iname "$REGION-*.ovpn" ;;
    esac | shuf -n 1
}

# --- Ejecución principal ---

log "Iniciando rotación VPN"
log "Desconectando VPN anterior..."
sudo pkill openvpn
sleep 2

IP_ANTERIOR=$(get_public_ip)
log "IP actual: ${IP_ANTERIOR:-No disponible}"

for ((intento=1; intento<=MAX_ATTEMPTS; intento++)); do
    SELECTED=$(select_server)
    [ -z "$SELECTED" ] && { log "No hay servidores disponibles"; exit 1; }
    
    SERVER_NAME=$(basename "$SELECTED" .ovpn)
    log "Intento $intento/$MAX_ATTEMPTS - Conectando a: ${SERVER_NAME%%_*}"
    
    sudo openvpn --config "$SELECTED" --auth-user-pass "$AUTH_FILE" --daemon
    sleep $CONNECTION_TIMEOUT

    NUEVA_IP=$(get_public_ip)
    if [[ -z "$NUEVA_IP" || "$NUEVA_IP" == "$IP_ANTERIOR" ]]; then
        log "Fallo en conexión"
        sudo pkill openvpn
        sleep $((intento * 1))
        continue
    fi

    if test_shopify; then
        log "Conexión exitosa! IP: $NUEVA_IP"
        exit 0
    else
        log "Shopify no accesible"
        sudo pkill openvpn
        sleep $((intento * 1))
    fi
done

log "No se pudo establecer conexión adecuada"
exit 1