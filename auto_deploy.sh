#!/bin/bash

# =========================================================================
# AUTO GIT DEPLOY - Shopify Bot
# Script para automatizar commits y versionamiento inteligente
# =========================================================================

# Configuración de colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración del proyecto
PROJECT_NAME="Shopify Bot"
BASE_VERSION="3.1"
REMOTE_REPO="https://github.com/Nkozeralf/imdbotnet.git"
PROJECT_DIR="/home/botexecutor/shopify-bot"

# Función para mostrar mensajes con colores
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Función para obtener la fecha actual
get_timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

# Función para obtener el siguiente número de versión
get_next_version() {
    local current_version=$(git tag --sort=-version:refname | grep "^v${BASE_VERSION}\." | head -n 1 | sed 's/^v//')
    
    if [ -z "$current_version" ]; then
        echo "${BASE_VERSION}.1"
    else
        local patch_version=$(echo $current_version | cut -d'.' -f3)
        local next_patch=$((patch_version + 1))
        echo "${BASE_VERSION}.${next_patch}"
    fi
}

# Función para analizar cambios en archivos específicos
analyze_file_changes() {
    local changed_files=$(git diff --name-only HEAD~1 2>/dev/null || git ls-files)
    local commit_components=()
    
    # Analizar tipos de archivos modificados
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            case "$file" in
                *launcher.py)
                    commit_components+=("🚀 Launcher")
                    ;;
                *pedido_bot_base.py)
                    commit_components+=("🤖 Bot Core")
                    ;;
                *analizador_de_tienda.py)
                    commit_components+=("📊 Store Analyzer")
                    ;;
                *rotador_proxy.py)
                    commit_components+=("🔄 Proxy Rotator")
                    ;;
                *dashboard.py|*streamlit*)
                    commit_components+=("📈 Dashboard")
                    ;;
                *data_generator.py)
                    commit_components+=("💾 Data Generator")
                    ;;
                *notificador_telegram.py)
                    commit_components+=("📱 Telegram Notifier")
                    ;;
                *rabbitmq*)
                    commit_components+=("🐰 RabbitMQ")
                    ;;
                *verificador_formulario.py)
                    commit_components+=("✅ Form Validator")
                    ;;
                *reporte.py)
                    commit_components+=("📋 Reports")
                    ;;
                *limpiador_logs.py)
                    commit_components+=("🧹 Log Cleaner")
                    ;;
                config/*)
                    commit_components+=("⚙️ Config")
                    ;;
                logs/*)
                    commit_components+=("📝 Logs")
                    ;;
                proxies/*)
                    commit_components+=("🌐 Proxies")
                    ;;
                surfshark/*)
                    commit_components+=("🦈 Surfshark")
                    ;;
                tiendas/*)
                    commit_components+=("🏪 Stores")
                    ;;
                requirements.txt)
                    commit_components+=("📦 Dependencies")
                    ;;
                *.sh)
                    commit_components+=("⚡ Scripts")
                    ;;
                *)
                    commit_components+=("📄 Files")
                    ;;
            esac
        fi
    done <<< "$changed_files"
    
    # Eliminar duplicados y formatear
    local unique_components=($(printf "%s\n" "${commit_components[@]}" | sort -u))
    echo "${unique_components[@]}"
}

# Función para generar mensaje de commit automático
generate_commit_message() {
    local version=$1
    local components=$(analyze_file_changes)
    local timestamp=$(get_timestamp)
    
    if [ -z "$components" ]; then
        components="📄 General Updates"
    fi
    
    echo "v${version}: ${components}

🔄 Auto-deploy: ${timestamp}
📋 Cambios detectados en: $(git diff --name-only --cached | tr '\n' ' ')
🏷️ Version: ${BASE_VERSION} - Respeta VPN → Proxy → Navegación

---
Auto-generated commit by deploy script"
}

# Función principal de deploy
deploy_project() {
    print_header "INICIANDO AUTO DEPLOY - ${PROJECT_NAME}"
    
    # Verificar si estamos en el directorio correcto
    if [ ! -f "launcher.py" ]; then
        print_error "No se encontró launcher.py. ¿Estás en el directorio correcto?"
        print_status "Cambiando al directorio del proyecto..."
        cd "$PROJECT_DIR" || exit 1
    fi
    
    # Verificar si hay cambios para commitear
    if [ -z "$(git status --porcelain)" ]; then
        print_warning "No hay cambios para commitear."
        read -p "¿Deseas crear un tag de versión de todas formas? (y/n): " create_tag
        if [ "$create_tag" != "y" ]; then
            exit 0
        fi
    fi
    
    # Inicializar git si no existe
    if [ ! -d ".git" ]; then
        print_status "Inicializando repositorio Git..."
        git init
        git remote add origin "$REMOTE_REPO"
    fi
    
    # Configurar .gitignore si no existe
    if [ ! -f ".gitignore" ]; then
        print_status "Creando .gitignore..."
        cat > .gitignore << EOF
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
.DS_Store
*.swp
*.swo
*~
.env
.vscode/
.idea/
*.save
EOF
    fi
    
    # Obtener la siguiente versión
    local next_version=$(get_next_version)
    print_status "Próxima versión: v${next_version}"
    
    # Mostrar archivos que se van a agregar
    print_status "Archivos detectados para commit:"
    git status --porcelain
    
    # Confirmar con el usuario
    echo ""
    read -p "¿Proceder con el deploy de la versión v${next_version}? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        print_warning "Deploy cancelado por el usuario."
        exit 0
    fi
    
    # Agregar todos los archivos
    print_status "Agregando archivos al staging area..."
    git add .
    
    # Generar mensaje de commit
    local commit_message=$(generate_commit_message "$next_version")
    
    # Realizar commit
    print_status "Realizando commit..."
    git commit -m "$commit_message"
    
    # Crear tag de versión
    print_status "Creando tag v${next_version}..."
    git tag -a "v${next_version}" -m "Release ${next_version} - ${PROJECT_NAME}

🎯 Versión: ${BASE_VERSION} - Respeta VPN → Proxy → Navegación
📅 Fecha: $(get_timestamp)
🚀 Deploy automático"
    
    # Push al repositorio remoto
    print_status "Subiendo cambios al repositorio remoto..."
    
    # Push de la rama principal
    git push origin main 2>/dev/null || git push origin master 2>/dev/null || {
        print_status "Configurando rama principal..."
        git branch -M main
        git push -u origin main
    }
    
    # Push de los tags
    git push origin --tags
    
    print_header "✅ DEPLOY COMPLETADO EXITOSAMENTE"
    print_status "Versión desplegada: v${next_version}"
    print_status "Repositorio: ${REMOTE_REPO}"
    print_status "Timestamp: $(get_timestamp)"
    
    # Mostrar últimos commits
    echo ""
    print_status "Últimos commits:"
    git log --oneline -5
}

# Función para mostrar ayuda
show_help() {
    echo "Auto Git Deploy - ${PROJECT_NAME}"
    echo ""
    echo "Uso: $0 [opción]"
    echo ""
    echo "Opciones:"
    echo "  deploy    Realizar deploy completo (por defecto)"
    echo "  status    Mostrar estado del repositorio"
    echo "  version   Mostrar versión actual y próxima"
    echo "  help      Mostrar esta ayuda"
    echo ""
    echo "El script automáticamente:"
    echo "  - Detecta cambios en archivos"
    echo "  - Genera commits descriptivos"
    echo "  - Maneja versionamiento automático"
    echo "  - Sube cambios a GitHub"
}

# Función para mostrar estado
show_status() {
    print_header "ESTADO DEL REPOSITORIO"
    
    if [ -d ".git" ]; then
        echo "📁 Directorio: $(pwd)"
        echo "🌿 Rama actual: $(git branch --show-current)"
        echo "📋 Estado:"
        git status --short
        echo ""
        echo "🏷️ Últimos tags:"
        git tag --sort=-version:refname | head -5
    else
        print_warning "No es un repositorio Git"
    fi
}

# Función para mostrar información de versión
show_version_info() {
    print_header "INFORMACIÓN DE VERSIÓN"
    echo "📦 Proyecto: ${PROJECT_NAME}"
    echo "🔢 Versión base: ${BASE_VERSION}"
    echo "🔢 Próxima versión: v$(get_next_version)"
    echo "📅 Timestamp: $(get_timestamp)"
}

# Función principal
main() {
    case "${1:-deploy}" in
        "deploy")
            deploy_project
            ;;
        "status")
            show_status
            ;;
        "version")
            show_version_info
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
