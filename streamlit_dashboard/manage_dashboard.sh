#!/bin/bash

# Dashboard Manager - Herramienta de gestión completa
# Ubicación: /home/botexecutor/shopify-bot/streamlit_dashboard/manage_dashboard.sh

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuración
DASHBOARD_DIR="/home/botexecutor/shopify-bot/streamlit_dashboard"
PID_FILE="${DASHBOARD_DIR}/streamlit.pid"
LOG_FILE="${DASHBOARD_DIR}/streamlit.log"
SERVICE_NAME="streamlit-dashboard"

# Funciones de utilidad
print_banner() {
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${PURPLE}🎛️  Dashboard Manager - Sistema de Pedidos Automatizados${NC}"
    echo -e "${PURPLE}================================================================${NC}"
}

log_message() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success_message() {
    echo -e "${GREEN}✅ $1${NC}"
}

error_message() {
    echo -e "${RED}❌ $1${NC}"
}

warning_message() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Función para mostrar el estado
show_status() {
    echo -e "${BLUE}📊 Estado del Dashboard:${NC}"
    echo "================================================================"
    
    # Verificar proceso
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p "${PID}" > /dev/null 2>&1; then
            success_message "Dashboard ejecutándose (PID: ${PID})"
            echo -e "   🌐 URLs disponibles:"
            echo -e "      • Local:  http://localhost:8501"
            echo -e "      • Red:    http://$(hostname -I | awk '{print $1}'):8501"
            
            # Mostrar uso de recursos
            echo -e "\n   📈 Uso de recursos:"
            ps -p "${PID}" -o pid,ppid,%cpu,%mem,cmd --no-headers | while read pid ppid cpu mem cmd; do
                echo -e "      • CPU: ${cpu}% | RAM: ${mem}% | CMD: ${cmd}"
            done
        else
            error_message "PID file existe pero proceso no está corriendo"
            rm -f "${PID_FILE}"
        fi
    else
        warning_message "Dashboard no está ejecutándose"
    fi
    
    # Verificar servicio systemd
    if systemctl is-enabled "${SERVICE_NAME}" >/dev/null 2>&1; then
        if systemctl is-active "${SERVICE_NAME}" >/dev/null 2>&1; then
            success_message "Servicio systemd activo y habilitado"
        else
            warning_message "Servicio systemd habilitado pero inactivo"
        fi
    else
        warning_message "Servicio systemd no está configurado"
    fi
    
    # Verificar logs recientes
    if [ -f "${LOG_FILE}" ]; then
        echo -e "\n   📝 Últimas líneas del log:"
        tail -n 3 "${LOG_FILE}" | sed 's/^/      /'
    fi
    
    echo "================================================================"
}

# Función para iniciar el dashboard
start_dashboard() {
    log_message "Iniciando dashboard..."
    
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p "${PID}" > /dev/null 2>&1; then
            warning_message "Dashboard ya está ejecutándose (PID: ${PID})"
            return 0
        fi
    fi
    
    cd "${DASHBOARD_DIR}"
    ./run_dashboard.sh
}

# Función para detener el dashboard
stop_dashboard() {
    log_message "Deteniendo dashboard..."
    
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p "${PID}" > /dev/null 2>&1; then
            kill "${PID}"
            sleep 2
            
            if ps -p "${PID}" > /dev/null 2>&1; then
                warning_message "Proceso no respondió, forzando terminación..."
                kill -9 "${PID}"
            fi
            
            rm -f "${PID_FILE}"
            success_message "Dashboard detenido exitosamente"
        else
            warning_message "PID file existe pero proceso no está corriendo"
            rm -f "${PID_FILE}"
        fi
    else
        warning_message "Dashboard no está ejecutándose"
    fi
}

# Función para reiniciar el dashboard
restart_dashboard() {
    log_message "Reiniciando dashboard..."
    stop_dashboard
    sleep 2
    start_dashboard
}

# Función para mostrar logs en tiempo real
show_logs() {
    if [ -f "${LOG_FILE}" ]; then
        echo -e "${BLUE}📄 Logs en tiempo real (Ctrl+C para salir):${NC}"
        echo "================================================================"
        tail -f "${LOG_FILE}"
    else
        error_message "Archivo de logs no encontrado: ${LOG_FILE}"
    fi
}

# Función para instalar el servicio systemd
install_service() {
    log_message "Instalando servicio systemd..."
    
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    if [ -f "${SERVICE_FILE}" ]; then
        warning_message "Servicio ya existe, sobrescribiendo..."
    fi
    
    # Copiar archivo de servicio
    sudo cp "${DASHBOARD_DIR}/streamlit-dashboard.service" "${SERVICE_FILE}" || {
        error_message "No se pudo copiar el archivo de servicio"
        return 1
    }
    
    # Recargar systemd
    sudo systemctl daemon-reload
    
    # Habilitar servicio
    sudo systemctl enable "${SERVICE_NAME}"
    
    success_message "Servicio systemd instalado y habilitado"
    log_message "Para gestionar el servicio usa:"
    echo "  • sudo systemctl start ${SERVICE_NAME}"
    echo "  • sudo systemctl stop ${SERVICE_NAME}"
    echo "  • sudo systemctl status ${SERVICE_NAME}"
}

# Función para mostrar información del sistema
show_system_info() {
    echo -e "${BLUE}🖥️  Información del Sistema:${NC}"
    echo "================================================================"
    echo -e "🏠 Directorio:     ${DASHBOARD_DIR}"
    echo -e "🐍 Python (venv):  $(source /home/botexecutor/venv-playwright/bin/activate && python --version)"
    echo -e "📦 Streamlit:      $(source /home/botexecutor/venv-playwright/bin/activate && streamlit --version)"
    echo -e "🌐 IP Local:       $(hostname -I | awk '{print $1}')"
    echo -e "💾 Espacio:        $(df -h "${DASHBOARD_DIR}" | tail -1 | awk '{print $4 " disponible de " $2}')"
    echo -e "⚡ Memoria:        $(free -h | grep Mem | awk '{print $3 " usado de " $2}')"
    echo "================================================================"
}

# Función para limpiar archivos temporales
cleanup() {
    log_message "Limpiando archivos temporales..."
    
    # Limpiar logs antiguos (mantener últimos 7 días)
    find "${DASHBOARD_DIR}" -name "*.log" -type f -mtime +7 -delete 2>/dev/null
    
    # Limpiar PID files huérfanos
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ! ps -p "${PID}" > /dev/null 2>&1; then
            rm -f "${PID_FILE}"
            log_message "PID file huérfano eliminado"
        fi
    fi
    
    success_message "Limpieza completada"
}

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}📖 Ayuda - Dashboard Manager${NC}"
    echo "================================================================"
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start      Iniciar el dashboard"
    echo "  stop       Detener el dashboard"
    echo "  restart    Reiniciar el dashboard"
    echo "  status     Mostrar estado actual"
    echo "  logs       Mostrar logs en tiempo real"
    echo "  install    Instalar servicio systemd para auto-inicio"
    echo "  info       Mostrar información del sistema"
    echo "  cleanup    Limpiar archivos temporales"
    echo "  help       Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start                    # Iniciar dashboard"
    echo "  $0 status                   # Ver estado"
    echo "  $0 logs                     # Ver logs en tiempo real"
    echo "================================================================"
}

# Función principal
main() {
    print_banner
    
    case "${1:-status}" in
        "start")
            start_dashboard
            ;;
        "stop")
            stop_dashboard
            ;;
        "restart")
            restart_dashboard
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "install")
            install_service
            ;;
        "info")
            show_system_info
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            warning_message "Comando desconocido: $1"
            show_help
            exit 1
            ;;
    esac
}

# Verificar que estamos en el directorio correcto
if [ ! -f "${DASHBOARD_DIR}/dashboard.py" ]; then
    error_message "Este script debe ejecutarse desde ${DASHBOARD_DIR}"
    exit 1
fi

# Ejecutar función principal
main "$@"
