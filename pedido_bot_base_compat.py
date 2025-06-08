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
