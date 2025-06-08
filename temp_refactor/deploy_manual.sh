#!/bin/bash

# Deploy manual de refactorización
set -e

PROJECT_DIR="/home/botexecutor/shopify-bot"
BACKUP_DIR="/home/botexecutor/backup_$(date +%Y%m%d_%H%M%S)"

echo "🚀 Iniciando refactorización manual..."

# Crear backup
echo "💾 Creando backup..."
mkdir -p "$BACKUP_DIR"
cp -r "$PROJECT_DIR" "$BACKUP_DIR/shopify-bot-original"

# Ir a directorio temporal donde están los nuevos archivos
cd temp_refactor

# Verificar que los archivos existen
if [[ ! -f "bot_core.py" ]] || [[ ! -f "bot_executor.py" ]]; then
    echo "❌ Archivos no encontrados en temp_refactor/"
    exit 1
fi

# Mover archivos al directorio principal
cd ..
mv temp_refactor/bot_core.py .
mv temp_refactor/bot_executor.py .

# Crear capa de compatibilidad
cat > pedido_bot_base_compat.py << 'COMPAT_EOF'
# pedido_bot_base_compat.py - Capa de compatibilidad
import warnings
from bot_core import ejecutar_pedido, cargar_configuracion_tienda

def ejecutar_pedido_old(tienda_id, proxy_config=None, fast_mode=False):
    warnings.warn("Usando API de compatibilidad", DeprecationWarning)
    return ejecutar_pedido(tienda_id, proxy_config, fast_mode)

class OptimizedStoreAutomation:
    def execute_order(self, store_id, proxy_config=None, fast_mode=False):
        return ejecutar_pedido(store_id, proxy_config, fast_mode)

__all__ = ['ejecutar_pedido_old', 'OptimizedStoreAutomation', 'cargar_configuracion_tienda']
COMPAT_EOF

# Actualizar launcher.py
if [[ -f "launcher.py" ]]; then
    echo "🔧 Actualizando launcher.py..."
    sed -i.bak 's/from pedido_bot_base import ejecutar_pedido/from bot_core import ejecutar_pedido/' launcher.py
fi

# Crear script de rollback
cat > rollback_refactor.sh << 'ROLLBACK_EOF'
#!/bin/bash
echo "🔄 Iniciando rollback..."

if [[ -f "pedido_bot_base.py.backup" ]]; then
    cp "pedido_bot_base.py.backup" "pedido_bot_base.py"
    echo "✅ pedido_bot_base.py restaurado"
fi

if [[ -f "launcher.py.backup" ]]; then
    cp "launcher.py.backup" "launcher.py"
    echo "✅ launcher.py restaurado"
fi

rm -f bot_core.py bot_executor.py pedido_bot_base_compat.py

echo "✅ Rollback completado"
ROLLBACK_EOF

chmod +x rollback_refactor.sh

# Crear documentación
cat > MIGRATION_INFO.md << 'DOC_EOF'
# Migración a Arquitectura Modular

## Fecha de Migración
$(date)

## Cambios Realizados
- ✅ pedido_bot_base.py dividido en bot_core.py + bot_executor.py
- ✅ Timeouts inteligentes implementados
- ✅ Detección automática de tiendas Shopify
- ✅ Compatibilidad mantenida

## Archivos Importantes
- **bot_core.py**: Núcleo del bot
- **bot_executor.py**: Coordinador de tareas
- **pedido_bot_base_compat.py**: Compatibilidad

## Rollback
Si hay problemas: `./rollback_refactor.sh`

## Testing
- `python bot_core.py`
- `python bot_executor.py test`
DOC_EOF

# Test básico
echo "🧪 Ejecutando test básico..."
source /home/botexecutor/venv-playwright/bin/activate

python -c "
import bot_core
import bot_executor
print('✅ Imports funcionan correctamente')
"

echo "✅ Refactorización completada!"
echo "📋 Archivos creados:"
echo "  - bot_core.py"
echo "  - bot_executor.py" 
echo "  - pedido_bot_base_compat.py"
echo "  - rollback_refactor.sh"
echo "  - MIGRATION_INFO.md"
echo ""
echo "💾 Backup en: $BACKUP_DIR"
echo "🔄 Para rollback: ./rollback_refactor.sh"
