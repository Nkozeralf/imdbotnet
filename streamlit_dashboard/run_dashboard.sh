#!/bin/bash

# Script de lanzamiento para Streamlit Dashboard
# Ubicación: /home/botexecutor/shopify-bot/streamlit_dashboard/run_dashboard.sh

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para logging con timestamp
log_message() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Función para mostrar error y salir
error_exit() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

# Función para mostrar éxito
success_message() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Función para mostrar advertencia
warning_message() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Configuración
VENV_PATH="/home/botexecutor/venv-playwright"
DASHBOARD_DIR="/home/botexecutor/shopify-bot/streamlit_dashboard"
DASHBOARD_FILE="dashboard.py"
PID_FILE="${DASHBOARD_DIR}/streamlit.pid"
LOG_FILE="${DASHBOARD_DIR}/streamlit.log"

# Banner
echo "================================================================"
echo "🚀 Streamlit Dashboard Launcher - Sistema de Pedidos Automatizados"
echo "================================================================"

# Verificar que estamos en el directorio correcto
if [ ! -f "${DASHBOARD_DIR}/${DASHBOARD_FILE}" ]; then
    error_exit "dashboard.py no encontrado en ${DASHBOARD_DIR}"
fi

log_message "Verificando directorio de trabajo..."
cd "${DASHBOARD_DIR}" || error_exit "No se pudo cambiar al directorio ${DASHBOARD_DIR}"

# Verificar entorno virtual
log_message "Verificando entorno virtual..."
if [ ! -f "${VENV_PATH}/bin/activate" ]; then
    error_exit "Entorno virtual no encontrado en ${VENV_PATH}"
fi

# Activar entorno virtual
log_message "Activando entorno virtual venv-playwright..."
source "${VENV_PATH}/bin/activate" || error_exit "No se pudo activar el entorno virtual"

# Verificar Streamlit
log_message "Verificando instalación de Streamlit..."
if ! command -v streamlit &> /dev/null; then
    warning_message "Streamlit no encontrado, instalando..."
    pip install streamlit || error_exit "No se pudo instalar Streamlit"
fi

# Verificar dependencias adicionales
log_message "Verificando dependencias..."
python -c "import plotly, pandas, requests" 2>/dev/null || {
    warning_message "Instalando dependencias faltantes..."
    pip install plotly pandas requests || error_exit "No se pudieron instalar las dependencias"
}

# Verificar si hay una instancia corriendo
if [ -f "${PID_FILE}" ]; then
    OLD_PID=$(cat "${PID_FILE}")
    if ps -p "${OLD_PID}" > /dev/null 2>&1; then
        warning_message "Streamlit ya está corriendo (PID: ${OLD_PID})"
        echo "Para detenerlo, ejecuta: kill ${OLD_PID}"
        echo "O accede directamente a: http://localhost:8501"
        exit 0
    else
        log_message "Eliminando archivo PID obsoleto..."
        rm -f "${PID_FILE}"
    fi
fi

# Lanzar Streamlit
success_message "Iniciando Streamlit Dashboard..."
echo "================================================================"
echo "📊 Dashboard disponible en:"
echo "   🏠 Local:   http://localhost:8501"
echo "   🌐 Red:     http://$(hostname -I | awk '{print $1}'):8501"
echo "================================================================"
echo "💡 Consejos:"
echo "   • Presiona Ctrl+C para detener el servidor"
echo "   • Para ejecutar en background: ./run_dashboard.sh &"
echo "   • Para auto-inicio: usar el servicio systemd"
echo "================================================================"

# Ejecutar Streamlit y capturar PID
nohup streamlit run "${DASHBOARD_FILE}" \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --browser.gatherUsageStats=false \
    --server.fileWatcherType=poll \
    > "${LOG_FILE}" 2>&1 &

STREAMLIT_PID=$!
echo "${STREAMLIT_PID}" > "${PID_FILE}"

success_message "Streamlit iniciado exitosamente (PID: ${STREAMLIT_PID})"
log_message "Logs disponibles en: ${LOG_FILE}"

# Esperar un momento para verificar que se inició correctamente
sleep 3

if ps -p "${STREAMLIT_PID}" > /dev/null 2>&1; then
    success_message "✅ Dashboard ejecutándose correctamente"
    echo ""
    echo "🎯 Para acceder al dashboard:"
    echo "   http://localhost:8501"
    echo ""
    echo "🔧 Para gestionar el servicio:"
    echo "   • Ver estado: ps -p ${STREAMLIT_PID}"
    echo "   • Detener: kill ${STREAMLIT_PID}"
    echo "   • Ver logs: tail -f ${LOG_FILE}"
    echo ""
else
    error_exit "Streamlit falló al iniciar. Revisa los logs en ${LOG_FILE}"
fi
