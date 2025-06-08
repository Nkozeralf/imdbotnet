# bot_executor.py - Ejecutor y coordinador del sistema
import os
import json
import time
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Importar núcleo del bot
from bot_core import ShopifyBotCore, NetworkProfiler
from rotador_proxy import obtener_proxy_colombiano_garantizado, estado_proxies
from notificador_telegram import enviar_resumen_telegram

logger = logging.getLogger("bot_executor")
logger.setLevel(logging.INFO)

if not logger.handlers:
    from logging.handlers import RotatingFileHandler
    handler = RotatingFileHandler("logs/bot_executor.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

@dataclass
class ExecutionTask:
    """Tarea de ejecución individual"""
    task_id: str
    store_id: str
    order_number: int
    scheduled_time: datetime
    proxy_config: Optional[Dict[str, str]] = None
    execution_mode: str = "standard"
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 2

@dataclass
class ExecutionStats:
    """Estadísticas de ejecución"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_summary: Dict[str, int] = field(default_factory=dict)

class IntelligentTaskManager:
    """Gestor inteligente de tareas"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.active_tasks: Dict[str, ExecutionTask] = {}
        self.completed_tasks: List[ExecutionTask] = []
        self.failed_tasks: List[ExecutionTask] = []
        self.task_queue: List[ExecutionTask] = []
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
    
    def create_tasks_from_config(self, stores: List[str], orders_per_store: int, use_intervals: bool = True) -> List[ExecutionTask]:
        """Crea tareas desde configuración"""
        tasks = []
        base_time = datetime.now()
        
        for store in stores:
            for order_num in range(1, orders_per_store + 1):
                if use_intervals:
                    import random
                    delay_seconds = random.uniform(60, 600)
                    scheduled_time = base_time + timedelta(seconds=len(tasks) * delay_seconds)
                else:
                    scheduled_time = base_time + timedelta(seconds=len(tasks) * 5)
                
                task = ExecutionTask(
                    task_id=f"{store}_{order_num}_{int(time.time())}",
                    store_id=store,
                    order_number=order_num,
                    scheduled_time=scheduled_time
                )
                
                tasks.append(task)
        
        tasks.sort(key=lambda t: t.scheduled_time)
        logger.info(f"📋 Creadas {len(tasks)} tareas para {len(stores)} tiendas")
        return tasks
    
    def execute_batch(self, tasks: List[ExecutionTask]) -> ExecutionStats:
        """Ejecuta lote de tareas"""
        self.task_queue = tasks.copy()
        stats = ExecutionStats(
            total_tasks=len(tasks),
            start_time=datetime.now()
        )
        
        logger.info("="*80)
        logger.info(f"🚀 INICIANDO EJECUCIÓN DE LOTE: {len(tasks)} tareas")
        logger.info("="*80)
        
        try:
            futures = []
            
            while self.task_queue or self.active_tasks or futures:
                while (len(self.active_tasks) < self.max_concurrent and 
                       self.task_queue and 
                       len(futures) < self.max_concurrent):
                    
                    task = self._get_next_ready_task()
                    if task:
                        future = self.executor.submit(self._execute_single_task, task)
                        futures.append((future, task))
                        self.active_tasks[task.task_id] = task
                        logger.info(f"🎯 Lanzando tarea: {task.task_id}")
                
                if futures:
                    completed_futures = []
                    for future, task in futures:
                        if future.done():
                            completed_futures.append((future, task))
                    
                    for future, task in completed_futures:
                        futures.remove((future, task))
                        self._handle_task_completion(future, task, stats)
                
                time.sleep(0.5)
            
            stats.end_time = datetime.now()
            self._finalize_stats(stats)
            
        except Exception as e:
            logger.error(f"❌ Error crítico: {e}")
        finally:
            self.executor.shutdown(wait=True)
        
        return stats
    
    def _get_next_ready_task(self) -> Optional[ExecutionTask]:
        """Obtiene siguiente tarea lista"""
        now = datetime.now()
        for i, task in enumerate(self.task_queue):
            if task.scheduled_time <= now:
                return self.task_queue.pop(i)
        return None
    
    def _execute_single_task(self, task: ExecutionTask) -> Dict[str, Any]:
        """Ejecuta una tarea individual"""
        task.start_time = datetime.now()
        task.status = "running"
        
        try:
            logger.info(f"🛒 EJECUTANDO: {task.task_id}")
            
            proxy_config = obtener_proxy_colombiano_garantizado(task.store_id)
            if not proxy_config:
                raise Exception("No se pudo obtener proxy colombiano")
            
            bot = ShopifyBotCore()
            result = bot.execute_order(
                store_id=task.store_id,
                proxy_config=proxy_config,
                execution_mode=task.execution_mode,
                debug=False
            )
            
            task.end_time = datetime.now()
            task.result = result
            
            if result["success"]:
                task.status = "completed"
                logger.info(f"✅ ÉXITO: {task.task_id} -> {result.get('order_id', 'N/A')}")
            else:
                task.status = "failed"
                logger.error(f"❌ FALLO: {task.task_id} -> {result['message']}")
            
            return result
            
        except Exception as e:
            task.end_time = datetime.now()
            task.status = "failed"
            logger.error(f"💥 ERROR: {task.task_id} -> {str(e)}")
            
            return {
                "success": False,
                "message": str(e),
                "store_id": task.store_id
            }
    
    def _handle_task_completion(self, future, task: ExecutionTask, stats: ExecutionStats):
        """Maneja finalización de tarea"""
        try:
            result = future.result()
            
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            if task.status == "completed":
                self.completed_tasks.append(task)
                stats.completed_tasks += 1
            else:
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = "pending"
                    task.scheduled_time = datetime.now() + timedelta(seconds=30 * task.retry_count)
                    self.task_queue.append(task)
                    logger.info(f"🔄 Reintentando: {task.task_id}")
                else:
                    self.failed_tasks.append(task)
                    stats.failed_tasks += 1
                    
                    error_type = self._classify_error(task.result.get("message", "") if task.result else "")
                    stats.error_summary[error_type] = stats.error_summary.get(error_type, 0) + 1
            
        except Exception as e:
            logger.error(f"❌ Error procesando tarea: {e}")
    
    def _classify_error(self, error_message: str) -> str:
        """Clasifica tipo de error"""
        if not error_message:
            return "unknown"
        
        error_lower = error_message.lower()
        
        if "timeout" in error_lower:
            return "timeout"
        elif "proxy" in error_lower or "ip" in error_lower:
            return "network"
        elif "popup" in error_lower or "formulario" in error_lower:
            return "interaction"
        elif "navegando" in error_lower:
            return "navigation"
        else:
            return "other"
    
    def _finalize_stats(self, stats: ExecutionStats):
        """Finaliza estadísticas"""
        if stats.total_tasks > 0:
            stats.success_rate = (stats.completed_tasks / stats.total_tasks) * 100

class BotOrchestrator:
    """Orquestador principal"""
    
    def __init__(self):
        self.task_manager = None
        
    def execute_batch_orders(self, stores: List[str], orders_per_store: int, **kwargs) -> ExecutionStats:
        """Ejecuta lote de pedidos"""
        
        if not stores:
            raise ValueError("Lista de tiendas vacía")
        
        if orders_per_store <= 0:
            raise ValueError("Número de pedidos debe ser mayor a 0")
        
        missing_stores = []
        for store in stores:
            if not store.startswith("http"):
                config_path = f"tiendas/{store}.json"
                if not os.path.exists(config_path):
                    missing_stores.append(store)
        
        if missing_stores:
            raise ValueError(f"Tiendas no encontradas: {', '.join(missing_stores)}")
        
        max_concurrent = kwargs.get("max_concurrent", 3)
        use_intervals = kwargs.get("use_intervals", True)
        
        self.task_manager = IntelligentTaskManager(max_concurrent=max_concurrent)
        
        tasks = self.task_manager.create_tasks_from_config(
            stores, 
            orders_per_store, 
            use_intervals
        )
        
        stats = self.task_manager.execute_batch(tasks)
        
        self._post_process_execution(stats, stores, kwargs)
        
        return stats
    
    def _post_process_execution(self, stats: ExecutionStats, stores: List[str], config: Dict[str, Any]):
        """Post-procesamiento"""
        try:
            if config.get("enable_telegram", True):
                self._send_telegram_notifications(stats, stores)
        except Exception as e:
            logger.error(f"❌ Error en post-procesamiento: {e}")
    
    def _send_telegram_notifications(self, stats: ExecutionStats, stores: List[str]):
        """Envía notificaciones"""
        try:
            if not self.task_manager:
                return
            
            store_results = {}
            
            for task in self.task_manager.completed_tasks:
                store_id = task.store_id
                if store_id not in store_results:
                    store_results[store_id] = {"exitosos": [], "fallidos": []}
                
                if task.result:
                    store_results[store_id]["exitosos"].append({
                        "exito": True,
                        "order_id": task.result.get("order_id", "N/A"),
                        "nombre": f"Cliente_{task.order_number}"
                    })
            
            for task in self.task_manager.failed_tasks:
                store_id = task.store_id
                if store_id not in store_results:
                    store_results[store_id] = {"exitosos": [], "fallidos": []}
                
                store_results[store_id]["fallidos"].append({
                    "exito": False,
                    "mensaje": task.result.get("message", "Error desconocido") if task.result else "Error de ejecución"
                })
            
            for store_id, results in store_results.items():
                try:
                    enviar_resumen_telegram(
                        store_id,
                        results["exitosos"],
                        results["fallidos"]
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Error enviando Telegram para {store_id}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error en notificaciones: {e}")

def ejecutar_pedido_coordinado(tienda_id: str, proxy_config: Optional[Dict[str, str]] = None, fast_mode: bool = False) -> Dict[str, Any]:
    """Función de interfaz pública"""
    from bot_core import ejecutar_pedido
    return ejecutar_pedido(tienda_id, proxy_config, fast_mode)

def ejecutar_lote_pedidos(tiendas: List[str], pedidos_por_tienda: int, **kwargs) -> Dict[str, Any]:
    """Función de interfaz para lotes"""
    
    orchestrator = BotOrchestrator()
    
    try:
        execution_mode = "fast" if kwargs.get("fast_mode", False) else "standard"
        
        stats = orchestrator.execute_batch_orders(
            stores=tiendas,
            orders_per_store=pedidos_por_tienda,
            execution_mode=execution_mode,
            use_intervals=kwargs.get("usar_intervalos", True),
            max_concurrent=kwargs.get("max_concurrent", 3),
            use_proxy_service=kwargs.get("usar_proxy_service", True),
            enable_telegram=kwargs.get("enable_telegram", True)
        )
        
        return {
            "exito": True,
            "total_programados": stats.total_tasks,
            "completados": stats.completed_tasks,
            "fallidos": stats.failed_tasks,
            "tasa_exito": stats.success_rate,
            "tiempo_ejecucion": (stats.end_time - stats.start_time).total_seconds() if stats.end_time and stats.start_time else 0,
            "errores_por_tipo": stats.error_summary
        }
        
    except Exception as e:
        logger.error(f"❌ Error en ejecución: {e}")
        return {
            "exito": False,
            "mensaje": str(e),
            "total_programados": 0,
            "completados": 0,
            "fallidos": 0,
            "tasa_exito": 0.0
        }

def get_system_status() -> Dict[str, Any]:
    """Obtiene estado del sistema"""
    try:
        proxy_status = estado_proxies()
        network_metrics = NetworkProfiler.measure_network_quality()
        
        tiendas_dir = "tiendas"
        available_stores = []
        if os.path.exists(tiendas_dir):
            available_stores = [f[:-5] for f in os.listdir(tiendas_dir) if f.endswith('.json')]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "proxy_system": proxy_status,
            "network_quality": {
                "latency_ms": network_metrics.current_latency,
                "quality": network_metrics.connection_quality,
                "timeout_multiplier": network_metrics.calculate_timeout_multiplier()
            },
            "available_stores": available_stores,
            "store_count": len(available_stores),
            "system_ready": len(available_stores) > 0 and proxy_status.get("dataimpulse", {}).get("available", False)
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "system_ready": False
        }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            logger.info("🧪 Test del sistema...")
            try:
                result = ejecutar_pedido_coordinado("diversytienda", fast_mode=True)
                print(f"Resultado: {result}")
            except Exception as e:
                print(f"Error: {e}")
                
        elif command == "status":
            status = get_system_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
            
        else:
            print(f"Comando desconocido: {command}")
    else:
        print("Bot Executor inicializado correctamente")
