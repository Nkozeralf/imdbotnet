# bot_core.py - Núcleo del Bot Refactorizado
import os
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Response
from urllib.parse import urlparse, urljoin

# Importaciones del sistema actual
from rotador_proxy import obtener_proxy_colombiano_garantizado, probar_proxy
from data_generator import generar_datos
from verificador_formulario import formulario_completo

# Configuración de logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("bot_core")
logger.setLevel(logging.INFO)

if not logger.handlers:
    from logging.handlers import RotatingFileHandler
    handler = RotatingFileHandler(f"{LOG_DIR}/bot_core.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

@dataclass
class NetworkMetrics:
    """Métricas de red para calibración dinámica de timeouts"""
    baseline_latency: float = 0.0
    current_latency: float = 0.0
    connection_quality: str = "unknown"
    
    def calculate_timeout_multiplier(self) -> float:
        """Calcula multiplicador de timeout basado en condiciones de red"""
        if self.current_latency > 2000:
            return 3.0
        elif self.current_latency > 1000:
            return 2.0
        elif self.current_latency > 500:
            return 1.5
        else:
            return 1.0

@dataclass
class StoreProfile:
    """Perfil de tienda con detección automática"""
    store_id: str
    base_url: str
    platform_type: str = "shopify"
    form_framework: str = "unknown"
    detected_fields: Dict[str, str] = field(default_factory=dict)

class AdaptiveTimeoutManager:
    """Gestor de timeouts que se adapta a condiciones de red"""
    
    BASE_TIMEOUTS = {
        "navigation": 30000,
        "element_wait": 20000,
        "popup_wait": 25000,
        "form_submit": 45000,
        "page_load": 35000
    }
    
    def __init__(self, network_metrics: NetworkMetrics):
        self.network_metrics = network_metrics
        self.multiplier = network_metrics.calculate_timeout_multiplier()
        logger.info(f"🕒 Timeout multiplier: {self.multiplier:.2f}x")
    
    def get_timeout(self, operation: str) -> int:
        """Obtiene timeout adaptativo para una operación"""
        base = self.BASE_TIMEOUTS.get(operation, 20000)
        adaptive = int(base * self.multiplier)
        min_timeout = base * 0.5
        max_timeout = base * 4.0
        return max(min_timeout, min(adaptive, max_timeout))

class ShopifyDetector:
    """Detector automático de estructuras de tienda Shopify"""
    
    COMMON_PATTERNS = {
        "releasit_cod": {
            "popup_triggers": [
                "._rsi-buy-now-button",
                "button[aria-label*='PAGAR EN CASA']",
                "button[aria-label*='PAGAR CONTRAENTREGA']"
            ],
            "form_containers": [
                "#_rsi-cod-form-modal-form",
                "._rsi-cod-form"
            ],
            "common_fields": {
                "first_name": ["#_rsi-field-first_name"],
                "last_name": ["#_rsi-field-last_name"],
                "email": ["#_rsi-field-email"],
                "phone": ["#_rsi-field-phone"],
                "address": ["#_rsi-field-address"]
            }
        }
    }
    
    @classmethod
    def detect_store_structure(cls, page: Page, base_url: str) -> StoreProfile:
        """Detecta automáticamente la estructura de una tienda"""
        store_id = urlparse(base_url).netloc.replace("www.", "")
        profile = StoreProfile(store_id=store_id, base_url=base_url)
        
        try:
            page_content = page.content()
            
            if "_rsi" in page_content or "releasit" in page_content.lower():
                profile.form_framework = "releasit"
                cls._detect_releasit_fields(page, profile)
            else:
                profile.form_framework = "native"
            
            logger.info(f"🔍 Detección: {profile.platform_type}/{profile.form_framework}")
            
        except Exception as e:
            logger.error(f"❌ Error en detección: {e}")
        
        return profile
    
    @classmethod
    def _detect_releasit_fields(cls, page: Page, profile: StoreProfile):
        """Detecta campos específicos de Releasit COD"""
        patterns = cls.COMMON_PATTERNS["releasit_cod"]
        
        for field_name, selectors in patterns["common_fields"].items():
            for selector in selectors:
                try:
                    if page.locator(selector).count() > 0:
                        profile.detected_fields[field_name] = selector
                        break
                except:
                    continue

class NetworkProfiler:
    """Perfilador de red para calibración automática"""
    
    @staticmethod
    def measure_network_quality(proxy_config: Optional[Dict[str, str]] = None) -> NetworkMetrics:
        """Mide calidad de red y latencias"""
        metrics = NetworkMetrics()
        
        try:
            test_endpoints = ["https://www.shopify.com", "https://api.ipify.org"]
            latencies = []
            
            session = requests.Session()
            if proxy_config and proxy_config.get("server"):
                session.proxies = {"http": proxy_config["server"], "https": proxy_config["server"]}
            
            for endpoint in test_endpoints:
                try:
                    start = time.time()
                    response = session.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        latency = (time.time() - start) * 1000
                        latencies.append(latency)
                except:
                    continue
            
            if latencies:
                metrics.current_latency = sum(latencies) / len(latencies)
                
                if metrics.current_latency < 200:
                    metrics.connection_quality = "excellent"
                elif metrics.current_latency < 500:
                    metrics.connection_quality = "good"
                elif metrics.current_latency < 1000:
                    metrics.connection_quality = "fair"
                else:
                    metrics.connection_quality = "poor"
                
                logger.info(f"📊 Red: {metrics.current_latency:.0f}ms ({metrics.connection_quality})")
            else:
                metrics.current_latency = 1000
                metrics.connection_quality = "poor"
                
        except Exception as e:
            logger.error(f"❌ Error midiendo red: {e}")
            metrics.current_latency = 1500
            metrics.connection_quality = "poor"
        
        return metrics

class ShopifyBotCore:
    """Núcleo principal del bot Shopify con capacidades avanzadas"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    def execute_order(self, store_id: str, proxy_config: Optional[Dict[str, str]] = None, execution_mode: str = "standard", debug: bool = False) -> Dict[str, Any]:
        """Método principal de ejecución de pedidos"""
        
        start_time = time.time()
        result = {
            "store_id": store_id,
            "success": False,
            "message": "",
            "order_id": None,
            "execution_time": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            logger.info("="*60)
            logger.info(f"🛒 INICIANDO PEDIDO: {store_id}")
            logger.info("="*60)
            
            # 1. Configurar contexto
            if not self._setup_context(store_id, proxy_config, execution_mode):
                result["message"] = "Error en configuración"
                return result
            
            # 2. Verificar IP colombiana
            ip_check = self._verify_colombian_ip()
            if not ip_check["valid"]:
                result["message"] = f"IP no colombiana: {ip_check['ip']}"
                return result
            
            logger.info(f"🇨🇴 IP colombiana confirmada: {ip_check['ip']}")
            
            # 3. Navegación y procesamiento
            if not self._navigate_to_store():
                result["message"] = "Error navegando al producto"
                return result
            
            # 4. Procesar pedido
            order_result = self._process_order_flow()
            result.update(order_result)
            
            if result["success"]:
                logger.info(f"✅ PEDIDO EXITOSO: {result.get('order_id', 'N/A')}")
            else:
                logger.error(f"❌ PEDIDO FALLIDO: {result['message']}")
                
        except Exception as e:
            result["message"] = f"Error crítico: {str(e)}"
            logger.error(f"💥 Error crítico: {e}")
        
        finally:
            self._cleanup()
            result["execution_time"] = time.time() - start_time
            logger.info(f"⏱️ Tiempo total: {result['execution_time']:.2f}s")
        
        return result
    
    def _setup_context(self, store_id: str, proxy_config: Optional[Dict[str, str]], execution_mode: str) -> bool:
        """Configura el contexto de ejecución"""
        try:
            # Determinar URL
            if store_id.startswith("http"):
                self.base_url = store_id
                self.store_id = urlparse(store_id).netloc.replace("www.", "")
            else:
                config_path = f"tiendas/{store_id}.json"
                if not os.path.exists(config_path):
                    logger.error(f"Configuración no encontrada: {config_path}")
                    return False
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.base_url = config.get("url_producto") or config.get("url")
                self.store_id = store_id
                self.store_config = config
            
            # Validar proxy
            if not proxy_config:
                proxy_config = obtener_proxy_colombiano_garantizado(self.store_id)
            
            if not proxy_config or not probar_proxy(proxy_config):
                logger.error("Proxy no válido")
                return False
            
            self.proxy_config = proxy_config
            
            # Medir red y crear timeout manager
            network_metrics = NetworkProfiler.measure_network_quality(proxy_config)
            self.timeout_manager = AdaptiveTimeoutManager(network_metrics)
            
            # Generar datos del cliente
            self.customer_data = generar_datos()
            
            logger.info(f"🎯 Contexto configurado - Cliente: {self.customer_data['nombre']} {self.customer_data['apellido']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando contexto: {e}")
            return False
    
    def _create_browser_session(self) -> bool:
        """Crea sesión de navegador"""
        try:
            self.playwright = sync_playwright().start()
            
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
            
            self.browser = self.playwright.chromium.launch(headless=True, args=browser_args)
            
            context_config = {
                "locale": "es-CO",
                "timezone_id": "America/Bogota",
                "ignore_https_errors": True,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080}
            }
            
            if self.proxy_config and self.proxy_config.get("server"):
                proxy_settings = {"server": self.proxy_config["server"]}
                if self.proxy_config.get("username"):
                    proxy_settings.update({
                        "username": self.proxy_config["username"],
                        "password": self.proxy_config["password"]
                    })
                context_config["proxy"] = proxy_settings
            
            self.context = self.browser.new_context(**context_config)
            self.page = self.context.new_page()
            
            # Configurar timeouts
            self.page.set_default_timeout(self.timeout_manager.get_timeout("element_wait"))
            self.page.set_default_navigation_timeout(self.timeout_manager.get_timeout("navigation"))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando navegador: {e}")
            return False
    
    def _verify_colombian_ip(self) -> Dict[str, Any]:
        """Verifica que la IP sea colombiana"""
        if not self._create_browser_session():
            return {"valid": False, "ip": "unknown"}
        
        ip_services = ["https://httpbin.org/ip", "https://api.ipify.org?format=json"]
        
        for service in ip_services:
            try:
                response = self.page.goto(service, timeout=15000)
                if not response or response.status != 200:
                    continue
                
                time.sleep(1)
                ip_data = self.page.evaluate("() => document.body.innerText")
                data = json.loads(ip_data)
                
                ip = data.get("ip") or data.get("origin", "").split(",")[0].strip()
                if not ip:
                    continue
                
                # Verificar si es colombiana (simplificado)
                try:
                    geo_response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
                    if geo_response.status_code == 200:
                        geo_data = geo_response.json()
                        is_colombian = geo_data.get('countryCode', '').upper() == 'CO'
                        return {"valid": is_colombian, "ip": ip}
                except:
                    pass
                
                return {"valid": True, "ip": ip}  # Asumir válida si no se puede verificar
                
            except Exception as e:
                continue
        
        return {"valid": True, "ip": "unknown"}  # No bloquear si no se puede verificar
    
    def _navigate_to_store(self) -> bool:
        """Navega a la tienda"""
        try:
            logger.info(f"🌐 Navegando a: {self.base_url}")
            
            response = self.page.goto(self.base_url, timeout=self.timeout_manager.get_timeout("navigation"))
            if response and response.status >= 400:
                logger.error(f"HTTP {response.status}")
                return False
            
            time.sleep(3)
            logger.info("✅ Navegación exitosa")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error navegando: {e}")
            return False
    
    def _process_order_flow(self) -> Dict[str, Any]:
        """Procesa el flujo completo de pedido"""
        try:
            # 1. Detectar estructura
            self.store_profile = ShopifyDetector.detect_store_structure(self.page, self.base_url)
            
            # 2. Abrir popup
            if not self._handle_popup():
                return {"success": False, "message": "Error abriendo popup"}
            
            # 3. Llenar formulario
            if not self._fill_form():
                return {"success": False, "message": "Error llenando formulario"}
            
            # 4. Enviar
            return self._submit_form()
            
        except Exception as e:
            return {"success": False, "message": f"Error en flujo: {str(e)}"}
    
    def _handle_popup(self) -> bool:
        """Maneja apertura de popup"""
        try:
            # Usar configuración específica o detectar automáticamente
            if hasattr(self, 'store_config') and self.store_config.get("boton_popup"):
                popup_selector = self.store_config["boton_popup"]
            else:
                # Buscar patrones comunes
                popup_patterns = ShopifyDetector.COMMON_PATTERNS["releasit_cod"]["popup_triggers"]
                popup_selector = None
                
                for pattern in popup_patterns:
                    try:
                        if self.page.locator(pattern).count() > 0:
                            popup_selector = pattern
                            break
                    except:
                        continue
            
            if not popup_selector:
                logger.error("No se encontró botón de popup")
                return False
            
            logger.info(f"🎯 Abriendo popup: {popup_selector}")
            
            timeout = self.timeout_manager.get_timeout("popup_wait")
            self.page.wait_for_selector(popup_selector, timeout=timeout, state="visible")
            
            element = self.page.locator(popup_selector).first
            element.scroll_into_view_if_needed()
            time.sleep(0.5)
            element.click()
            
            # Esperar formulario
            time.sleep(2)
            logger.info("✅ Popup abierto")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error con popup: {e}")
            return False
    
    def _fill_form(self) -> bool:
        """Llena formulario de forma inteligente"""
        try:
            logger.info("📝 Llenando formulario...")
            
            # Usar campos detectados o configuración específica
            if hasattr(self, 'store_config') and self.store_config.get("campos"):
                field_mapping = self.store_config["campos"]
            else:
                # Mapeo por defecto
                field_mapping = {
                    "#_rsi-field-first_name": "nombre",
                    "#_rsi-field-last_name": "apellido",
                    "#_rsi-field-email": "email",
                    "#_rsi-field-phone": "telefono",
                    "#_rsi-field-address": "direccion"
                }
            
            filled_count = 0
            total_fields = len(field_mapping)
            
            for selector, field_type in field_mapping.items():
                try:
                    value = self.customer_data.get(field_type)
                    if value and self._fill_field(selector, str(value)):
                        filled_count += 1
                except Exception as e:
                    logger.debug(f"Error llenando {selector}: {e}")
                    continue
            
            # Manejar selects de ubicación si existen
            if hasattr(self, 'store_config'):
                self._handle_location_selects()
            
            # Checkbox si existe
            self._handle_checkbox()
            
            success_rate = (filled_count / max(total_fields, 1)) * 100
            logger.info(f"📊 Formulario: {filled_count}/{total_fields} ({success_rate:.1f}%)")
            
            return success_rate >= 70
            
        except Exception as e:
            logger.error(f"❌ Error llenando formulario: {e}")
            return False
    
    def _fill_field(self, selector: str, value: str) -> bool:
        """Llena un campo individual"""
        try:
            timeout = self.timeout_manager.get_timeout("element_wait")
            self.page.wait_for_selector(selector, timeout=timeout, state="visible")
            
            element = self.page.locator(selector).first
            element.clear()
            time.sleep(0.1)
            element.fill(value)
            
            return True
            
        except Exception:
            return False
    
    def _handle_location_selects(self):
        """Maneja selects de departamento y ciudad"""
        try:
            selects = self.store_config.get("selects", [])
            departamentos = self.store_config.get("departamento_valores", ["ANT", "CUN", "VAC"])
            
            for select_config in selects:
                selector = select_config["selector"]
                valor = select_config["valor"]
                
                if valor == "departamento":
                    import random
                    dept = random.choice(departamentos)
                    self._select_option(selector, dept)
                    time.sleep(2)  # Esperar carga de ciudades
                elif valor == "ciudad":
                    self._select_first_available_city(selector)
                    
        except Exception as e:
            logger.debug(f"Error en selects de ubicación: {e}")
    
    def _select_option(self, selector: str, value: str) -> bool:
        """Selecciona opción en un select"""
        try:
            element = self.page.locator(selector).first
            element.select_option(value)
            return True
        except:
            return False
    
    def _select_first_available_city(self, selector: str):
        """Selecciona primera ciudad disponible"""
        try:
            time.sleep(1)
            options = self.page.query_selector_all(f'{selector} option')
            for option in options[1:]:  # Skip first (usually empty)
                value = option.get_attribute("value")
                if value and value.strip():
                    self.page.locator(selector).first.select_option(value)
                    break
        except Exception as e:
            logger.debug(f"Error seleccionando ciudad: {e}")
    
    def _handle_checkbox(self):
        """Maneja checkbox si existe"""
        try:
            if hasattr(self, 'store_config') and self.store_config.get("checkbox"):
                checkbox_selector = self.store_config["checkbox"]
                checkbox = self.page.locator(checkbox_selector).first
                if not checkbox.is_checked():
                    checkbox.check()
        except Exception as e:
            logger.debug(f"Error con checkbox: {e}")
    
    def _submit_form(self) -> Dict[str, Any]:
        """Envía formulario y procesa resultado"""
        try:
            logger.info("🚀 Enviando formulario...")
            
            # Buscar botón de envío
            if hasattr(self, 'store_config') and self.store_config.get("boton_envio"):
                submit_selector = self.store_config["boton_envio"]
            else:
                submit_selector = "._rsi-modal-submit-button"
            
            timeout = self.timeout_manager.get_timeout("element_wait")
            self.page.wait_for_selector(submit_selector, timeout=timeout, state="visible")
            
            element = self.page.locator(submit_selector).first
            element.scroll_into_view_if_needed()
            time.sleep(0.5)
            element.click()
            
            # Esperar resultado
            logger.info("⏳ Esperando confirmación...")
            submit_timeout = self.timeout_manager.get_timeout("form_submit")
            
            try:
                self.page.wait_for_url("**/orders/**", timeout=submit_timeout)
                time.sleep(2)
                
                url_actual = self.page.url
                order_id = self._extract_order_id(url_actual)
                
                return {
                    "success": True,
                    "message": "Pedido completado exitosamente",
                    "order_id": order_id,
                    "confirmation_url": url_actual
                }
                
            except:
                # Buscar confirmación en página actual
                success_indicators = [".order-number", ".thank-you", "text=Gracias"]
                
                for indicator in success_indicators:
                    try:
                        if self.page.locator(indicator).count() > 0:
                            confirmation = self.page.locator(indicator).first.inner_text()
                            return {
                                "success": True,
                                "message": "Pedido confirmado",
                                "order_id": confirmation
                            }
                    except:
                        continue
                
                return {"success": False, "message": "Timeout esperando confirmación"}
                
        except Exception as e:
            return {"success": False, "message": f"Error enviando formulario: {str(e)}"}
    
    def _extract_order_id(self, url: str) -> Optional[str]:
        """Extrae order ID de la URL"""
        try:
            if "/orders/" in url:
                order_id = url.split("/orders/")[1].split("?")[0].split("/")[0]
                if order_id and len(order_id) > 5:
                    return order_id
        except:
            pass
        return None
    
    def _cleanup(self):
        """Limpia recursos del navegador"""
        try:
            if self.context:
                self.context.close()
        except:
            pass
        
        try:
            if self.browser:
                self.browser.close()
        except:
            pass
        
        try:
            if self.playwright:
                self.playwright.stop()
        except:
            pass

# Funciones de interfaz pública (compatibilidad)
def ejecutar_pedido(tienda_id: str, proxy_config: Optional[Dict[str, str]] = None, fast_mode: bool = False) -> Dict[str, Any]:
    """Función principal de interfaz pública (compatible con código existente)"""
    bot = ShopifyBotCore()
    execution_mode = "fast" if fast_mode else "standard"
    
    result = bot.execute_order(
        store_id=tienda_id,
        proxy_config=proxy_config,
        execution_mode=execution_mode,
        debug=False
    )
    
    # Transformar resultado para compatibilidad
    legacy_result = {
        "tienda": result["store_id"],
        "exito": result["success"],
        "mensaje": result["message"],
        "order_id": result.get("order_id"),
        "timestamp": result["timestamp"]
    }
    
    # Agregar nombre del cliente
    if hasattr(bot, 'customer_data') and bot.customer_data:
        legacy_result["nombre"] = f"{bot.customer_data.get('nombre', '')} {bot.customer_data.get('apellido', '')}"
    
    return legacy_result

def cargar_configuracion_tienda(store_id: str) -> dict:
    """Función de compatibilidad para cargar configuración"""
    try:
        config_path = f"tiendas/{store_id}.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if "url_producto" in config and "url" not in config:
            config["url"] = config["url_producto"]
        
        return config
        
    except Exception as e:
        logger.error(f"Error cargando configuración de {store_id}: {e}")
        return {}

if __name__ == "__main__":
    logger.info("Bot Core inicializado correctamente")
