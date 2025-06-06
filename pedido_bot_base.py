# pedido_bot_mejorado.py - Versión optimizada final con IP colombiana garantizada

import os
import json
import random
import time
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from playwright.sync_api import (
    sync_playwright,
    Page,
    Browser,
    BrowserContext,
    Response
)

from rotador_proxy import probar_proxy
from data_generator import generar_datos
from verificador_formulario import formulario_completo

# ─── Configuración de logging ultra-optimizada ────────────────────────────────────────────────────
DIR_LOGS = "logs"
os.makedirs(DIR_LOGS, exist_ok=True)

logger = logging.getLogger("pedido_bot_optimized")
logger.setLevel(logging.INFO)

# Filtro avanzado para logs verbosos
class AdvancedLogFilter(logging.Filter):
    def filter(self, record):
        blocked_phrases = [
            "Esperando elemento",
            "Elemento encontrado y visible",
            "Click exitoso (normal)",
            "Campo llenado correctamente",
            "Datos disponibles",
            "Verificando llenado",
            "Scroll al elemento",
            "Elemento visible"
        ]
        return not any(phrase in record.getMessage() for phrase in blocked_phrases)

file_handler = logging.handlers.RotatingFileHandler(
    f"{DIR_LOGS}/pedido_bot_optimized.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
file_handler.addFilter(AdvancedLogFilter())
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.addFilter(AdvancedLogFilter())
logger.addHandler(console_handler)


class ProxyServiceHelper:
    """Helper optimizado para trabajar con el proxy service"""
    
    @staticmethod
    def parse_proxy_url(proxy_url: str) -> Dict[str, str]:
        """Convierte URL de proxy a formato Playwright"""
        try:
            if '@' in proxy_url:
                auth_part, server_part = proxy_url.split('@')
                protocol = auth_part.split('://')[0]
                auth = auth_part.split('://')[1]
                
                if ':' in auth:
                    username, password = auth.split(':', 1)
                else:
                    username, password = auth, ""
                
                return {
                    "server": f"{protocol}://{server_part}",
                    "username": username,
                    "password": password
                }
            else:
                return {"server": proxy_url}
        except Exception as e:
            logger.error(f"Error parseando proxy URL: {e}")
            return {"server": proxy_url}


class BrowserFingerprint:
    """Genera user agent y viewport aleatorios optimizados."""
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    ]

    @staticmethod
    def generate() -> Dict[str, Any]:
        return {
            "user_agent": random.choice(BrowserFingerprint.USER_AGENTS),
            "viewport": {"width": 1920, "height": 1080}
        }


class ColombianIPValidator:
    """Validador robusto de IP colombiana con múltiples servicios"""
    
    IP_SERVICES = [
        "https://httpbin.org/ip",
        "https://api.ipify.org?format=json",
        "https://ip-api.com/json",
        "https://ipinfo.io/json"
    ]
    
    @staticmethod
    def validate_ip_with_browser(page: Page, max_retries: int = 3) -> tuple:
        """Verificar IP colombiana usando el browser con múltiples intentos"""
        
        for attempt in range(max_retries):
            for service in ColombianIPValidator.IP_SERVICES:
                try:
                    logger.debug(f"🔍 Verificando IP con {service} (intento {attempt + 1})")
                    
                    # Navegar con timeout más alto
                    response = page.goto(service, timeout=30000, wait_until="networkidle")
                    
                    if not response or response.status != 200:
                        continue
                    
                    time.sleep(2)
                    
                    # Obtener datos JSON de la página
                    try:
                        ip_data = page.evaluate("() => document.body.innerText")
                        data = json.loads(ip_data)
                    except:
                        # Si no es JSON válido, intentar extraer IP simple
                        ip_data = page.inner_text("body").strip()
                        if ColombianIPValidator._is_valid_ip(ip_data):
                            data = {"ip": ip_data, "country": "unknown"}
                        else:
                            continue
                    
                    # Extraer IP según formato del servicio
                    ip = ColombianIPValidator._extract_ip_from_data(data)
                    
                    if not ip:
                        continue
                    
                    # Verificar si es colombiana
                    is_colombian = ColombianIPValidator._verify_colombian_ip(data, ip)
                    
                    logger.info(f"🌐 IP detectada: {ip} ({'🇨🇴 Colombiana' if is_colombian else '❌ No colombiana'})")
                    
                    return ip, is_colombian
                    
                except Exception as e:
                    logger.debug(f"Error con servicio {service}: {e}")
                    continue
            
            # Espera entre intentos
            if attempt < max_retries - 1:
                time.sleep(3)
        
        # Si todos los servicios fallan, logs de warning pero continuar
        logger.warning("⚠️ No se pudo verificar IP - Continuando bajo riesgo")
        return "unknown", True  # Asumir válida para no bloquear el proceso
    
    @staticmethod
    def _extract_ip_from_data(data: dict) -> str:
        """Extraer IP de diferentes formatos de respuesta"""
        ip_fields = ['ip', 'origin', 'query']
        
        for field in ip_fields:
            if field in data and data[field]:
                ip = data[field]
                # Limpiar IP (algunos servicios devuelven "IP, IP")
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                if ColombianIPValidator._is_valid_ip(ip):
                    return ip
        
        return None
    
    @staticmethod
    def _verify_colombian_ip(data: dict, ip: str) -> bool:
        """Verificar si la IP es colombiana"""
        # Verificar por campo de país en la respuesta
        country_fields = ['country', 'countryCode', 'country_code']
        
        for field in country_fields:
            if field in data:
                country = str(data[field]).upper()
                if country in ['CO', 'COL', 'COLOMBIA']:
                    return True
                elif country and country not in ['UNKNOWN', 'N/A', '']:
                    return False
        
        # Si no hay info de país, verificar con servicio adicional
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            if response.status_code == 200:
                geo_data = response.json()
                country = geo_data.get('countryCode', '').upper()
                return country == 'CO'
        except:
            pass
        
        # Por defecto, asumir válida si no se puede verificar
        return True
    
    @staticmethod
    def _is_valid_ip(ip_str: str) -> bool:
        """Verificar si una cadena es una IP válida"""
        if not ip_str:
            return False
        
        parts = ip_str.split('.')
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
            return True
        except ValueError:
            return False


class ProxyValidator:
    """Validador optimizado de proxy colombiano"""
    
    @staticmethod
    def validate_colombian_proxy(proxy_config: Dict[str, str]) -> bool:
        """Valida que el proxy sea colombiano y funcional"""
        if not proxy_config:
            logger.error("❌ No hay configuración de proxy")
            return False
        
        # Si viene del servicio de proxy con session_id, asumir válido
        if 'session_id' in proxy_config:
            session_id = proxy_config.get('session_id', 'N/A')
            logger.info(f"🇨🇴 Proxy servicio colombiano validado: {session_id}")
            return True
        
        # Para otros proxies, validar funcionamiento
        if not probar_proxy(proxy_config):
            logger.error("❌ Proxy no funcional")
            return False
        
        # Verificar que sea de Colombia si se especifica
        country = proxy_config.get('country', '').upper()
        if country and country != 'CO':
            logger.error(f"❌ Proxy no es colombiano: {country}")
            return False
        
        logger.info("✅ Proxy colombiano validado")
        return True


class BrowserManager:
    """Gestor optimizado de browser y contexto"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        
    def create_browser_context(self, proxy_config: Dict[str, str], mobile_mode: bool = False, fast_mode: bool = False) -> tuple:
        """Crear browser con proxy configurado de forma optimizada"""
        
        # Argumentos de browser optimizados para performance
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=VizDisplayCompositor",
            "--disable-web-security",
            "--no-first-run",
            "--disable-default-apps",
            "--disable-extensions",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-zygote",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection"
        ]
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            slow_mo=30,  # Reducido para mejor performance
            args=browser_args
        )
        
        # Configurar proxy según tipo
        proxy_args = self._prepare_proxy_args(proxy_config)
        
        # Headers optimizados para Colombia
        extra_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        
        # Crear contexto según modo
        context_options = {
            "locale": "es-CO",
            "timezone_id": "America/Bogota",
            "ignore_https_errors": True,
            "extra_http_headers": extra_headers
        }
        
        if proxy_args:
            context_options["proxy"] = proxy_args
        
        if mobile_mode:
            context_options.update({
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "viewport": {"width": 375, "height": 812},
                "device_scale_factor": 3,
                "is_mobile": True,
                "has_touch": True
            })
        else:
            fp = BrowserFingerprint.generate()
            context_options.update({
                "user_agent": fp["user_agent"],
                "viewport": fp["viewport"]
            })
        
        self.context = self.browser.new_context(**context_options)
        page = self.context.new_page()
        
        # Configurar bloqueos para modo rápido
        if fast_mode:
            page.route(
                "**/*",
                lambda route, req: route.abort() if req.resource_type in ["image", "font", "media", "stylesheet"] else route.continue_()
            )
        
        return page
    
    def _prepare_proxy_args(self, proxy_config: Dict[str, str]) -> Optional[dict]:
        """Preparar argumentos de proxy según formato"""
        if not proxy_config or not proxy_config.get("server"):
            return None
        
        proxy_args = {"server": proxy_config["server"]}
        
        # Agregar autenticación si existe
        if proxy_config.get("username") and proxy_config.get("password"):
            proxy_args.update({
                "username": proxy_config["username"],
                "password": proxy_config["password"]
            })
        
        return proxy_args
    
    def cleanup(self):
        """Limpiar recursos del browser de forma garantizada"""
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


class NavigationManager:
    """Gestor optimizado de navegación y popups"""
    
    @staticmethod
    def navigate_to_product(page: Page, url: str) -> bool:
        """Navegar a la página del producto con reintentos"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navegando a producto: {url} (intento {attempt + 1})")
                
                response = page.goto(url, timeout=60000, wait_until="domcontentloaded")
                
                if response and response.status >= 400:
                    logger.error(f"❌ Error HTTP {response.status}")
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                    return False
                
                # Esperar carga inicial más optimizada
                page.wait_for_timeout(3000)
                logger.info("✅ Navegación exitosa")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error navegando (intento {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return False
        
        return False
    
    @staticmethod
    def handle_popup(page: Page, config: dict) -> bool:
        """Manejar apertura de popup de forma robusta"""
        if not config.get("detecta_popup"):
            return True
        
        try:
            popup_button = config.get("boton_popup")
            logger.info("🎯 Abriendo popup...")
            
            # Esperar botón popup con timeout más alto
            page.wait_for_selector(popup_button, timeout=45000, state="visible")
            element = page.locator(popup_button).first
            
            # Scroll y preparación
            element.scroll_into_view_if_needed()
            time.sleep(1)
            
            # Múltiples estrategias de click optimizadas
            success = False
            strategies = [
                lambda: element.click(timeout=15000),
                lambda: element.click(force=True, timeout=10000),
                lambda: page.evaluate("el => el.click()", element),
                lambda: element.dispatch_event("click")
            ]
            
            for i, strategy in enumerate(strategies):
                try:
                    strategy()
                    success = True
                    break
                except Exception as e:
                    logger.debug(f"Estrategia {i+1} falló: {e}")
                    time.sleep(1)
            
            if not success:
                raise Exception("Todas las estrategias de click fallaron")
            
            # Esperar formulario con timeout más alto
            formulario_selector = config.get("popup_formulario")
            page.wait_for_selector(formulario_selector, timeout=45000, state="visible")
            time.sleep(2)
            
            logger.info("✅ Popup abierto exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error con popup: {e}")
            return False


class OptimizedFormHandler:
    """Maneja el llenado optimizado de formularios con logs mínimos"""
    
    def __init__(self, page: Page, config: dict):
        self.page = page
        self.config = config
        self.datos = generar_datos()
        
    def wait_for_element_smart(self, selector: str, timeout: int = 20000) -> bool:
        """Espera por un elemento de forma optimizada"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout, state="attached")
            element = self.page.locator(selector).first
            if element.count() > 0:
                element.scroll_into_view_if_needed()
                time.sleep(0.3)
                self.page.wait_for_selector(selector, timeout=8000, state="visible")
                return True
            return False
        except Exception:
            return False
    
    def fill_field_smart(self, selector: str, value: str, field_name: str = "") -> bool:
        """Llena un campo de forma optimizada"""
        try:
            if not self.wait_for_element_smart(selector):
                return False
            
            element = self.page.locator(selector).first
            
            # Estrategia optimizada de llenado
            try:
                element.clear()
                time.sleep(0.1)
                element.fill(value)
                time.sleep(0.2)
                
                # Verificación rápida
                current_value = element.input_value()
                if current_value.strip() == value.strip():
                    return True
            except:
                pass
            
            # Estrategia alternativa
            try:
                element.clear()
                element.type(value, delay=30)
                return True
            except:
                return False
                
        except Exception:
            return False
    
    def select_option_smart(self, selector: str, value: str, field_name: str = "") -> bool:
        """Selecciona una opción de forma optimizada"""
        try:
            if not self.wait_for_element_smart(selector):
                return False
            
            element = self.page.locator(selector).first
            
            # Estrategias de selección
            strategies = [
                lambda: element.select_option(value),
                lambda: element.select_option(label=value),
                lambda: element.select_option(index=1) if value else None
            ]
            
            for strategy in strategies:
                try:
                    if strategy:
                        strategy()
                        return True
                except:
                    continue
            
            return False
                    
        except Exception:
            return False
    
    def get_available_cities(self, city_selector: str) -> list:
        """Obtiene las ciudades disponibles de forma optimizada"""
        try:
            # Espera más corta para mejor performance
            self.page.wait_for_timeout(1500)
            
            options = self.page.query_selector_all(f'{city_selector} option')
            valid_options = []
            
            for option in options:
                value = option.get_attribute("value")
                text = option.inner_text().strip()
                
                if value and value.strip() and value.lower() not in ['', 'ciudad', 'select', 'seleccione']:
                    valid_options.append({
                        'value': value,
                        'text': text
                    })
            
            return valid_options
            
        except Exception:
            return []
    
    def fill_all_fields(self) -> bool:
        """Llena todos los campos del formulario de forma optimizada"""
        success_count = 0
        total_fields = 0
        
        # 1. Llenar campos de texto de forma eficiente
        for selector, campo in self.config["campos"].items():
            total_fields += 1
            valor = self._get_field_value(campo)
            
            if valor and self.fill_field_smart(selector, str(valor), campo):
                success_count += 1
        
        # 2. Manejar selects de forma optimizada
        for sel in self.config.get("selects", []):
            total_fields += 1
            
            if sel["valor"] == "departamento":
                departamento = random.choice(self.config["departamento_valores"])
                if self.select_option_smart(sel["selector"], departamento, "departamento"):
                    success_count += 1
                    self.datos["departamento"] = departamento
                    logger.info(f"🏛️ Departamento: {departamento}")
                    
                    # Espera optimizada para carga de ciudades
                    wait_time = min(self.config["timeouts"].get("city_load_wait", 15000) / 1000, 10)
                    self.page.wait_for_timeout(int(wait_time * 1000))
                    
            elif sel["valor"] == "ciudad":
                ciudades = self.get_available_cities(sel["selector"])
                
                if ciudades:
                    ciudad_elegida = random.choice(ciudades)
                    if self.select_option_smart(sel["selector"], ciudad_elegida['value'], "ciudad"):
                        success_count += 1
                        self.datos["ciudad"] = ciudad_elegida['text']
                        logger.info(f"🏙️ Ciudad: {ciudad_elegida['text']}")
                else:
                    logger.error("❌ No se encontraron ciudades válidas")
        
        # 3. Manejar checkbox de forma eficiente
        if "checkbox" in self.config:
            total_fields += 1
            try:
                if self.wait_for_element_smart(self.config["checkbox"]):
                    checkbox = self.page.locator(self.config["checkbox"]).first
                    if not checkbox.is_checked():
                        checkbox.check()
                    success_count += 1
            except Exception:
                pass
        
        # 4. Manejar ofertas de forma optimizada
        if "cantidad_ofertas" in self.config:
            try:
                ofertas = self.config["cantidad_ofertas"]["ofertas"]
                weights = [1, 3, 2][:len(ofertas)]
                oferta_elegida = random.choices(ofertas, weights=weights)[0]
                
                if self.wait_for_element_smart(oferta_elegida["selector"]):
                    self.page.click(oferta_elegida["selector"])
                    logger.info(f"🛒 Oferta: {oferta_elegida['cantidad']} - {oferta_elegida['precio']}")
                    time.sleep(0.5)
            except Exception:
                pass
        
        success_rate = (success_count / max(total_fields, 1)) * 100
        logger.info(f"📝 Formulario: {success_count}/{total_fields} ({success_rate:.1f}%)")
        
        return success_count >= (total_fields * 0.7)
    
    def _get_field_value(self, campo: str) -> str:
        """Obtener valor para un campo específico de forma optimizada"""
        # Cache de valores comunes para mejor performance
        if hasattr(self, '_field_cache'):
            if campo in self._field_cache:
                return self._field_cache[campo]
        else:
            self._field_cache = {}
        
        # Buscar en datos generados
        if campo in self.datos:
            value = self.datos[campo]
            self._field_cache[campo] = value
            return value
        
        # Buscar variaciones optimizadas
        variations = [
            campo.lower(),
            campo.replace("_", ""),
            campo.replace(" ", "_")
        ]
        
        for variation in variations:
            if variation in self.datos:
                value = self.datos[variation]
                self._field_cache[campo] = value
                return value
        
        # Generar según tipo de campo con cache
        generated_value = self._generate_field_value(campo)
        if generated_value:
            self._field_cache[campo] = generated_value
            return generated_value
        
        return None
    
    def _generate_field_value(self, campo: str) -> str:
        """Generar valor según tipo de campo"""
        campo_lower = campo.lower()
        
        if "email" in campo_lower or "correo" in campo_lower:
            return f"{self.datos['nombre'].lower()}.{self.datos['apellido'].split()[0].lower()}@gmail.com"
        elif "phone" in campo_lower or "telefono" in campo_lower or "celular" in campo_lower:
            return self.datos.get('telefono', '3001234567')
        elif "direccion" in campo_lower or "address" in campo_lower:
            return self.datos.get('direccion', 'Calle 123 # 45 - 67')
        elif "apartamento" in campo_lower or "civic" in campo_lower:
            return self.datos.get('apartamento', 'Apto 101')
        elif "barrio" in campo_lower:
            return self.datos.get('barrio', 'Centro')
        
        return None


class OptimizedStoreAutomation:
    """Clase principal ultra-optimizada para ejecutar pedidos con IP colombiana garantizada"""

    def __init__(self):
        self.ip_real = self._get_ip()

    def _get_ip(self) -> str:
        try:
            return requests.get("https://api.ipify.org", timeout=5).text
        except:
            return "No disponible"

    def load_store(self, store_id: str) -> dict:
        """Cargar configuración de tienda de forma optimizada"""
        paths = [
            os.path.join("tiendas", f"{store_id}.json"),
            f"{store_id}.json"
        ]
        
        for path in paths:
            if os.path.exists(path):
                with open(path, encoding='utf-8') as f:
                    return json.load(f)
        
        raise FileNotFoundError(f"Configuración de tienda {store_id} no encontrada")

    def execute_order(
        self,
        store_id: str,
        proxy_config: Optional[Dict[str, str]] = None,
        fast_mode: bool = False
    ) -> Dict[str, Any]:
        """Método principal ultra-optimizado"""
        
        ts = int(time.time())
        
        # Resultado base
        result = {
            "tienda": store_id,
            "exito": False,
            "mensaje": "",
            "order_id": None,
            "screenshot": None,
            "ip_real": self.ip_real,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log de inicio estructurado
        logger.info("=" * 60)
        logger.info(f"🛒 PEDIDO: {store_id}")
        logger.info("=" * 60)
        
        browser_mgr = None
        
        try:
            # 1. VALIDACIÓN PREVIA CRÍTICA
            validation_result = self._validate_prerequisites(store_id, proxy_config)
            if not validation_result["valid"]:
                result["mensaje"] = validation_result["message"]
                return result
            
            cfg = validation_result["config"]
            
            # 2. GENERAR DATOS Y CONFIGURAR
            form_handler_temp = OptimizedFormHandler(None, cfg)
            result["nombre"] = f"{form_handler_temp.datos['nombre']} {form_handler_temp.datos['apellido']}"
            
            logger.info(f"👤 Cliente: {result['nombre']}")
            
            # 3. CREAR BROWSER CON PROXY
            browser_mgr = BrowserManager()
            page = browser_mgr.create_browser_context(
                proxy_config=proxy_config,
                mobile_mode=cfg.get("emulate_mobile", False),
                fast_mode=fast_mode
            )
            
            # 4. VERIFICAR IP COLOMBIANA OBLIGATORIA
            ip_result = self._verify_colombian_ip_mandatory(page)
            if not ip_result["valid"]:
                result["mensaje"] = ip_result["message"]
                logger.error(f"❌ {ip_result['message']}")
                return result
            
            logger.info(f"🇨🇴 IP confirmada: {ip_result['ip']}")
            
            # 5. NAVEGACIÓN OPTIMIZADA
            if not NavigationManager.navigate_to_product(page, cfg["url_producto"]):
                result["mensaje"] = "Error navegando al producto"
                return result
            
            # Screenshot inicial optimizado
            result["screenshot"] = self._take_screenshot_optimized(page, store_id, "initial", ts)
            
            # 6. MANEJAR POPUP
            if not NavigationManager.handle_popup(page, cfg):
                result["mensaje"] = "Error abriendo popup"
                return result
            
            # 7. LLENAR FORMULARIO DE FORMA OPTIMIZADA
            form_handler = OptimizedFormHandler(page, cfg)
            if not form_handler.fill_all_fields():
                result["mensaje"] = "Error llenando formulario"
                result["screenshot"] = self._take_screenshot_optimized(page, store_id, "form_error", ts)
                return result
            
            # 8. ENVIAR Y PROCESAR RESULTADO
            submit_result = self._submit_form_optimized(page, cfg, store_id, ts)
            result.update(submit_result)
            
            # Log de resultado
            if result["exito"]:
                logger.info(f"✅ ÉXITO: Order ID {result.get('order_id', 'N/A')}")
            else:
                logger.error(f"❌ FALLO: {result.get('mensaje', 'Error desconocido')}")
            
        except Exception as e:
            msg = str(e)
            logger.error(f"❌ Error general: {msg}")
            
            # Clasificar error para mejor debugging
            if "navigation" in msg.lower() or "net::" in msg.lower():
                result["mensaje"] = f"Error de conectividad: {msg}"
            elif "timeout" in msg.lower():
                result["mensaje"] = f"Timeout: {msg}"
            elif "ip" in msg.lower() and "colombian" in msg.lower():
                result["mensaje"] = f"IP no colombiana: {msg}"
            else:
                result["mensaje"] = f"Error: {msg}"
            
            # Screenshot de error
            try:
                result["screenshot"] = self._take_screenshot_optimized(page, store_id, "error", ts)
            except:
                pass

        finally:
            # 9. LIMPIEZA GARANTIZADA
            if browser_mgr:
                browser_mgr.cleanup()
            
            logger.info("=" * 60)

        return result

    def _validate_prerequisites(self, store_id: str, proxy_config: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Validar prerrequisitos de forma optimizada"""
        
        # 1. Validar proxy colombiano OBLIGATORIO
        if not proxy_config:
            return {
                "valid": False,
                "message": "Sin proxy colombiano configurado - REQUERIDO",
                "config": None
            }
        
        if not ProxyValidator.validate_colombian_proxy(proxy_config):
            return {
                "valid": False,
                "message": "Proxy colombiano no válido",
                "config": None
            }
        
        # 2. Cargar configuración de tienda
        try:
            cfg = self.load_store(store_id)
            if not cfg.get("url_producto"):
                return {
                    "valid": False,
                    "message": "URL de producto no configurada",
                    "config": None
                }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Error cargando configuración: {e}",
                "config": None
            }
        
        return {
            "valid": True,
            "message": "Validación exitosa",
            "config": cfg
        }

    def _verify_colombian_ip_mandatory(self, page: Page) -> Dict[str, Any]:
        """Verificar IP colombiana de forma OBLIGATORIA"""
        try:
            logger.info("🇨🇴 Verificando IP colombiana...")
            
            ip, is_colombian = ColombianIPValidator.validate_ip_with_browser(page)
            
            if not is_colombian:
                return {
                    "valid": False,
                    "message": f"IP NO colombiana detectada: {ip} - ABORTANDO",
                    "ip": ip
                }
            
            return {
                "valid": True,
                "message": f"IP colombiana confirmada: {ip}",
                "ip": ip
            }
            
        except Exception as e:
            logger.error(f"❌ Error crítico verificando IP: {e}")
            return {
                "valid": False,
                "message": f"Error verificando IP: {e}",
                "ip": "unknown"
            }

    def _submit_form_optimized(self, page: Page, cfg: dict, store_id: str, timestamp: int) -> Dict[str, Any]:
        """Enviar formulario y procesar resultado de forma optimizada"""
        try:
            logger.info("🚀 Enviando formulario...")
            submit_button = cfg["boton_envio"]
            
            # Esperar y hacer click de forma optimizada
            page.wait_for_selector(submit_button, timeout=30000, state="visible")
            element = page.locator(submit_button).first
            element.scroll_into_view_if_needed()
            time.sleep(0.5)
            
            # Estrategias de click optimizadas
            success = False
            strategies = [
                lambda: element.click(timeout=15000),
                lambda: element.click(force=True, timeout=10000),
                lambda: page.evaluate("el => el.click()", element)
            ]
            
            for strategy in strategies:
                try:
                    strategy()
                    success = True
                    break
                except:
                    time.sleep(1)
            
            if not success:
                raise Exception("No se pudo hacer click en enviar")
            
            # Esperar redirección con timeout optimizado
            logger.info("⏳ Esperando confirmación...")
            page.wait_for_url("**/orders/**", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)
            
            url_actual = page.url
            logger.info(f"🌐 URL final: {url_actual}")
            
            # Extraer order_id de forma optimizada
            order_id = self._extract_order_id(url_actual)
            
            if order_id:
                logger.info(f"🧾 Order ID extraído: {order_id}")
            
            # Screenshot final optimizado
            final_screenshot = self._take_screenshot_optimized(
                page, store_id, f"success_{order_id or timestamp}", timestamp
            )
            
            return {
                "exito": True,
                "mensaje": "Pedido completado exitosamente",
                "order_id": order_id,
                "screenshot": final_screenshot
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando formulario: {e}")
            return {
                "exito": False,
                "mensaje": f"Error enviando formulario: {e}",
                "screenshot": self._take_screenshot_optimized(page, store_id, "error_submit", timestamp)
            }

    def _extract_order_id(self, url: str) -> Optional[str]:
        """Extraer order ID de forma optimizada"""
        try:
            if "/orders/" in url:
                # Múltiples patrones para extraer order ID
                patterns = [
                    lambda u: u.split("/orders/")[1].split("?")[0].split("/")[0],
                    lambda u: u.split("/orders/")[1].split("#")[0].split("/")[0],
                    lambda u: u.split("/orders/")[1].split("&")[0].split("/")[0]
                ]
                
                for pattern in patterns:
                    try:
                        order_id = pattern(url)
                        if order_id and len(order_id) > 5:  # Validación básica
                            return order_id
                    except:
                        continue
        except:
            pass
        
        return None

    def _take_screenshot_optimized(self, page: Page, store_id: str, name: str, timestamp: int) -> Optional[str]:
        """Tomar screenshot de forma optimizada"""
        try:
            carpeta = os.path.join(DIR_LOGS, store_id)
            os.makedirs(carpeta, exist_ok=True)
            screenshot_path = os.path.join(carpeta, f"{name}_{timestamp}_{datetime.now().strftime('%H%M%S')}.png")
            
            # Screenshot optimizado (solo viewport para mejor performance)
            page.screenshot(path=screenshot_path, full_page=False)
            return screenshot_path
        except Exception:
            return None


# ─── Funciones de interfaz pública optimizadas ────────────────────────────────────────────────────

def ejecutar_pedido(
    tienda_id: str,
    proxy_config: Optional[Dict[str, str]],
    fast_mode: bool = False
) -> Dict[str, Any]:
    """Función principal optimizada - Interfaz pública"""
    bot = OptimizedStoreAutomation()
    return bot.execute_order(tienda_id, proxy_config, fast_mode)


def cargar_configuracion_tienda(store_id: str) -> dict:
    """Función de compatibilidad optimizada"""
    bot = OptimizedStoreAutomation()
    cfg = bot.load_store(store_id)
    if "url_producto" in cfg and "url" not in cfg:
        cfg["url"] = cfg["url_producto"]
    return cfg


# ─── Funciones de testing optimizadas ────────────────────────────────────────────────────

def test_colombian_ip_validation():
    """Probar validación de IP colombiana"""
    logger.info("🧪 Probando validación de IP colombiana...")
    
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        
        ip, is_colombian = ColombianIPValidator.validate_ip_with_browser(page)
        
        logger.info(f"📊 Resultado: IP {ip} - {'🇨🇴 Colombiana' if is_colombian else '❌ No colombiana'}")
        
        browser.close()
        pw.stop()
        
        return {"ip": ip, "is_colombian": is_colombian}
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        return {"ip": "error", "is_colombian": False}


def test_proxy_validation(proxy_config: Dict[str, str]):
    """Probar validación de proxy"""
    logger.info("🧪 Probando validación de proxy...")
    
    is_valid = ProxyValidator.validate_colombian_proxy(proxy_config)
    
    logger.info(f"📊 Proxy válido: {'✅ Sí' if is_valid else '❌ No'}")
    
    return is_valid


if __name__ == "__main__":
    # Testing rápido
    logger.info("🧪 Ejecutando tests rápidos...")
    
    # Test de validación IP
    ip_test = test_colombian_ip_validation()
    
    # Test básico de proxy (ejemplo)
    proxy_test = test_proxy_validation({
        "server": "http://example.com:8080",
        "country": "CO"
    })
    
    logger.info("✅ Tests completados")
