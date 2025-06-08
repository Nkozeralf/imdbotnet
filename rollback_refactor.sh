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

rm -f bot_core.py bot_executor.py pedido_bot_base_compat.py launcher_optimized.py

echo "✅ Rollback completado"
echo "⚠️  Reinicia los servicios que estén corriendo"
