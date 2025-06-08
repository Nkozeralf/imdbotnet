import os
import time
import logging
import logging.handlers
import random
from datetime import datetime, timedelta
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console

from limpiador_logs import limpiar_logs
from pedido_bot_base import ejecutar_pedido
from rotador_proxy import obtener_proxy, probar_proxy
from notificador_telegram import enviar_resumen_telegram

# ─── Configuración de logging optimizada ────────────────────────────────────────────────────
DIR_LOGS = "logs"
os.makedirs(DIR_LOGS, exist_ok=True)
logger = logging.getLogger("launcher_optimized")
logger.setLevel(logging.INFO)

# Filtro para reducir logs repetitivos
class LogFilter(logging.Filter):
    def filter(self, record):
        blocked_phrases = [
            "Tabla de progreso",
            "Actualizando tabla",
            "Refrescando estado"
        ]
        return not any(phrase in record.getMessage() for phrase in blocked_phrases)

file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(DIR_LOGS, "launcher_optimized.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
file_handler.addFilter(LogFilter())
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.addFilter(LogFilter())
logger.addHandler(console_handler)

# Constantes
TIENDAS_DIR = "tiendas"
VPN_SCRIPT_PATH = "surfshark/surfshark_rotate.sh"
PROXY_SERVICE_URL = "http://proxy-svc:8002"


class ProxyServiceClient:
    """Cliente optimizado para el servicio de proxy colombiano"""
    
    def __init__(self, service_url: str = PROXY_SERVICE_URL):
        self.service_url = service_url
        self.session = requests.Session()
        
    def get_proxy(self, session_id: str = None, force_new: bool = False) -> dict:
        """Obtener proxy del servicio"""
        try:
            response = self.session.post(
                f"{self.service_url}/get-proxy",
                json={
                    "session_id": session_id,
                    "force_new": force_new
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "server": data["proxy"],
                    "username": None,
                    "password": None,
                    "session_id": data["session_id"],
                    "country": data["country"]
                }
            else:
                logger.error(f"Error del servicio proxy: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error conectando al servicio proxy: {e}")
            return None
    
    def get_stats(self) -> dict:
        """Obtener estadísticas del servicio"""
        try:
            response = self.session.get(f"{self.service_url}/stats", timeout=5)
            return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    def test_service(self) -> bool:
        """Probar disponibilidad del servicio"""
        try:
            response = self.session.get(f"{self.service_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


class OptimizedOrderManager:
    """Gestor optimizado de pedidos respetando el flujo VPN → Proxy → Navegación"""
    
    def __init__(self):
        self.completed_orders = []
        self.failed_orders = []
        self.proxy_client = ProxyServiceClient()
        self.console = Console()
        
    def execute_orders(self, tiendas: list, pedidos_por_tienda: int, usar_proxy_service: bool = True, fast_mode: bool = False, usar_intervalos: bool = True):
        """Ejecutar pedidos con logs optimizados"""
        
        # Crear lista de tareas
        scheduled_tasks = []
        
        for tienda in tiendas:
            for i in range(pedidos_por_tienda):
                if usar_intervalos:
                    delay_minutes = random.uniform(1, 10)
                    delay_seconds = delay_minutes * 60
                    scheduled_time = datetime.now() + timedelta(seconds=delay_seconds)
                else:
                    base_delay = len(scheduled_tasks) * 5
                    delay_seconds = base_delay
                    scheduled_time = datetime.now() + timedelta(seconds=delay_seconds)
                
                task = {
                    'id': f"{tienda}_{i+1}",
                    'tienda': tienda,
                    'pedido_num': i + 1,
                    'scheduled_time': scheduled_time,
                    'usar_proxy_service': usar_proxy_service,
                    'fast_mode': fast_mode,
                    'status': 'pending'
                }
                
                scheduled_tasks.append(task)
        
        scheduled_tasks.sort(key=lambda x: x['scheduled_time'])
        
        logger.info("=" * 80)
        logger.info(f"🚀 INICIANDO EJECUCIÓN DE {len(scheduled_tasks)} PEDIDOS")
        logger.info(f"📊 Modo: {'Intervalos variables' if usar_intervalos else 'Inmediato'}")
        logger.info(f"🌐 Proxy: {'Servicio colombiano' if usar_proxy_service else 'DataImpulse'}")
        logger.info(f"⚡ Fast mode: {'Sí' if fast_mode else 'No'}")
        logger.info("=" * 80)
        
        # Ejecutar tareas
        self._execute_tasks_optimized(scheduled_tasks)
        
        # Resumen final
        self._log_final_summary()
    
    def _execute_tasks_optimized(self, tasks: list):
        """Ejecutar tareas con logs lineales optimizados"""
        
        def execute_single_task(task):
            """Ejecutar una tarea individual con logs estructurados"""
            
            # Esperar hasta tiempo programado
            now = datetime.now()
            if task['scheduled_time'] > now:
                sleep_time = (task['scheduled_time'] - now).total_seconds()
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            task['start_time'] = datetime.now()
            
            # Header del pedido
            self._log_order_header(task)
            
            try:
                # 1. Obtener proxy PRIMERO (respetando flujo original)
                proxy_config = self._get_proxy_for_task(task)
                
                if not proxy_config:
                    raise Exception("No se pudo obtener proxy colombiano válido")
                
                # 2. Log de configuración proxy
                self._log_proxy_config(task, proxy_config)
                
                # 3. Ejecutar pedido (que internamente verificará IP colombiana)
                logger.info(f"🛒 [{task['id']}] Ejecutando pedido con proxy colombiano...")
                
                result = ejecutar_pedido(
                    tienda_id=task['tienda'],
                    proxy_config=proxy_config,
                    fast_mode=task['fast_mode']
                )
                
                # 4. Procesar resultado
                task['result'] = result
                task['end_time'] = datetime.now()
                execution_time = (task['end_time'] - task['start_time']).total_seconds()
                
                if result['exito']:
                    task['status'] = 'completed'
                    self.completed_orders.append(task)
                    self._log_success(task, result, execution_time)
                else:
                    task['status'] = 'failed'
                    self.failed_orders.append(task)
                    self._log_failure(task, result, execution_time)
                
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                task['end_time'] = datetime.now()
                execution_time = (task['end_time'] - task['start_time']).total_seconds()
                self.failed_orders.append(task)
                self._log_error(task, e, execution_time)
            
            # Footer del pedido
            self._log_order_footer(task)
        
        # Ejecutar en paralelo con ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_single_task, task) for task in tasks]
            
            # Esperar a que terminen todas las tareas
            for future in futures:
                future.result()
        
        logger.info("🏁 Todos los pedidos han sido procesados")
    
    def _get_proxy_for_task(self, task: dict) -> dict:
        """Obtener proxy para una tarea específica - RESPETANDO FLUJO ORIGINAL"""
        
        # RESPETAMOS TU FLUJO: VPN ya está activa, ahora obtener proxy colombiano
        if task['usar_proxy_service']:
            logger.info(f"🇨🇴 [{task['id']}] Intentando servicio proxy colombiano...")
            proxy_config = self.proxy_client.get_proxy()
            if proxy_config:
                # Verificar que sea colombiano
                if proxy_config.get("country", "").upper() == "CO":
                    logger.info(f"✅ [{task['id']}] Proxy servicio colombiano obtenido")
                    return proxy_config
                else:
                    logger.warning(f"⚠️ [{task['id']}] Servicio retornó país {proxy_config.get('country')}, no CO")
            
            logger.warning(f"⚠️ [{task['id']}] Proxy service falló, usando DataImpulse")
        
        # Fallback a DataImpulse (que YA verifica IP colombiana internamente)
        logger.info(f"🔄 [{task['id']}] Usando DataImpulse como fallback...")
        proxy_config = obtener_proxy("CO")
        
        if proxy_config:
            logger.info(f"✅ [{task['id']}] Proxy DataImpulse obtenido")
            return proxy_config
        else:
            logger.error(f"❌ [{task['id']}] No se pudo obtener proxy colombiano")
            return None
    
    def _log_order_header(self, task: dict):
        """Log de inicio de pedido"""
        logger.info("┌" + "─" * 78 + "┐")
        logger.info(f"│ 🚀 PEDIDO {task['id']:<20} | TIENDA: {task['tienda']:<30} │")
        logger.info(f"│ ⏰ INICIO: {task['start_time'].strftime('%H:%M:%S'):<66} │")
        logger.info("├" + "─" * 78 + "┤")
    
    def _log_proxy_config(self, task: dict, proxy_config: dict):
        """Log de configuración de proxy"""
        proxy_type = "Servicio CO" if 'session_id' in proxy_config else "DataImpulse"
        proxy_info = proxy_config.get('session_id', proxy_config.get('server', 'N/A'))
        detected_ip = proxy_config.get('detected_ip', 'N/A')
        
        logger.info(f"│ 🌐 PROXY: {proxy_type:<10} | INFO: {str(proxy_info):<45} │")
        if detected_ip != 'N/A':
            logger.info(f"│ 🇨🇴 IP PROXY: {detected_ip:<62} │")
        logger.info("├" + "─" * 78 + "┤")
    
    def _log_success(self, task: dict, result: dict, execution_time: float):
        """Log de pedido exitoso"""
        order_id = result.get('order_id', 'N/A')
        nombre = result.get('nombre', 'N/A')
        
        logger.info(f"│ ✅ ÉXITO | ORDER: {order_id:<20} | CLIENTE: {nombre:<25} │")
        logger.info(f"│ ⏱️  TIEMPO: {execution_time:.1f}s{'':<59} │")
    
    def _log_failure(self, task: dict, result: dict, execution_time: float):
        """Log de pedido fallido"""
        mensaje = result.get('mensaje', 'Error desconocido')[:50]
        
        logger.error(f"│ ❌ FALLO | ERROR: {mensaje:<55} │")
        logger.error(f"│ ⏱️  TIEMPO: {execution_time:.1f}s{'':<59} │")
    
    def _log_error(self, task: dict, error: Exception, execution_time: float):
        """Log de error de ejecución"""
        error_msg = str(error)[:50]
        
        logger.error(f"│ 💥 ERROR | {error_msg:<62} │")
        logger.error(f"│ ⏱️  TIEMPO: {execution_time:.1f}s{'':<59} │")
    
    def _log_order_footer(self, task: dict):
        """Log de fin de pedido"""
        logger.info("└" + "─" * 78 + "┘")
        logger.info("")  # Línea en blanco para separar pedidos
    
    def _log_final_summary(self):
        """Log de resumen final optimizado"""
        total = len(self.completed_orders) + len(self.failed_orders)
        success_rate = (len(self.completed_orders) / max(total, 1)) * 100
        
        logger.info("=" * 80)
        logger.info("🎯 RESUMEN FINAL DE EJECUCIÓN")
        logger.info("=" * 80)
        logger.info(f"📊 Total pedidos: {total}")
        logger.info(f"✅ Exitosos: {len(self.completed_orders)}")
        logger.info(f"❌ Fallidos: {len(self.failed_orders)}")
        logger.info(f"📈 Tasa de éxito: {success_rate:.1f}%")
        
        if self.completed_orders:
            logger.info("\n🎉 PEDIDOS EXITOSOS:")
            for order in self.completed_orders:
                result = order.get('result', {})
                order_id = result.get('order_id', 'N/A')
                nombre = result.get('nombre', 'N/A')
                logger.info(f"  • {order['id']} → {order_id} ({nombre})")
        
        if self.failed_orders:
            logger.info("\n💥 PEDIDOS FALLIDOS:")
            for order in self.failed_orders:
                error = order.get('error', order.get('result', {}).get('mensaje', 'Error desconocido'))
                logger.info(f"  • {order['id']} → {error[:60]}")
        
        logger.info("=" * 80)
    
    def get_summary(self) -> dict:
        """Obtener resumen de resultados"""
        total = len(self.completed_orders) + len(self.failed_orders)
        return {
            'total_programados': total,
            'completados': len(self.completed_orders),
            'fallidos': len(self.failed_orders),
            'tasa_exito': (len(self.completed_orders) / max(total, 1)) * 100,
            'pedidos_exitosos': self.completed_orders,
            'pedidos_fallidos': self.failed_orders
        }


# ─── Funciones auxiliares optimizadas ────────────────────────────────────────────────────

def listar_tiendas() -> list:
    """Retorna lista de IDs de tiendas"""
    if not os.path.isdir(TIENDAS_DIR):
        return []
    return [f[:-5] for f in os.listdir(TIENDAS_DIR) if f.endswith('.json')]


def verificar_url_tienda(tienda_id: str) -> bool:
    """Verifica que la URL de la tienda responda correctamente"""
    try:
        from pedido_bot_base import cargar_configuracion_tienda
        config = cargar_configuracion_tienda(tienda_id)
        url = config.get('url_producto') or config.get('url')
        if not url:
            return False
            
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        response = requests.head(base_url, timeout=10, allow_redirects=True)
        return response.status_code < 400
    except Exception:
        return False


def rotar_vpn():
    """Ejecuta script de rotación de VPN si existe - RESPETANDO TU FLUJO ORIGINAL"""
    if os.path.exists(VPN_SCRIPT_PATH):
        logger.info("🔁 Rotando IP pública con Surfshark VPN...")
        os.system(f"sudo bash {VPN_SCRIPT_PATH}")
        logger.info("⏳ Esperando estabilización de red post-VPN...")
        time.sleep(8)
        
        # Log de IP después de VPN (solo informativo)
        try:
            ip_post_vpn = requests.get("https://api.ipify.org", timeout=5).text
            logger.info(f"🌐 IP post-VPN: {ip_post_vpn}")
        except:
            logger.info("🌐 IP post-VPN: No se pudo verificar")
    else:
        logger.warning(f"Script de VPN no encontrado: {VPN_SCRIPT_PATH}")


def validate_network_basic():
    """Validación básica de red - SIN abortar por IP"""
    try:
        # Solo verificar conectividad básica
        test_ip = requests.get("https://api.ipify.org", timeout=5).text
        logger.info(f"🌐 Conectividad verificada - IP base: {test_ip}")
        return True
    except Exception as e:
        logger.error(f"❌ Error de conectividad básica: {e}")
        return False


# ─── Función principal CORREGIDA ────────────────────────────────────────────────────

def main():
    console = Console()

    console.print("\n[bold blue]🚀 Launcher Optimizado - Flujo de Seguridad Corregido[/]")
    console.print("[dim]Versión 3.1 - Respeta VPN → Proxy → Navegación[/]\n")

    # 1) Limpiar logs
    respuesta = input("¿Deseas limpiar logs y capturas anteriores? (s/n): ").strip().lower()
    if respuesta == 's':
        limpiar_logs(confirmado=True)
        logger.info("✔️ Logs y capturas eliminados")

    # 2) Listar tiendas disponibles
    tiendas = listar_tiendas()
    if not tiendas:
        console.print("[red]No hay tiendas en 'tiendas/'[/]")
        return

    console.print("\n[bold]Tiendas disponibles:[/]")
    for idx, tienda in enumerate(tiendas, start=1):
        console.print(f"  {idx}. {tienda}")

    # 3) Selección de tiendas
    sel = input("\nSelecciona tiendas (ej: 1,2 o 'all' para todas): ").strip()
    
    if sel.lower() == 'all':
        escogidas = tiendas.copy()
    else:
        escogidas = []
        for part in sel.split(','):
            if part.isdigit():
                i = int(part) - 1
                if 0 <= i < len(tiendas):
                    escogidas.append(tiendas[i])
    
    if not escogidas:
        console.print("[red]Selección inválida[/]")
        return

    # 4) Configuración de pedidos
    try:
        n = int(input("¿Cuántos pedidos deseas generar por tienda?: ").strip())
        if n <= 0:
            raise ValueError()
    except ValueError:
        console.print("[red]Número de pedidos inválido[/]")
        return

    # 5) Opciones
    usar_proxy_service = input("¿Usar servicio de proxy colombiano? (s/n): ").strip().lower() == 's'
    fast_mode = input("¿Activar modo rápido (sin imágenes ni delays)? (s/n): ").strip().lower() == 's'
    
    total_pedidos = len(escogidas) * n
    usar_intervalos = False
    
    if total_pedidos > 10:
        usar_intervalos = input("¿Usar intervalos aleatorios entre pedidos (1-10 min)? (s/n): ").strip().lower() == 's'
    else:
        respuesta = input(f"Solo {total_pedidos} pedidos. ¿Usar intervalos aleatorios (1-10 min) o ejecutar inmediatamente? (intervalos/inmediato): ").strip().lower()
        usar_intervalos = respuesta.startswith('i') == False and respuesta.startswith('inm') == False

    # 6) Mostrar configuración
    console.print(f"\n[bold green]Configuración:[/]")
    console.print(f"  📦 Tiendas: {', '.join(escogidas)}")
    console.print(f"  🔢 Pedidos por tienda: {n}")
    console.print(f"  🌐 Proxy service: {'Sí' if usar_proxy_service else 'No'}")
    console.print(f"  ⚡ Modo rápido: {'Sí' if fast_mode else 'No'}")
    console.print(f"  📊 Total pedidos: {total_pedidos}")
    console.print(f"  ⏱️ Intervalos: {'Sí (1-10 min)' if usar_intervalos else 'No (inmediato)'}")

    if input("\n¿Continuar? (s/n): ").strip().lower() != 's':
        return

    # 7) Verificar tiendas
    console.print("\n[bold]🔍 Verificando tiendas...[/]")
    tiendas_validas = []
    for tienda in escogidas:
        if verificar_url_tienda(tienda):
            tiendas_validas.append(tienda)
            console.print(f"  ✅ {tienda}")
        else:
            console.print(f"  ❌ {tienda} - No disponible")

    if not tiendas_validas:
        console.print("[red]❌ Ninguna tienda está disponible[/]")
        return

    escogidas = tiendas_validas

    # 8) FLUJO CORRECTO: VPN PRIMERO
    console.print("\n[bold]🔒 Iniciando flujo de seguridad...[/]")
    rotar_vpn()

    # 9) Verificar proxy service si se seleccionó
    if usar_proxy_service:
        proxy_client = ProxyServiceClient()
        if proxy_client.test_service():
            stats = proxy_client.get_stats()
            if stats:
                console.print(f"\n[bold green]📊 Proxy Service Stats:[/]")
                console.print(f"  • Datos restantes: {stats.get('remaining_gb', 'N/A')} GB")
                console.print(f"  • Success rate: {stats.get('success_rate', 'N/A')}%")
        else:
            console.print("[yellow]⚠️ No se pudo conectar al Proxy Service, usando DataImpulse[/]")
            usar_proxy_service = False

    # 10) Validación básica de red (SIN abortar por IP)
    logger.info("🌐 Validando conectividad básica...")
    if not validate_network_basic():
        console.print("[red]❌ Problemas de conectividad básica[/]")
        return

    # 11) Ejecutar pedidos - La verificación IP colombiana se hace EN CADA PEDIDO
    console.print(f"\n[bold blue]🚀 Iniciando ejecución con flujo de seguridad...[/]")
    console.print("[dim]Flujo: VPN → Proxy Colombiano → Verificación IP → Navegación[/]")
    
    order_manager = OptimizedOrderManager()
    
    try:
        order_manager.execute_orders(
            tiendas=escogidas,
            pedidos_por_tienda=n,
            usar_proxy_service=usar_proxy_service,
            fast_mode=fast_mode,
            usar_intervalos=usar_intervalos
        )
        
        # 12) Resumen final con Rich
        summary = order_manager.get_summary()
        
        from rich.table import Table
        table = Table(title="Resumen Final de Pedidos")
        table.add_column("Métrica", justify="left")
        table.add_column("Valor", justify="center")
        
        table.add_row("Total programados", str(summary['total_programados']))
        table.add_row("Completados exitosamente", f"✅ {summary['completados']}")
        table.add_row("Fallidos", f"❌ {summary['fallidos']}")
        table.add_row("Tasa de éxito", f"{summary['tasa_exito']:.1f}%")
        
        console.print("\n")
        console.print(table)
        
        # 13) Notificaciones Telegram
        for tienda in escogidas:
            pedidos_tienda = [p for p in summary['pedidos_exitosos'] if p['tienda'] == tienda]
            fallidos_tienda = [p for p in summary['pedidos_fallidos'] if p['tienda'] == tienda]
            
            exitosos = [{'exito': True, 'order_id': p.get('result', {}).get('order_id'), 'nombre': p.get('result', {}).get('nombre', 'N/A')} for p in pedidos_tienda]
            fallidos = [{'exito': False, 'mensaje': p.get('result', {}).get('mensaje', p.get('error', 'Error desconocido'))} for p in fallidos_tienda]
            
            if exitosos or fallidos:
                enviar_resumen_telegram(tienda, exitosos, fallidos)
        
        logger.info(f"✅ Proceso completado - {summary['completados']}/{summary['total_programados']} pedidos exitosos")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Proceso interrumpido por el usuario[/]")
        logger.info("Proceso interrumpido por el usuario")
    except Exception as e:
        console.print(f"\n[red]❌ Error inesperado: {str(e)}[/]")
        logger.error(f"Error inesperado: {str(e)}")


if __name__ == '__main__':
    main()
